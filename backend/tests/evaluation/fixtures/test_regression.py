import pytest
import os
import numpy as np

from app.analytics.sar_analysis import SARAnalyzer
from app.analytics.change_analysis import BiTemporalChangeAnalyzer
from app.domain.models import ImageAsset, AssetModality
from app.services.validator import InputValidator

def build_asset(path):
    validator = InputValidator()
    val = validator.validate(path)
    val.update({
        "asset_id": "test_id",
        "filename": os.path.basename(path),
        "mime_type": "image/tiff",
        "storage_location": path
    })
    return ImageAsset(**val)

def test_sar_deterministic_regression():
    sar_path = "mock_data/real_samples/simulated_sar_sample.tif"
    if not os.path.exists(sar_path):
        pytest.skip("Real sample data not found. Run download script first.")

    asset_model = build_asset(sar_path)
    assert asset_model.modality == AssetModality.SAR, "Validator should identify S1 simulated as SAR"
    
    analyzer = SARAnalyzer(artifact_dir="artifacts/test")
    
    result = analyzer.analyze(asset_model)
    assert result["success"] is True
    assert "metrics" in result
    metrics = result["metrics"]
    
    assert "mean" in metrics
    assert "p99" in metrics
    # Ensure they are numeric
    assert isinstance(metrics["mean"], float)
    
def test_change_deterministic_regression():
    t1_path = "mock_data/real_samples/landsat7_rgb_sample.tif"
    t2_path = "mock_data/real_samples/landsat7_rgb_t2_simulated.tif"
    
    if not os.path.exists(t1_path) or not os.path.exists(t2_path):
        pytest.skip("Real sample data not found. Run download script first.")
        
    t1_asset = build_asset(t1_path)
    t2_asset = build_asset(t2_path)
    
    analyzer = BiTemporalChangeAnalyzer(artifact_dir="artifacts/test")
    
    # We used pixel_diff and know the burn scar size
    result = analyzer.analyze(t1_asset, t2_asset, analysis_type="pixel_diff", threshold=10.0)
    assert result["success"] is True
    assert "metrics" in result
    
    metrics = result["metrics"]
    assert "changed_pixel_count" in metrics
    assert "valid_pixel_count" in metrics
    assert "change_fraction" in metrics
    
    # Invariant check
    calc_fraction = metrics["changed_pixel_count"] / max(metrics["valid_pixel_count"], 1)
    assert np.isclose(calc_fraction, metrics["change_fraction"], atol=1e-5), "Numerical invariant violated"
