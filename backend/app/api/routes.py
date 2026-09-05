from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional, Dict
from pathlib import Path
import uuid
import shutil
import io

from app.domain.models import (
    AnalysisRequest, AnalysisResult, BoundingBox, ImageAsset,
    AssetFormat, AssetModality
)
from app.services.validator import InputValidator
from app.agent.registry import ToolRegistry
from app.agent.execution import ToolExecutionService
from app.agent.orchestrator import SatQueryAgent
from app.agent.providers import DummyLLMProvider, AgentExecutionPlan, AgentPlanStep
from app.analytics.tools import NdviTool, AreaTool, Qwen2VLTool
from app.analytics.change_tools import BiTemporalChangeTool
from app.analytics.sar_tools import SARAnalysisTool
from app.analytics.fusion_tools import CrossModalEvidenceTool

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# In-memory asset store (keyed by asset_id)
# ─────────────────────────────────────────────────────────────────────────────
_ASSET_STORE: Dict[str, ImageAsset] = {}
_UPLOADS_DIR = Path("uploads")
_UPLOADS_DIR.mkdir(exist_ok=True)

validator = InputValidator()


# ─────────────────────────────────────────────────────────────────────────────
# Dependency: SatQueryAgent
# ─────────────────────────────────────────────────────────────────────────────
from app.agent.providers import DummyLLMProvider, HeuristicLLMProvider, AgentExecutionPlan, AgentPlanStep
from app.analytics.models import Qwen2VLAdapter

def get_satquery_agent():
    registry = ToolRegistry()
    registry.register(NdviTool())
    registry.register(AreaTool())
    registry.register(BiTemporalChangeTool())
    registry.register(SARAnalysisTool())
    registry.register(CrossModalEvidenceTool())
    
    qwen_adapter = Qwen2VLAdapter()
    registry.register(Qwen2VLTool(qwen_adapter))

    execution_service = ToolExecutionService(registry)
    llm_provider = HeuristicLLMProvider()

    return SatQueryAgent(execution_service, llm_provider)


# ─────────────────────────────────────────────────────────────────────────────
# POST /upload
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/upload", response_model=ImageAsset)
async def upload_asset(
    file: UploadFile = File(...),
    role: Optional[str] = Form(None),
    acquisition_time: Optional[str] = Form(None),
):
    """Upload a satellite image. Returns ImageAsset with geospatial metadata."""
    asset_id = str(uuid.uuid4())
    suffix = Path(file.filename).suffix if file.filename else ".bin"
    save_path = _UPLOADS_DIR / f"{asset_id}{suffix}"

    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save failed: {e}")

    val = validator.validate(str(save_path))

    if val["errors"]:
        save_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail={"errors": val["errors"], "warnings": val["warnings"]}
        )

    bounds = None
    if val.get("geospatial_bounds"):
        b = val["geospatial_bounds"]
        bounds = BoundingBox(
            min_x=b["min_x"], min_y=b["min_y"],
            max_x=b["max_x"], max_y=b["max_y"]
        )

    from datetime import datetime
    acq_time = None
    if acquisition_time:
        try:
            acq_time = datetime.fromisoformat(acquisition_time)
        except Exception:
            pass

    asset = ImageAsset(
        asset_id=asset_id,
        filename=file.filename or f"asset{suffix}",
        mime_type=file.content_type or "application/octet-stream",
        format=val["format"],
        dimensions=val.get("dimensions"),
        band_count=val.get("band_count"),
        modality=val["modality"],
        crs=val.get("crs"),
        geospatial_bounds=bounds,
        transform=val.get("transform"),
        pixel_resolution=val.get("resolution"),
        band_semantics=val.get("band_semantics", {}),
        capabilities=val.get("capabilities", {}),
        metadata={"role": role or "UNKNOWN", "original_filename": file.filename},
        storage_location=str(save_path),
        validation_state="VALID",
        warnings=val.get("warnings", []),
        acquisition_time=acq_time,
    )

    _ASSET_STORE[asset_id] = asset
    return asset


# ─────────────────────────────────────────────────────────────────────────────
# GET /assets/{asset_id}
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/assets/{asset_id}", response_model=ImageAsset)
def get_asset(asset_id: str):
    asset = _ASSET_STORE.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


# ─────────────────────────────────────────────────────────────────────────────
# GET /assets/{asset_id}/thumbnail  →  PNG preview
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/assets/{asset_id}/thumbnail")
def get_thumbnail(asset_id: str, size: int = 256):
    asset = _ASSET_STORE.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    try:
        import rasterio
        import numpy as np
        from PIL import Image

        with rasterio.open(asset.storage_location) as src:
            band_count = src.count
            if band_count >= 3:
                data = src.read([1, 2, 3])
            else:
                data = src.read(1)
                data = np.stack([data, data, data], axis=0)

            out = np.zeros((3, data.shape[1], data.shape[2]), dtype=np.uint8)
            for i in range(3):
                band = data[i].astype(np.float32)
                b_min, b_max = band.min(), band.max()
                if b_max > b_min:
                    band = (band - b_min) / (b_max - b_min) * 255
                out[i] = band.clip(0, 255).astype(np.uint8)

            img_array = np.transpose(out, (1, 2, 0))
            img = Image.fromarray(img_array, mode="RGB")
            img.thumbnail((size, size), Image.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_bytes = buf.getvalue()

        return Response(content=png_bytes, media_type="image/png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Thumbnail generation failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# POST /analyze
# ─────────────────────────────────────────────────────────────────────────────
class AnalyzePayload(BaseModel):
    query: str
    asset_ids: List[str]
    roi: Optional[BoundingBox] = None


@router.post("/analyze", response_model=AnalysisResult)
def analyze(payload: AnalyzePayload, agent: SatQueryAgent = Depends(get_satquery_agent)):
    """Primary endpoint for natural language analysis queries."""
    request = AnalysisRequest(
        query=payload.query,
        input_asset_ids=payload.asset_ids,
        roi=payload.roi,
        session_context="session_web"
    )

    loaded_assets = []
    missing = []
    for aid in payload.asset_ids:
        asset = _ASSET_STORE.get(aid)
        if asset:
            loaded_assets.append(asset)
        else:
            missing.append(aid)

    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Assets not found in session: {missing}. Upload first via POST /api/v1/upload"
        )

    result = agent.process_request(request, loaded_assets)
    return result
