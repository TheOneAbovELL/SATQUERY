import pytest
import numpy as np
import rasterio
from rasterio.transform import from_bounds
import os
from datetime import datetime, timedelta

from app.domain.models import ImageAsset, ToolRequest, ToolErrorCode
from app.analytics.change_tools import BiTemporalChangeTool
from app.services.validator import InputValidator

def create_synthetic_geotiff(path, crs, bounds, width, height, bands, dtype=rasterio.uint8, colorinterp=None, data_fill=None, change_box=None):
    transform = from_bounds(*bounds, width, height)
    with rasterio.open(
        path, 'w', driver='GTiff', height=height, width=width, count=bands,
        dtype=dtype, crs=crs, transform=transform
    ) as dst:
        for i in range(1, bands + 1):
            if data_fill is not None:
                arr = np.full((height, width), data_fill, dtype=dtype)
            else:
                arr = np.ones((height, width), dtype=dtype) * 50
                
            if change_box is not None:
                cmin_r, cmax_r, cmin_c, cmax_c = change_box
                arr[cmin_r:cmax_r, cmin_c:cmax_c] = 200 # Significant change
                
            dst.write(arr, i)
        if colorinterp:
            dst.colorinterp = colorinterp

@pytest.fixture
def tmp_change_rasters(tmp_path):
    artifacts = str(tmp_path / "artifacts")
    os.makedirs(artifacts, exist_ok=True)
    
    ci = [rasterio.enums.ColorInterp.red, rasterio.enums.ColorInterp.green, rasterio.enums.ColorInterp.blue, rasterio.enums.ColorInterp.undefined]
    
    # Base configuration: 100x100 pixels
    base_bounds = (0, 0, 1000, 1000)
    
    # Pair 1: Identical
    p_id_1 = str(tmp_path / "id_1.tif")
    p_id_2 = str(tmp_path / "id_2.tif")
    create_synthetic_geotiff(p_id_1, 'EPSG:32633', base_bounds, 100, 100, 4, colorinterp=ci)
    create_synthetic_geotiff(p_id_2, 'EPSG:32633', base_bounds, 100, 100, 4, colorinterp=ci)

    # Pair 2: Known rectangular change
    p_ch_1 = str(tmp_path / "ch_1.tif")
    p_ch_2 = str(tmp_path / "ch_2.tif")
    create_synthetic_geotiff(p_ch_1, 'EPSG:32633', base_bounds, 100, 100, 4, colorinterp=ci, data_fill=50)
    # Change box: rows 20-30, cols 40-60 (10x20 = 200 pixels)
    create_synthetic_geotiff(p_ch_2, 'EPSG:32633', base_bounds, 100, 100, 4, colorinterp=ci, data_fill=50, change_box=(20, 30, 40, 60))

    # Pair 3: Partial overlap
    p_po_1 = str(tmp_path / "po_1.tif")
    p_po_2 = str(tmp_path / "po_2.tif")
    create_synthetic_geotiff(p_po_1, 'EPSG:32633', (0, 0, 1000, 1000), 100, 100, 4, colorinterp=ci)
    create_synthetic_geotiff(p_po_2, 'EPSG:32633', (500, 500, 1500, 1500), 100, 100, 4, colorinterp=ci)

    # Pair 4: Different CRS (Geographic vs Projected)
    p_crs_1 = str(tmp_path / "crs_1.tif")
    p_crs_2 = str(tmp_path / "crs_2.tif")
    create_synthetic_geotiff(p_crs_1, 'EPSG:4326', (-10, -10, 10, 10), 100, 100, 4, colorinterp=ci)
    create_synthetic_geotiff(p_crs_2, 'EPSG:4326', (-10, -10, 10, 10), 100, 100, 4, colorinterp=ci, change_box=(20, 30, 40, 60))

    val = InputValidator()
    
    def make_asset(id, p):
        res = val.validate(p)
        return ImageAsset(asset_id=id, filename=os.path.basename(p), mime_type="image/tiff", storage_location=p, acquisition_time=datetime.now(), **res)
        
    return {
        "artifacts": artifacts,
        "id_1": make_asset("id_1", p_id_1),
        "id_2": make_asset("id_2", p_id_2),
        "ch_1": make_asset("ch_1", p_ch_1),
        "ch_2": make_asset("ch_2", p_ch_2),
        "po_1": make_asset("po_1", p_po_1),
        "po_2": make_asset("po_2", p_po_2),
        "crs_1": make_asset("crs_1", p_crs_1),
        "crs_2": make_asset("crs_2", p_crs_2)
    }

def test_identical_images_zero_change(tmp_change_rasters):
    tool = BiTemporalChangeTool(artifact_dir=tmp_change_rasters["artifacts"])
    req = ToolRequest(request_id="1", analysis_id="a1", tool_id="bi_temporal_change_analysis", input_asset_ids=["id_1", "id_2"], parameters={"t1_asset_id": "id_1", "t2_asset_id": "id_2", "threshold": 0.1})
    
    res = tool.execute(req, [tmp_change_rasters["id_1"], tmp_change_rasters["id_2"]])
    
    assert res.success is True
    assert res.outputs["changed_pixel_count"] == 0
    assert res.outputs["change_fraction"] == 0.0
    assert res.outputs["region_count"] == 0

def test_known_rectangular_change(tmp_change_rasters):
    tool = BiTemporalChangeTool(artifact_dir=tmp_change_rasters["artifacts"])
    req = ToolRequest(request_id="2", analysis_id="a2", tool_id="bi_temporal_change_analysis", input_asset_ids=["ch_1", "ch_2"], parameters={"t1_asset_id": "ch_1", "t2_asset_id": "ch_2", "threshold": 50})
    
    res = tool.execute(req, [tmp_change_rasters["ch_1"], tmp_change_rasters["ch_2"]])
    
    assert res.success is True
    assert res.outputs["changed_pixel_count"] == 200 # 10x20 region
    assert res.outputs["change_fraction"] == 0.02 # 200 / 10000
    assert res.outputs["region_count"] == 1
    
    region = res.spatial_artifacts[0]
    assert region["pixel_count"] == 200
    assert region["bbox"]["row_min"] == 20
    assert region["bbox"]["row_max"] == 29
    assert region["bbox"]["col_min"] == 40
    assert region["bbox"]["col_max"] == 59
    assert "area" in region

def test_partial_overlap_filtering(tmp_change_rasters):
    tool = BiTemporalChangeTool(artifact_dir=tmp_change_rasters["artifacts"])
    req = ToolRequest(request_id="3", analysis_id="a3", tool_id="bi_temporal_change_analysis", input_asset_ids=["po_1", "po_2"], parameters={"t1_asset_id": "po_1", "t2_asset_id": "po_2"})
    
    res = tool.execute(req, [tmp_change_rasters["po_1"], tmp_change_rasters["po_2"]])
    assert res.success is True
    assert res.metrics["valid_pixel_count"] == 2500 # Overlap is 50x50 pixels of the 100x100
    assert res.outputs["changed_pixel_count"] == 0

def test_geographic_crs_area_unavailable(tmp_change_rasters):
    tool = BiTemporalChangeTool(artifact_dir=tmp_change_rasters["artifacts"])
    req = ToolRequest(request_id="4", analysis_id="a4", tool_id="bi_temporal_change_analysis", input_asset_ids=["crs_1", "crs_2"], parameters={"t1_asset_id": "crs_1", "t2_asset_id": "crs_2", "threshold": 50})
    
    res = tool.execute(req, [tmp_change_rasters["crs_1"], tmp_change_rasters["crs_2"]])
    assert res.success is True
    assert res.outputs["changed_pixel_count"] == 200
    assert res.metrics.get("changed_area") is None
    assert "unavailable" in res.outputs["area_units"]

def test_provenance_and_artifacts(tmp_change_rasters):
    tool = BiTemporalChangeTool(artifact_dir=tmp_change_rasters["artifacts"])
    req = ToolRequest(request_id="5", analysis_id="a5", tool_id="bi_temporal_change_analysis", input_asset_ids=["ch_1", "ch_2"], parameters={"t1_asset_id": "ch_1", "t2_asset_id": "ch_2"})
    
    res = tool.execute(req, [tmp_change_rasters["ch_1"], tmp_change_rasters["ch_2"]])
    assert res.success is True
    assert len(res.visual_artifacts) > 0
    assert len(res.provenance) > 0
    
    mask_file = res.visual_artifacts[0]
    assert os.path.exists(mask_file)

def test_delta_ndvi(tmp_change_rasters):
    # Overwrite semantics for testing to ensure NDVI runs
    a1, a2 = tmp_change_rasters["ch_1"], tmp_change_rasters["ch_2"]
    a1.band_semantics = {1: "RED", 2: "GREEN", 3: "BLUE", 4: "NIR"}
    a2.band_semantics = {1: "RED", 2: "GREEN", 3: "BLUE", 4: "NIR"}
    
    tool = BiTemporalChangeTool(artifact_dir=tmp_change_rasters["artifacts"])
    req = ToolRequest(request_id="6", analysis_id="a6", tool_id="bi_temporal_change_analysis", input_asset_ids=["ch_1", "ch_2"], parameters={"t1_asset_id": "ch_1", "t2_asset_id": "ch_2", "analysis_type": "delta_ndvi", "threshold": 0.01})
    
    res = tool.execute(req, [a1, a2])
    assert res.success is True
    assert res.outputs["analysis_type"] == "delta_ndvi"
