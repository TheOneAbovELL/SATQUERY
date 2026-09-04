import time
from typing import List

from app.agent.interfaces import BaseTool
from app.domain.models import ToolDefinition, ToolRequest, ToolResult, ToolErrorCode, ImageAsset, AssetModality
from app.analytics.sar_analysis import SARAnalyzer
from app.analytics.change_tools import BiTemporalChangeTool


class SARAnalysisTool(BaseTool):
    """
    Specialist tool for analyzing Synthetic Aperture Radar (SAR) imagery.
    Handles single-image stats and bright-target thresholds.
    For bi-temporal SAR change, it routes internally to the BiTemporalChangeAnalyzer.
    """
    def __init__(self, artifact_dir: str = "./artifacts"):
        definition = ToolDefinition(
            tool_id="sar_analysis",
            name="SAR Analysis Specialist",
            description="Analyzes SAR imagery. Provides backscatter statistics, threshold-based bright target detection, and SAR-safe visualization. Supports temporal SAR change detection.",
            task_capabilities=["sar_analysis", "backscatter_detection", "sar_statistics", "sar_temporal_change"],
            accepted_modalities=[AssetModality.SAR],
            output_schema={
                "analysis_type": "str",
                "threshold_used": "float",
                "region_count": "int"
            },
            version="1.0"
        )
        super().__init__(definition)
        self.analyzer = SARAnalyzer(artifact_dir=artifact_dir)
        self.change_tool = BiTemporalChangeTool(artifact_dir=artifact_dir)

    def execute(self, request: ToolRequest, assets: List[ImageAsset]) -> ToolResult:
        start_time = time.time()
        
        analysis_type = request.parameters.get("analysis_type", "descriptive_statistics")
        
        # Route SAR change detection to the BiTemporal tool logic directly.
        if analysis_type == "temporal_change":
            # Override request parameters to force absolute pixel difference for SAR change
            req_params = dict(request.parameters)
            req_params["analysis_type"] = "pixel_diff"
            request.parameters = req_params
            return self.change_tool.execute(request, assets)

        asset_id = request.parameters.get("asset_id")
        if not asset_id:
            return self._error_result(request, ToolErrorCode.INPUT_INVALID, "asset_id is required.", start_time)
            
        asset = next((a for a in assets if a.asset_id == asset_id), None)
        if not asset:
            return self._error_result(request, ToolErrorCode.INPUT_INVALID, "asset_id not found in loaded assets.", start_time)

        if asset.modality != AssetModality.SAR:
            # We don't fail outright if the user forces it, but we warn.
            # Some SAR files might not be perfectly tagged.
            pass

        polarization = request.parameters.get("polarization")
        threshold = request.parameters.get("threshold")
        min_region_size = request.parameters.get("min_region_size", 25)
        to_db = request.parameters.get("to_db", True)

        try:
            result = self.analyzer.analyze(
                asset=asset,
                analysis_type=analysis_type,
                polarization=polarization,
                threshold=threshold,
                min_region_size=min_region_size,
                to_db=to_db
            )

            if "error" in result:
                code = getattr(ToolErrorCode, result["error"], ToolErrorCode.EXECUTION_FAILED)
                return self._error_result(request, code, result["message"], start_time)

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
            return self._error_result(request, ToolErrorCode.EXECUTION_FAILED, f"SAR analysis failed: {str(e)}", start_time)

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
