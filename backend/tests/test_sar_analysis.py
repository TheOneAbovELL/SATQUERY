import pytest
import numpy as np
import rasterio
from rasterio.transform import from_bounds
import os
from datetime import datetime

from app.domain.models import ImageAsset, ToolRequest, AssetModality
from app.analytics.sar_tools import SARAnalysisTool
from app.services.validator import InputValidator

def create_synthetic_sar_geotiff(path, crs, bounds, width, height, bands, dtype=rasterio.float32, polarizations=None, data_fill=None, bright_box=None):
    transform = from_bounds(*bounds, width, height)
    with rasterio.open(
        path, 'w', driver='GTiff', height=height, width=width, count=bands,
        dtype=dtype, crs=crs, transform=transform
    ) as dst:
        if polarizations:
            dst.update_tags(SENSOR="SENTINEL-1 SAR")
            # rasterio doesn't directly support setting descriptions easily in all versions without a workaround,
            # but we can set them like this:
            for i, pol in enumerate(polarizations, start=1):
                dst.set_band_description(i, pol)

        for i in range(1, bands + 1):
            if data_fill is not None:
                arr = np.full((height, width), data_fill, dtype=dtype)
            else:
                arr = np.random.uniform(0.1, 0.3, (height, width)).astype(dtype) # Background noise
                
            if bright_box is not None:
                cmin_r, cmax_r, cmin_c, cmax_c = bright_box
                arr[cmin_r:cmax_r, cmin_c:cmax_c] = 50.0 # Bright scatterer
                
            dst.write(arr, i)

@pytest.fixture
def tmp_sar_rasters(tmp_path):
    artifacts = str(tmp_path / "artifacts")
    os.makedirs(artifacts, exist_ok=True)
    
    base_bounds = (0, 0, 1000, 1000)
    
    # 1. Standard SAR image (VV, VH)
    p_sar_1 = str(tmp_path / "sar_1.tif")
    create_synthetic_sar_geotiff(p_sar_1, 'EPSG:32633', base_bounds, 100, 100, 2, polarizations=["VV", "VH"], bright_box=(20, 30, 40, 60))

    # 2. SAR image 2 for temporal change
    p_sar_2 = str(tmp_path / "sar_2.tif")
    create_synthetic_sar_geotiff(p_sar_2, 'EPSG:32633', base_bounds, 100, 100, 2, polarizations=["VV", "VH"], data_fill=0.2, bright_box=(20, 30, 40, 60))

    val = InputValidator()
    
    def make_asset(id, p):
        res = val.validate(p)
        return ImageAsset(asset_id=id, filename=os.path.basename(p), mime_type="image/tiff", storage_location=p, acquisition_time=datetime.now(), **res)
        
    return {
        "artifacts": artifacts,
        "sar_1": make_asset("sar_1", p_sar_1),
        "sar_2": make_asset("sar_2", p_sar_2)
    }

def test_sar_validation_modality(tmp_sar_rasters):
    asset = tmp_sar_rasters["sar_1"]
    assert asset.modality == AssetModality.SAR
    assert asset.band_semantics[1] == "VV"
    assert asset.band_semantics[2] == "VH"

def test_sar_descriptive_statistics(tmp_sar_rasters):
    tool = SARAnalysisTool(artifact_dir=tmp_sar_rasters["artifacts"])
    req = ToolRequest(request_id="1", analysis_id="a1", tool_id="sar_analysis", input_asset_ids=["sar_1"], parameters={"asset_id": "sar_1", "analysis_type": "descriptive_statistics"})
    
    res = tool.execute(req, [tmp_sar_rasters["sar_1"]])
    
    assert res.success is True
    assert res.metrics["max"] >= 50.0 # Bright scatterer
    assert res.metrics["valid_pixel_count"] == 10000
    assert len(res.visual_artifacts) == 1 # PNG generated

def test_sar_backscatter_threshold(tmp_sar_rasters):
    tool = SARAnalysisTool(artifact_dir=tmp_sar_rasters["artifacts"])
    req = ToolRequest(request_id="2", analysis_id="a2", tool_id="sar_analysis", input_asset_ids=["sar_1"], parameters={"asset_id": "sar_1", "analysis_type": "backscatter_threshold", "threshold": 40.0})
    
    res = tool.execute(req, [tmp_sar_rasters["sar_1"]])
    
    assert res.success is True
    assert res.outputs["threshold_used"] == 40.0
    assert res.outputs["region_count"] == 1
    
    region = res.spatial_artifacts[0]
    assert region["pixel_count"] == 200 # 10x20 box
    assert "area" in region

def test_sar_temporal_change(tmp_sar_rasters):
    tool = SARAnalysisTool(artifact_dir=tmp_sar_rasters["artifacts"])
    # Testing the routing to BiTemporal tool
    req = ToolRequest(request_id="3", analysis_id="a3", tool_id="sar_analysis", input_asset_ids=["sar_1", "sar_2"], parameters={"t1_asset_id": "sar_1", "t2_asset_id": "sar_2", "analysis_type": "temporal_change", "threshold": 10.0})
    
    res = tool.execute(req, [tmp_sar_rasters["sar_1"], tmp_sar_rasters["sar_2"]])
    
    assert res.success is True
    assert "changed_pixel_count" in res.outputs
    # Given sar_1 is random noise (0.1-0.3) + 50 box, and sar_2 is constant 0.2 + 50 box
    # The change in the 50 box is 0. The background change is small (<1.0), so threshold 10.0 -> 0 change.
    assert res.outputs["changed_pixel_count"] == 0
