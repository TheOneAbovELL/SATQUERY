from typing import List, Dict, Any
import time

from app.agent.interfaces import BaseTool
from app.domain.models import ToolDefinition, ToolRequest, ToolResult, ToolErrorCode, ImageAsset, AssetModality
from app.analytics.change_analysis import BiTemporalChangeAnalyzer


class BiTemporalChangeTool(BaseTool):
    """
    Agent tool wrapper for the BiTemporalChangeAnalyzer pipeline.
    Exposes deterministic bi-temporal change detection to the SatQuery agent.
    """
    def __init__(self, artifact_dir: str = "./artifacts"):
        definition = ToolDefinition(
            tool_id="bi_temporal_change_analysis",
            name="Bi-Temporal Change Analysis",
            description="Detects and quantifies changes between two satellite images (T1 and T2). Computes pixel differences, normalized changes, or spectral index deltas (e.g., NDVI).",
            task_capabilities=["change_detection", "temporal_analysis", "change_vqa"],
            accepted_modalities=[AssetModality.MULTISPECTRAL, AssetModality.RGB, AssetModality.GRAYSCALE],
            required_capabilities=[],  # Enforced dynamically by the relationship engine
            output_schema={
                "change_fraction": "float",
                "changed_pixel_count": "int",
                "region_count": "int",
                "threshold": "float",
                "analysis_type": "str"
            },
            version="1.0"
        )
        super().__init__(definition)
        self.analyzer = BiTemporalChangeAnalyzer(artifact_dir=artifact_dir)

    def execute(self, request: ToolRequest, assets: List[ImageAsset]) -> ToolResult:
        start_time = time.time()

        t1_id = request.parameters.get("t1_asset_id")
        t2_id = request.parameters.get("t2_asset_id")
        analysis_type = request.parameters.get("analysis_type", "pixel_diff")
        threshold = request.parameters.get("threshold", 0.1)
        min_region_size = request.parameters.get("min_region_size", 25)
        bands = request.parameters.get("bands", None)

        if not t1_id or not t2_id:
            return self._error_result(request, ToolErrorCode.INPUT_INVALID, "t1_asset_id and t2_asset_id are required.", start_time)

        # Locate assets
        t1_asset = next((a for a in assets if a.asset_id == t1_id), None)
        t2_asset = next((a for a in assets if a.asset_id == t2_id), None)

        if not t1_asset or not t2_asset:
            return self._error_result(request, ToolErrorCode.INPUT_INVALID, "One or both asset IDs not found in loaded assets.", start_time)

        try:
            # Run analysis
            result = self.analyzer.analyze(
                t1_asset=t1_asset,
                t2_asset=t2_asset,
                analysis_type=analysis_type,
                threshold=threshold,
                min_region_size=min_region_size,
                bands=bands
            )

            # Handle pipeline errors
            if "error" in result:
                error_code = getattr(ToolErrorCode, result["error"], ToolErrorCode.EXECUTION_FAILED)
                return self._error_result(request, error_code, result["message"], start_time)

            # Return success
            return ToolResult(
                request_id=request.request_id,
                tool_id=self.definition.tool_id,
                tool_version=self.definition.version,
                success=True,
                execution_duration_sec=time.time() - start_time,
                outputs=result["outputs"],
                metrics=result["metrics"],
                spatial_artifacts=result["spatial_artifacts"],
                visual_artifacts=result["visual_artifacts"],
                provenance=result["provenance"]
            )

        except Exception as e:
            return self._error_result(request, ToolErrorCode.EXECUTION_FAILED, f"Change analysis failed: {str(e)}", start_time)

    def _error_result(self, req: ToolRequest, code: ToolErrorCode, msg: str, start: float) -> ToolResult:
        return ToolResult(
            request_id=req.request_id,
            tool_id=self.definition.tool_id,
            tool_version=self.definition.version,
            success=False,
            execution_duration_sec=time.time() - start,
            error_code=code,
            error_message=msg
        )
