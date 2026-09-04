import pytest
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from app.domain.models import AssetFormat, AssetModality, ImageAsset, BoundingBox, RelationshipType, AlignmentStatus
from app.services.validator import InputValidator
from app.services.relationship_engine import ImageRelationshipEngine
from app.analytics.deterministic import DeterministicAnalyticsEngine
import os

def create_synthetic_geotiff(path, crs, bounds, width, height, bands, dtype=rasterio.uint8, colorinterp=None):
    transform = from_bounds(*bounds, width, height)
    with rasterio.open(
        path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=bands,
        dtype=dtype,
        crs=crs,
        transform=transform,
    ) as dst:
        for i in range(1, bands + 1):
            dst.write(np.ones((height, width), dtype=dtype) * i, i)
        if colorinterp:
            dst.colorinterp = colorinterp

@pytest.fixture
def tmp_rasters(tmp_path):
    p1 = str(tmp_path / "valid_projected.tif")
    from rasterio.enums import ColorInterp
    ci = [ColorInterp.blue, ColorInterp.green, ColorInterp.red, ColorInterp.undefined]
    create_synthetic_geotiff(p1, 'EPSG:32633', (0, 0, 1000, 1000), 100, 100, 4, colorinterp=ci)
    
    p2 = str(tmp_path / "valid_geographic.tif")
    create_synthetic_geotiff(p2, 'EPSG:4326', (-10, -10, 10, 10), 100, 100, 3)

    p3 = str(tmp_path / "missing_crs.tif")
    create_synthetic_geotiff(p3, None, (0, 0, 1000, 1000), 100, 100, 1)

    p4 = str(tmp_path / "shifted_projected.tif")
    create_synthetic_geotiff(p4, 'EPSG:32633', (500, 0, 1500, 1000), 100, 100, 4, colorinterp=ci)

    return {"p1": p1, "p2": p2, "p3": p3, "p4": p4}

def test_validator_projected(tmp_rasters):
    val = InputValidator()
    res = val.validate(tmp_rasters["p1"])
    assert res["valid"] is True
    assert res["format"] == AssetFormat.GEOTIFF
    assert res["crs"] == "EPSG:32633"
    assert res["capabilities"]["can_area_measurement"] is True
    assert res["modality"] == AssetModality.MULTISPECTRAL
    assert res["band_semantics"][3] == "RED"

def test_validator_geographic(tmp_rasters):
    val = InputValidator()
    res = val.validate(tmp_rasters["p2"])
    assert res["valid"] is True
    assert res["crs"] == "EPSG:4326"
    assert res["capabilities"]["can_area_measurement"] is False
    assert any("geographic" in w for w in res["warnings"])

def test_validator_missing_crs(tmp_rasters):
    val = InputValidator()
    res = val.validate(tmp_rasters["p3"])
    assert res["crs"] is None
    assert any("No CRS" in w for w in res["warnings"])

def test_relationship_engine(tmp_rasters):
    val = InputValidator()
    r1 = val.validate(tmp_rasters["p1"])
    r4 = val.validate(tmp_rasters["p4"])

    a1 = ImageAsset(asset_id="1", filename="1", mime_type="image/tiff", storage_location="1", **r1)
    a4 = ImageAsset(asset_id="4", filename="4", mime_type="image/tiff", storage_location="4", **r4)

    engine = ImageRelationshipEngine()
    assessment = engine.assess([a1, a4])
    
    assert RelationshipType.PARTIALLY_OVERLAPPING in assessment.relationship_types
    assert assessment.alignment_status == AlignmentStatus.REQUIRES_REGISTRATION
    assert assessment.overlap_percentage_a == 50.0

def test_deterministic_ndvi():
    engine = DeterministicAnalyticsEngine()
    nir = np.array([[100, 255], [120, 80]], dtype=float)
    red = np.array([[50, 255], [60, 40]], dtype=float)
    
    ndvi = engine.calculate_ndvi(nir, red, nodata=255.0)
    assert np.isclose(ndvi[0,0], (100-50)/(100+50))
    assert ndvi.mask[0,1] == True 

def test_deterministic_area():
    engine = DeterministicAnalyticsEngine()
    mask = np.array([[True, False], [True, True]])
    
    res = engine.calculate_mask_area(mask, (10.0, 10.0), is_projected=True)
    assert res["valid"] is True
    assert res["total_area"] == 300.0
    
    res2 = engine.calculate_mask_area(mask, (0.0001, 0.0001), is_projected=False)
    assert res2["valid"] is False
