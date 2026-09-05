from typing import List, Dict, Any
import rasterio
import numpy as np
import os
from app.domain.models import ToolDefinition, AssetModality, ToolRequest, ToolResult, ImageAsset, ToolErrorCode
from app.agent.interfaces import BaseTool
from app.analytics.deterministic import DeterministicAnalyticsEngine

class NdviTool(BaseTool):
    def __init__(self):
        definition = ToolDefinition(
            tool_id="ndvi_calculator",
            name="NDVI Calculator",
            description="Deterministically calculates Normalized Difference Vegetation Index (NDVI).",
            task_capabilities=["spectral_index", "vegetation_analysis"],
            accepted_modalities=[AssetModality.MULTISPECTRAL],
            required_capabilities=["can_ndvi"],
            output_schema={"type": "object", "properties": {"mean_ndvi": {"type": "number"}}},
            version="1.0.0"
        )
        super().__init__(definition)
        self.engine = DeterministicAnalyticsEngine()
        
    def execute(self, request: ToolRequest, assets: List[ImageAsset]) -> ToolResult:
        if not assets:
            return ToolResult(request_id=request.request_id, tool_id=self.definition.tool_id, tool_version=self.definition.version,
                              success=False, execution_duration_sec=0, error_code=ToolErrorCode.INPUT_INVALID, error_message="No assets provided")
        
        asset = assets[0]
        
        try:
            # Find RED and NIR bands
            red_idx = next(k for k, v in asset.band_semantics.items() if v == "RED")
            nir_idx = next(k for k, v in asset.band_semantics.items() if v == "NIR")
            
            with rasterio.open(asset.storage_location) as src:
                red_band = src.read(red_idx)
                nir_band = src.read(nir_idx)
                nodata = src.nodata
                
            ndvi_mask = self.engine.calculate_ndvi(nir_band, red_band, nodata=nodata)
            
            mean_ndvi = float(ndvi_mask.mean())
            
            return ToolResult(
                request_id=request.request_id,
                tool_id=self.definition.tool_id,
                tool_version=self.definition.version,
                success=True,
                execution_duration_sec=0.0, # Will be set by execution service
                outputs={},
                metrics={"mean_ndvi": mean_ndvi},
                provenance=["deterministic_calculation: (NIR-RED)/(NIR+RED)"],
                confidence={"DETERMINISTIC": 1.0}
            )
            
        except Exception as e:
            return ToolResult(
                request_id=request.request_id,
                tool_id=self.definition.tool_id,
                tool_version=self.definition.version,
                success=False,
                execution_duration_sec=0.0,
                error_code=ToolErrorCode.EXECUTION_FAILED,
                error_message=str(e)
            )

class AreaTool(BaseTool):
    def __init__(self):
        definition = ToolDefinition(
            tool_id="area_calculator",
            name="Physical Area Calculator",
            description="Calculates physical area in projected units.",
            task_capabilities=["area_measurement", "spatial_statistics"],
            accepted_modalities=[AssetModality.MULTISPECTRAL, AssetModality.GRAYSCALE, AssetModality.SAR, AssetModality.RGB],
            required_capabilities=["can_area_measurement"],
            output_schema={"type": "object", "properties": {"total_area": {"type": "number"}}},
            version="1.0.0"
        )
        super().__init__(definition)
        self.engine = DeterministicAnalyticsEngine()
        
    def execute(self, request: ToolRequest, assets: List[ImageAsset]) -> ToolResult:
        if not assets:
            return ToolResult(request_id=request.request_id, tool_id=self.definition.tool_id, tool_version=self.definition.version,
                              success=False, execution_duration_sec=0, error_code=ToolErrorCode.INPUT_INVALID, error_message="No assets provided")
        
        asset = assets[0]
        # In a real scenario, this would take a generated mask artifact as input rather than an entire image,
        # but for demonstration we calculate the area of valid (non-nodata) pixels in band 1.
        
        try:
            with rasterio.open(asset.storage_location) as src:
                band1 = src.read(1)
                if src.nodata is not None:
                    mask = (band1 != src.nodata)
                else:
                    mask = (band1 > 0) # naive fallback
                    
            res = self.engine.calculate_mask_area(
                mask, 
                pixel_resolution=asset.pixel_resolution or (1.0, 1.0), 
                is_projected=asset.capabilities.get("can_area_measurement", False)
            )
            
            if not res["valid"]:
                return ToolResult(
                    request_id=request.request_id, tool_id=self.definition.tool_id, tool_version=self.definition.version,
                    success=False, execution_duration_sec=0, error_code=ToolErrorCode.CAPABILITY_UNSUPPORTED, error_message=res["error"]
                )
                
            return ToolResult(
                request_id=request.request_id,
                tool_id=self.definition.tool_id,
                tool_version=self.definition.version,
                success=True,
                execution_duration_sec=0.0,
                metrics={"total_area": res["total_area"], "pixel_count": float(res["pixel_count"])},
                provenance=["deterministic_calculation: pixel_count * pixel_area"],
                confidence={"DETERMINISTIC": 1.0}
            )
        except Exception as e:
            return ToolResult(
                request_id=request.request_id, tool_id=self.definition.tool_id, tool_version=self.definition.version,
                success=False, execution_duration_sec=0, error_code=ToolErrorCode.EXECUTION_FAILED, error_message=str(e)
            )

class Qwen2VLTool(BaseTool):
    def __init__(self, adapter):
        definition = ToolDefinition(
            tool_id="visual_language_specialist",
            name="Visual Language Specialist (Qwen2-VL)",
            description="Remote-sensing visual understanding, VQA, and captioning. Uses Qwen2-VL-2B with optional RS LoRA adapter.",
            task_capabilities=["vqa", "captioning", "image_understanding", "rs_interpretation"],
            accepted_modalities=[AssetModality.RGB, AssetModality.MULTISPECTRAL],
            required_capabilities=[],
            output_schema={"type": "object", "properties": {"answer": {"type": "string"}}},
            version="1.1.0"
        )
        super().__init__(definition)
        self.adapter = adapter

    def execute(self, request: ToolRequest, assets: List[ImageAsset]) -> ToolResult:
        if not assets:
            return ToolResult(request_id=request.request_id, tool_id=self.definition.tool_id, tool_version=self.definition.version,
                              success=False, execution_duration_sec=0, error_code=ToolErrorCode.INPUT_INVALID, error_message="No assets provided")

        has_groq = os.environ.get("GROQ_API_KEY") or (os.path.exists(".env") and "GROQ_API_KEY" in open(".env").read())

        if not has_groq and not self.adapter.model:
            try:
                self.adapter.load()
            except Exception as e:
                return ToolResult(
                    request_id=request.request_id, tool_id=self.definition.tool_id, tool_version=self.definition.version,
                    success=False, execution_duration_sec=0, error_code=ToolErrorCode.EXECUTION_FAILED, error_message=f"Model load failed: {str(e)}"
                )
                
        # Prepare inputs
        try:
            import rasterio
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np
            
            def load_asset_as_pil(asset: ImageAsset) -> Image.Image:
                with rasterio.open(asset.storage_location) as src:
                    bands = []
                    # Try to use semantics first
                    for color in ["RED", "GREEN", "BLUE"]:
                        idx = None
                        for k, v in asset.band_semantics.items():
                            if v == color:
                                idx = k
                                break
                        if idx is not None:
                            bands.append(src.read(idx))
                            
                    # If semantics failed but we have 3+ bands, assume 1=R, 2=G, 3=B
                    if len(bands) < 3 and src.count >= 3:
                        bands = [src.read(1), src.read(2), src.read(3)]
                        
                    if len(bands) == 3:
                        r, g, b = bands
                        r_norm = np.clip((r - r.min()) / (r.max() - r.min() + 1e-5) * 255, 0, 255).astype(np.uint8)
                        g_norm = np.clip((g - g.min()) / (g.max() - g.min() + 1e-5) * 255, 0, 255).astype(np.uint8)
                        b_norm = np.clip((b - b.min()) / (b.max() - b.min() + 1e-5) * 255, 0, 255).astype(np.uint8)
                        rgb_arr = np.stack((r_norm, g_norm, b_norm), axis=-1)
                        return Image.fromarray(rgb_arr)
                    else:
                        b1 = src.read(1)
                        b1_norm = np.clip((b1 - b1.min()) / (b1.max() - b1.min() + 1e-5) * 255, 0, 255).astype(np.uint8)
                        return Image.fromarray(b1_norm).convert("RGB")

            images = [load_asset_as_pil(a) for a in assets]
            
            if len(images) == 1:
                final_img = images[0]
            else:
                # Stitch images horizontally for Change Detection / Multi-modal
                target_height = min(img.height for img in images)
                resized_images = [img.resize((int(img.width * target_height / img.height), target_height)) for img in images]
                total_width = sum(img.width for img in resized_images)
                
                final_img = Image.new('RGB', (total_width, target_height))
                x_offset = 0
                for img in resized_images:
                    final_img.paste(img, (x_offset, 0))
                    x_offset += img.width

            # Pass to adapter
            query = request.parameters.get("query", "Describe this remote-sensing image in detail.")
            if len(images) > 1:
                query = "The attached image contains two satellite observations of the same location stitched side-by-side (Time 1 on the left, Time 2 on the right). " + query

            predictions = self.adapter.predict({"image": final_img, "query": query})

            inference_mode = predictions.get("inference_mode", "Qwen2-VL-2B base")
            prov = predictions.get("provenance", ["Qwen2VLAdapter"])

            return ToolResult(
                request_id=request.request_id,
                tool_id=self.definition.tool_id,
                tool_version=self.definition.version,
                success=True,
                execution_duration_sec=0.0,
                outputs={
                    "answer": predictions["answer"],
                    "model": inference_mode,
                    "adapter_loaded": predictions.get("adapter_loaded", False)
                },
                metrics={},
                provenance=prov,
                confidence={"MODEL_CONFIDENCE": -1.0}
            )

        except Exception as e:
            return ToolResult(
                request_id=request.request_id, tool_id=self.definition.tool_id, tool_version=self.definition.version,
                success=False, execution_duration_sec=0, error_code=ToolErrorCode.EXECUTION_FAILED, error_message=f"Inference failed: {str(e)}"
            )
