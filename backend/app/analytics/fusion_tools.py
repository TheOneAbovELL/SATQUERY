import time
from typing import List, Dict, Any

from app.agent.interfaces import BaseTool
from app.domain.models import (
    ToolDefinition, ToolRequest, ToolResult, ToolErrorCode, ImageAsset,
    AssetModality, EvidenceItem, EvidenceRelationship
)
from app.analytics.cross_modal import CrossModalAnalyzer
from app.analytics.change_tools import BiTemporalChangeTool
from app.analytics.sar_tools import SARAnalysisTool

class CrossModalEvidenceTool(BaseTool):
    """
    Orchestrates optical and SAR specialists, extracting EvidenceItems,
    and classifying their spatial relationships.
    """
    def __init__(self, artifact_dir: str = "./artifacts"):
        definition = ToolDefinition(
            tool_id="cross_modal_evidence",
            name="Cross-Modal Evidence Intelligence",
            description="Fuses optical and SAR evidence to determine Agreement, Disagreement, or Complementarity based on spatial overlap of their signals.",
            task_capabilities=["multimodal_fusion", "optical_sar_comparison", "evidence_validation"],
            accepted_modalities=[AssetModality.OPTICAL, AssetModality.MULTISPECTRAL, AssetModality.SAR, AssetModality.RGB],
            output_schema={
                "relationship": "str",
                "iou": "float",
                "explanation": "str"
            },
            version="1.0"
        )
        super().__init__(definition)
        self.analyzer = CrossModalAnalyzer()
        self.optical_tool = BiTemporalChangeTool(artifact_dir=artifact_dir)
        self.sar_tool = SARAnalysisTool(artifact_dir=artifact_dir)

    def execute(self, request: ToolRequest, assets: List[ImageAsset]) -> ToolResult:
        start_time = time.time()
        
        # 1. Parameter parsing
        opt_t1_id = request.parameters.get("optical_t1_id")
        opt_t2_id = request.parameters.get("optical_t2_id")
        sar_t1_id = request.parameters.get("sar_t1_id")
        sar_t2_id = request.parameters.get("sar_t2_id")
        
        # For simplicity, if user provides single assets instead of pairs, we route to standard tools
        # For this prototype, we'll assume we are looking for change agreement (T1/T2 pairs for both).
        
        if not (opt_t1_id and opt_t2_id and sar_t1_id and sar_t2_id):
            return self._error_result(request, ToolErrorCode.INPUT_INVALID, "Missing required temporal pairs for cross-modal change analysis.", start_time)

        # 2. Run Optical Evidence
        opt_req = ToolRequest(
            request_id=f"{request.request_id}_opt",
            analysis_id=request.analysis_id,
            tool_id="bi_temporal_change_analysis",
            input_asset_ids=[opt_t1_id, opt_t2_id],
            parameters={"t1_asset_id": opt_t1_id, "t2_asset_id": opt_t2_id, "analysis_type": "pixel_diff", "threshold": request.parameters.get("opt_threshold", 0.1)}
        )
        opt_res = self.optical_tool.execute(opt_req, assets)
        if not opt_res.success:
            return self._error_result(request, opt_res.error_code, f"Optical specialist failed: {opt_res.error_message}", start_time)

        # 3. Run SAR Evidence
        sar_req = ToolRequest(
            request_id=f"{request.request_id}_sar",
            analysis_id=request.analysis_id,
            tool_id="sar_analysis",
            input_asset_ids=[sar_t1_id, sar_t2_id],
            parameters={"t1_asset_id": sar_t1_id, "t2_asset_id": sar_t2_id, "analysis_type": "temporal_change", "threshold": request.parameters.get("sar_threshold", 10.0)}
        )
        sar_res = self.sar_tool.execute(sar_req, assets)
        if not sar_res.success:
            return self._error_result(request, sar_res.error_code, f"SAR specialist failed: {sar_res.error_message}", start_time)

        # 4. Construct EvidenceItems
        opt_evidence = EvidenceItem(
            modality=AssetModality.OPTICAL,
            observation="Optical change detected.",
            metrics=opt_res.outputs,
            spatial_artifacts=opt_res.spatial_artifacts,
            source_tool=opt_res.tool_id,
            provenance=opt_res.provenance
        )
        
        sar_evidence = EvidenceItem(
            modality=AssetModality.SAR,
            observation="SAR backscatter change detected.",
            metrics=sar_res.outputs,
            spatial_artifacts=sar_res.spatial_artifacts,
            source_tool=sar_res.tool_id,
            provenance=sar_res.provenance
        )

        # 5. Cross-Modal Comparison
        fusion_result = self.analyzer.compare_evidence(opt_evidence, sar_evidence)
        
        relationship = fusion_result["relationship"]
        
        # 6. Build Final Result
        provenance = [
            f"Optical T1: {opt_t1_id}, Optical T2: {opt_t2_id}",
            f"SAR T1: {sar_t1_id}, SAR T2: {sar_t2_id}",
            "--- OPTICAL PROVENANCE ---"
        ] + opt_evidence.provenance + [
            "--- SAR PROVENANCE ---"
        ] + sar_evidence.provenance + [
            "--- CROSS-MODAL PROVENANCE ---"
        ] + fusion_result["provenance"]

        outputs = {
            "relationship": relationship.value,
            "explanation": fusion_result["explanation"]
        }
        
        metrics = {}
        for k, v in fusion_result["metrics"].items():
            if v is not None:
                metrics[k] = float(v)

        # Return visual artifacts from both
        visual_artifacts = opt_res.visual_artifacts + sar_res.visual_artifacts

        return ToolResult(
            request_id=request.request_id,
            tool_id=self.definition.tool_id,
            tool_version=self.definition.version,
            success=True,
            execution_duration_sec=time.time() - start_time,
            outputs=outputs,
            metrics=metrics,
            spatial_artifacts=opt_res.spatial_artifacts + sar_res.spatial_artifacts,
            visual_artifacts=visual_artifacts,
            provenance=provenance
        )

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
