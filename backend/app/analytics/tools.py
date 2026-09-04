from typing import List, Dict, Any
import rasterio
import numpy as np
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

        asset = assets[0]

        if not self.adapter.model:
            try:
                self.adapter.load()
            except Exception as e:
                return ToolResult(
                    request_id=request.request_id, tool_id=self.definition.tool_id, tool_version=self.definition.version,
                    success=False, execution_duration_sec=0, error_code=ToolErrorCode.EXECUTION_FAILED, error_message=f"Model load failed: {str(e)}"
                )
                
        # Prepare inputs
        try:
            # Safely create an RGB PIL image from the asset
            import rasterio
            from PIL import Image
            import numpy as np
            
            # Simple heuristic for RGB extraction
            with rasterio.open(asset.storage_location) as src:
                # Assuming bands 1,2,3 are RGB if no semantics, or extracting specific semantics
                bands = []
                for color in ["RED", "GREEN", "BLUE"]:
                    # Find band index
                    idx = None
                    for k, v in asset.band_semantics.items():
                        if v == color:
                            idx = k
                            break
                    if idx is not None:
                        bands.append(src.read(idx))
                        
                if len(bands) == 3:
                    # Construct RGB
                    r, g, b = bands
                    # Simple normalization to 0-255
                    r_norm = np.clip((r - r.min()) / (r.max() - r.min() + 1e-5) * 255, 0, 255).astype(np.uint8)
                    g_norm = np.clip((g - g.min()) / (g.max() - g.min() + 1e-5) * 255, 0, 255).astype(np.uint8)
                    b_norm = np.clip((b - b.min()) / (b.max() - b.min() + 1e-5) * 255, 0, 255).astype(np.uint8)
                    rgb_arr = np.stack((r_norm, g_norm, b_norm), axis=-1)
                    img = Image.fromarray(rgb_arr)
                else:
                    # Fallback to just reading first band as Grayscale
                    b1 = src.read(1)
                    b1_norm = np.clip((b1 - b1.min()) / (b1.max() - b1.min() + 1e-5) * 255, 0, 255).astype(np.uint8)
                    img = Image.fromarray(b1_norm).convert("RGB")
                    
            # Pass to adapter
            query = request.parameters.get("query", "Describe this remote-sensing image in detail.")
            predictions = self.adapter.predict({"image": img, "query": query})

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
