import pytest
import uuid
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from app.domain.models import ToolRequest, ImageAsset, AssetModality
from app.agent.registry import ToolRegistry
from app.agent.execution import ToolExecutionService
from app.analytics.tools import NdviTool
from app.analytics.models import DummySceneClassifierAdapter, SceneClassificationTool
from app.services.validator import InputValidator

def create_mock_raster(path, bands=4):
    transform = from_bounds(0, 0, 10, 10, 10, 10)
    with rasterio.open(
        path, 'w', driver='GTiff', height=10, width=10, count=bands,
        dtype=rasterio.uint8, crs='EPSG:32633', transform=transform
    ) as dst:
        for i in range(1, bands + 1):
            dst.write(np.ones((10, 10), dtype=rasterio.uint8) * i, i)

@pytest.fixture
def execution_env(tmp_path):
    registry = ToolRegistry()
    registry.register(NdviTool())
    
    adapter = DummySceneClassifierAdapter()
    registry.register(SceneClassificationTool(adapter))
    
    service = ToolExecutionService(registry)
    
    good_raster = str(tmp_path / "good.tif")
    create_mock_raster(good_raster, 4)
    
    bad_raster = str(tmp_path / "bad.tif")
    create_mock_raster(bad_raster, 1)
    
    return service, good_raster, bad_raster

def test_execution_service_success(execution_env):
    service, good_raster, _ = execution_env
    
    val = InputValidator()
    r = val.validate(good_raster)
    r["capabilities"]["can_ndvi"] = True
    r["band_semantics"] = {1: "BLUE", 2: "GREEN", 3: "RED", 4: "NIR"}
    asset = ImageAsset(asset_id="1", filename="good.tif", mime_type="image/tiff", storage_location=good_raster, **r)
    
    req = ToolRequest(
        request_id="req1", analysis_id="an1", tool_id="ndvi_calculator", input_asset_ids=["1"]
    )
    
    result = service.execute_tool(req, [asset])
    
    assert result.success is True
    assert "mean_ndvi" in result.metrics
    
    stages = [t.stage for t in result.trace_events]
    assert "TOOL_REQUESTED" in stages
    assert "EXECUTION_COMPLETED" in stages

def test_execution_service_capability_rejection(execution_env):
    service, _, bad_raster = execution_env
    
    val = InputValidator()
    r = val.validate(bad_raster)
    asset = ImageAsset(asset_id="2", filename="bad.tif", mime_type="image/tiff", storage_location=bad_raster, **r)
    
    req = ToolRequest(
        request_id="req2", analysis_id="an2", tool_id="ndvi_calculator", input_asset_ids=["2"]
    )
    
    result = service.execute_tool(req, [asset])
    
    assert result.success is False
    assert result.error_code == "CAPABILITY_UNSUPPORTED"
    
def test_execution_service_dummy_ml(execution_env):
    service, good_raster, _ = execution_env
    
    val = InputValidator()
    r = val.validate(good_raster)
    asset = ImageAsset(asset_id="1", filename="good.tif", mime_type="image/tiff", storage_location=good_raster, **r)
    
    req = ToolRequest(
        request_id="req3", analysis_id="an3", tool_id="scene_classifier", input_asset_ids=["1"]
    )
    
    result = service.execute_tool(req, [asset])
    assert result.success is True
    assert result.outputs.get("scene_class") == "Urban"
    assert "test_adapter" in result.provenance[0]
