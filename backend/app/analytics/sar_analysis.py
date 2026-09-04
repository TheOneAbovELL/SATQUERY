import os
import time
import numpy as np
import rasterio
from typing import Dict, Any, List

from app.domain.models import ImageAsset
from app.analytics.deterministic import DeterministicAnalyticsEngine
from app.analytics.preprocessing import RasterSARConverter

class SARAnalyzer:
    """
    Orchestrates SAR-specific single-image analysis.
    Computes statistics, finds threshold regions, and safely visualizes SAR anomalies.
    """
    def __init__(self, artifact_dir: str = "./artifacts"):
        self.analytics_engine = DeterministicAnalyticsEngine()
        self.sar_converter = RasterSARConverter()
        self.artifact_dir = artifact_dir
        os.makedirs(self.artifact_dir, exist_ok=True)

    def analyze(self, asset: ImageAsset, 
                analysis_type: str = "descriptive_statistics",
                polarization: str = None,
                threshold: float = None,
                min_region_size: int = 25,
                to_db: bool = True) -> Dict[str, Any]:
        """
        Executes deterministic SAR analysis and generates visual artifacts.
        """
        start_time = time.time()
        provenance = []

        try:
            with rasterio.open(asset.storage_location) as src:
                # Select band based on polarization
                band_idx = 1
                if polarization:
                    pol_upper = polarization.upper()
                    found = False
                    for k, v in asset.band_semantics.items():
                        if v == pol_upper:
                            band_idx = k
                            found = True
                            break
                    if not found:
                        return {"error": "INPUT_INVALID", "message": f"Polarization '{polarization}' not found in asset."}
                    provenance.append(f"Selected polarization: {pol_upper}")
                else:
                    # Default to first band if not specified
                    provenance.append("Using default (first) band for SAR analysis.")
                
                data = src.read(band_idx)
                nodata = src.nodata
                res = (abs(src.transform.a), abs(src.transform.e))
                is_proj = src.crs.is_projected if src.crs else False
        except Exception as e:
            return {"error": "EXECUTION_FAILED", "message": f"Failed to read SAR asset: {str(e)}"}

        outputs = {"analysis_type": analysis_type}
        metrics = {}
        spatial_artifacts = []
        
        # Determine stats
        stats = self.analytics_engine.compute_sar_statistics(data, nodata=nodata)
        metrics.update(stats)
        
        if analysis_type == "backscatter_threshold":
            if threshold is None:
                # If threshold not provided, use p99 as a heuristic bright-target threshold
                threshold = stats["p99"]
                provenance.append(f"Threshold not provided. Using p99 value: {threshold:.2f}")
            else:
                provenance.append(f"Using provided backscatter threshold: {threshold}")
                
            regions = self.analytics_engine.extract_backscatter_regions(
                band=data,
                threshold=threshold,
                direction="above",
                min_region_size=min_region_size,
                nodata=nodata,
                pixel_resolution=res,
                is_projected=is_proj
            )
            
            outputs["threshold_used"] = threshold
            outputs["region_count"] = len(regions)
            spatial_artifacts = regions[:10] # Top 10 by size
            
        elif analysis_type != "descriptive_statistics":
            return {"error": "INPUT_INVALID", "message": f"Unknown SAR analysis type: {analysis_type}"}

        # Visualization Artifact
        artifact_id = f"sar_{int(start_time)}_{band_idx}"
        rgb_path = os.path.join(self.artifact_dir, f"{artifact_id}_viz.png")
        
        try:
            # Generate safe dB/percentile-clipped visual representation
            img = self.sar_converter.to_visualization(
                data, to_db=to_db, clip_percentiles=(2, 98), nodata=nodata
            )
            img.save(rgb_path)
            provenance.append(f"Generated SAR visualization (to_db={to_db}, clip=2-98%).")
        except Exception as e:
            return {"error": "EXECUTION_FAILED", "message": f"Visualization failed: {str(e)}"}

        return {
            "success": True,
            "outputs": outputs,
            "metrics": metrics,
            "spatial_artifacts": spatial_artifacts,
            "visual_artifacts": [rgb_path],
            "provenance": provenance
        }
