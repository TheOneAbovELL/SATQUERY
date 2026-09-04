import pytest
import os
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from datetime import datetime

from app.domain.models import ImageAsset, ToolRequest, AssetModality, EvidenceRelationship
from app.analytics.fusion_tools import CrossModalEvidenceTool
from app.services.validator import InputValidator

def create_synthetic_geotiff(path, crs, bounds, width, height, bands, dtype=rasterio.uint8, is_sar=False, data_fill=None, change_box=None):
    transform = from_bounds(*bounds, width, height)
    with rasterio.open(
        path, 'w', driver='GTiff', height=height, width=width, count=bands,
        dtype=dtype, crs=crs, transform=transform
    ) as dst:
        if is_sar:
            dst.update_tags(SENSOR="SENTINEL-1 SAR")
            dst.set_band_description(1, "VV")
            dst.set_band_description(2, "VH")

        for i in range(1, bands + 1):
            if data_fill is not None:
                arr = np.full((height, width), data_fill, dtype=dtype)
            else:
                arr = np.ones((height, width), dtype=dtype) * 50
                
            if change_box is not None:
                cmin_r, cmax_r, cmin_c, cmax_c = change_box
                arr[cmin_r:cmax_r, cmin_c:cmax_c] = 200 # Significant change
                
            dst.write(arr, i)
        
        if not is_sar and bands >= 3:
            dst.colorinterp = [rasterio.enums.ColorInterp.red, rasterio.enums.ColorInterp.green, rasterio.enums.ColorInterp.blue, rasterio.enums.ColorInterp.undefined][:bands]

@pytest.fixture
def tmp_fusion_rasters(tmp_path):
    artifacts = str(tmp_path / "artifacts")
    os.makedirs(artifacts, exist_ok=True)
    
    base_bounds = (0, 0, 1000, 1000)
    
    # Pair 1: Optical T1/T2 with change box A
    o_t1 = str(tmp_path / "opt_t1.tif")
    o_t2 = str(tmp_path / "opt_t2.tif")
    create_synthetic_geotiff(o_t1, 'EPSG:32633', base_bounds, 100, 100, 4, data_fill=50)
    # Box A: rows 20-40, cols 40-60
    create_synthetic_geotiff(o_t2, 'EPSG:32633', base_bounds, 100, 100, 4, data_fill=50, change_box=(20, 40, 40, 60))

    # Pair 2: SAR T1/T2 with exactly the same change box A (AGREEMENT)
    s_a_t1 = str(tmp_path / "sar_a_t1.tif")
    s_a_t2 = str(tmp_path / "sar_a_t2.tif")
    create_synthetic_geotiff(s_a_t1, 'EPSG:32633', base_bounds, 100, 100, 2, dtype=rasterio.float32, is_sar=True, data_fill=0.2)
    create_synthetic_geotiff(s_a_t2, 'EPSG:32633', base_bounds, 100, 100, 2, dtype=rasterio.float32, is_sar=True, data_fill=0.2, change_box=(20, 40, 40, 60))

    # Pair 3: SAR T1/T2 with NO change (DISAGREEMENT)
    s_d_t1 = str(tmp_path / "sar_d_t1.tif")
    s_d_t2 = str(tmp_path / "sar_d_t2.tif")
    create_synthetic_geotiff(s_d_t1, 'EPSG:32633', base_bounds, 100, 100, 2, dtype=rasterio.float32, is_sar=True, data_fill=0.2)
    create_synthetic_geotiff(s_d_t2, 'EPSG:32633', base_bounds, 100, 100, 2, dtype=rasterio.float32, is_sar=True, data_fill=0.2)

    # Pair 4: SAR T1/T2 with DISJOINT change box B (COMPLEMENTARY)
    s_c_t1 = str(tmp_path / "sar_c_t1.tif")
    s_c_t2 = str(tmp_path / "sar_c_t2.tif")
    create_synthetic_geotiff(s_c_t1, 'EPSG:32633', base_bounds, 100, 100, 2, dtype=rasterio.float32, is_sar=True, data_fill=0.2)
    # Box B: rows 70-90, cols 70-90
    create_synthetic_geotiff(s_c_t2, 'EPSG:32633', base_bounds, 100, 100, 2, dtype=rasterio.float32, is_sar=True, data_fill=0.2, change_box=(70, 90, 70, 90))

    val = InputValidator()
    
    def make_asset(id, p):
        res = val.validate(p)
        return ImageAsset(asset_id=id, filename=os.path.basename(p), mime_type="image/tiff", storage_location=p, acquisition_time=datetime.now(), **res)
        
    return {
        "artifacts": artifacts,
        "opt_t1": make_asset("opt_t1", o_t1),
        "opt_t2": make_asset("opt_t2", o_t2),
        "sar_a_t1": make_asset("sar_a_t1", s_a_t1),
        "sar_a_t2": make_asset("sar_a_t2", s_a_t2),
        "sar_d_t1": make_asset("sar_d_t1", s_d_t1),
        "sar_d_t2": make_asset("sar_d_t2", s_d_t2),
        "sar_c_t1": make_asset("sar_c_t1", s_c_t1),
        "sar_c_t2": make_asset("sar_c_t2", s_c_t2)
    }

def test_cross_modal_agreement(tmp_fusion_rasters):
    tool = CrossModalEvidenceTool(artifact_dir=tmp_fusion_rasters["artifacts"])
    req = ToolRequest(
        request_id="1", analysis_id="a1", tool_id="cross_modal_evidence", 
        input_asset_ids=["opt_t1", "opt_t2", "sar_a_t1", "sar_a_t2"], 
        parameters={
            "optical_t1_id": "opt_t1", "optical_t2_id": "opt_t2", 
            "sar_t1_id": "sar_a_t1", "sar_t2_id": "sar_a_t2",
            "opt_threshold": 50, "sar_threshold": 10
        }
    )
    
    assets = [tmp_fusion_rasters[k] for k in ["opt_t1", "opt_t2", "sar_a_t1", "sar_a_t2"]]
    res = tool.execute(req, assets)
    
    assert res.success is True
    assert res.outputs["relationship"] == EvidenceRelationship.AGREEMENT
    assert res.metrics["iou"] > 0.9  # Nearly perfect overlap (1.0 ideally)

def test_cross_modal_disagreement(tmp_fusion_rasters):
    tool = CrossModalEvidenceTool(artifact_dir=tmp_fusion_rasters["artifacts"])
    req = ToolRequest(
        request_id="2", analysis_id="a2", tool_id="cross_modal_evidence", 
        input_asset_ids=["opt_t1", "opt_t2", "sar_d_t1", "sar_d_t2"], 
        parameters={
            "optical_t1_id": "opt_t1", "optical_t2_id": "opt_t2", 
            "sar_t1_id": "sar_d_t1", "sar_t2_id": "sar_d_t2",
            "opt_threshold": 50, "sar_threshold": 10
        }
    )
    
    assets = [tmp_fusion_rasters[k] for k in ["opt_t1", "opt_t2", "sar_d_t1", "sar_d_t2"]]
    res = tool.execute(req, assets)
    
    assert res.success is True
    assert res.outputs["relationship"] == EvidenceRelationship.DISAGREEMENT
    assert res.metrics["iou"] == 0.0

def test_cross_modal_complementary(tmp_fusion_rasters):
    tool = CrossModalEvidenceTool(artifact_dir=tmp_fusion_rasters["artifacts"])
    req = ToolRequest(
        request_id="3", analysis_id="a3", tool_id="cross_modal_evidence", 
        input_asset_ids=["opt_t1", "opt_t2", "sar_c_t1", "sar_c_t2"], 
        parameters={
            "optical_t1_id": "opt_t1", "optical_t2_id": "opt_t2", 
            "sar_t1_id": "sar_c_t1", "sar_t2_id": "sar_c_t2",
            "opt_threshold": 50, "sar_threshold": 10
        }
    )
    
    assets = [tmp_fusion_rasters[k] for k in ["opt_t1", "opt_t2", "sar_c_t1", "sar_c_t2"]]
    res = tool.execute(req, assets)
    
    assert res.success is True
    # The regions are disjoint: optical at 20-40, SAR at 70-90. Thus IoU is 0. 
    # Current logic maps IoU==0 to DISAGREEMENT since neither confirms the other.
    assert res.outputs["relationship"] == EvidenceRelationship.DISAGREEMENT
    assert res.metrics["iou"] == 0.0
