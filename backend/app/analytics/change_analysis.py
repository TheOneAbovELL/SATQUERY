import os
import time
import numpy as np
import rasterio
from typing import Dict, Any, List
from datetime import datetime
from PIL import Image

from app.domain.models import ImageAsset
from app.services.relationship_engine import ImageRelationshipEngine, RelationshipType, AlignmentStatus
from app.analytics.deterministic import DeterministicAnalyticsEngine
from app.analytics.preprocessing import RasterAligner, RasterRGBConverter


class BiTemporalChangeAnalyzer:
    """
    Orchestrates the bi-temporal change analysis pipeline.
    Validates temporal/spatial compatibility, aligns grids, computes deterministic change,
    extracts statistics/regions, and generates visual artifacts.
    """
    def __init__(self, artifact_dir: str = "./artifacts"):
        self.relationship_engine = ImageRelationshipEngine()
        self.analytics_engine = DeterministicAnalyticsEngine()
        self.aligner = RasterAligner()
        self.rgb_converter = RasterRGBConverter()
        self.artifact_dir = artifact_dir
        os.makedirs(self.artifact_dir, exist_ok=True)

    def analyze(self, t1_asset: ImageAsset, t2_asset: ImageAsset,
                analysis_type: str = "pixel_diff",
                threshold: float = 0.1,
                min_region_size: int = 25,
                bands: List[int] = None) -> Dict[str, Any]:
        """
        Executes the full bi-temporal change pipeline.
        Returns a dict structured for ToolResult fields.
        """
        start_time = time.time()
        provenance = []

        # 1. Temporal Validation
        t1_time = t1_asset.acquisition_time
        t2_time = t2_asset.acquisition_time
        if t1_time and t2_time and t1_time > t2_time:
            # Swap to ensure T1 is earlier
            t1_asset, t2_asset = t2_asset, t1_asset
            t1_time, t2_time = t2_time, t1_time
            provenance.append("Swapped T1 and T2 to ensure chronological order.")
        
        if not t1_time or not t2_time:
            provenance.append("temporal_metadata_unavailable: Unable to verify chronological ordering.")

        # 2. Spatial Compatibility
        assessment = self.relationship_engine.assess([t1_asset, t2_asset])
        if assessment.alignment_status == AlignmentStatus.INCOMPATIBLE:
            return {"error": "NO_SPATIAL_OVERLAP", "message": "Assets are spatially incompatible or have no overlap."}
        if RelationshipType.NON_OVERLAPPING in assessment.relationship_types:
            return {"error": "NO_SPATIAL_OVERLAP", "message": "Assets do not overlap spatially."}
        
        provenance.append(f"Spatial assessment complete: {assessment.alignment_status.name}")

        # 3. Co-registration & Overlap Extraction
        align_result = self.aligner.align_rasters(
            t1_asset.storage_location,
            t2_asset.storage_location,
            band_indices=bands
        )
        if "error" in align_result:
            return {"error": "NO_SPATIAL_OVERLAP", "message": "Failed to extract valid spatial overlap."}

        provenance.append(f"Alignment provenance: {str(align_result['provenance'])}")

        t1_data = align_result["t1_data"]
        t2_data = align_result["t2_data"]
        valid_mask = align_result["valid_mask"]
        
        if not np.any(valid_mask):
            return {"error": "INSUFFICIENT_VALID_DATA", "message": "No overlapping valid pixels found (all nodata)."}

        # 4. Change Computation
        # Default to first band if not specified (for simplified difference)
        band_idx = 0 
        
        if analysis_type == "pixel_diff":
            diff_res = self.analytics_engine.compute_pixel_difference(
                t1_data[band_idx], t2_data[band_idx], align_result["nodata_t1"]
            )
            diff_array = diff_res["absolute_difference"]
            provenance.append(f"Method: Absolute Pixel Difference on band index {bands[0] if bands else 1}")

        elif analysis_type == "normalized":
            diff_array = self.analytics_engine.compute_normalized_change(
                t1_data[band_idx], t2_data[band_idx], nodata=align_result["nodata_t1"]
            )
            provenance.append(f"Method: Normalized Change on band index {bands[0] if bands else 1}")
            
        elif analysis_type == "delta_ndvi":
            # Requires RED and NIR bands.
            try:
                red_idx = next(k-1 for k, v in t1_asset.band_semantics.items() if v == "RED")
                nir_idx = next(k-1 for k, v in t1_asset.band_semantics.items() if v == "NIR")
            except StopIteration:
                return {"error": "CAPABILITY_UNAVAILABLE", "message": "RED and NIR bands required for NDVI."}
            
            # Need to re-read or use existing if all bands were loaded
            # Assuming all bands were loaded if bands is None
            if len(t1_data) <= max(red_idx, nir_idx):
                return {"error": "CAPABILITY_UNAVAILABLE", "message": "Data array lacks required bands for NDVI."}
                
            ndvi_t1 = self.analytics_engine.calculate_ndvi(t1_data[nir_idx], t1_data[red_idx], align_result["nodata_t1"])
            ndvi_t2 = self.analytics_engine.calculate_ndvi(t2_data[nir_idx], t2_data[red_idx], align_result["nodata_t2"])
            
            diff_array = self.analytics_engine.compute_delta_index(ndvi_t1, ndvi_t2)
            provenance.append("Method: Delta NDVI (T2 - T1)")
            
        else:
            return {"error": "INPUT_INVALID", "message": f"Unknown analysis type: {analysis_type}"}

        # Combine valid masks
        if hasattr(diff_array, 'mask') and diff_array.mask is not np.bool_(False):
            final_valid_mask = valid_mask & (~diff_array.mask)
        else:
            final_valid_mask = valid_mask

        # 5. Change Mask & Statistics
        change_mask = self.analytics_engine.compute_change_mask(diff_array, threshold)
        # ensure we only count valid pixels
        change_mask = change_mask & final_valid_mask
        
        stats = self.analytics_engine.compute_change_statistics(
            change_mask, final_valid_mask, diff_array,
            pixel_resolution=align_result["pixel_resolution"],
            is_projected=align_result["is_projected"],
            threshold=threshold
        )
        
        # Move non-float values to outputs to satisfy Dict[str, float] for metrics
        area_units = stats.pop("area_units", "unavailable")
        changed_area = stats.pop("changed_area", None)
        total_analyzed_area = stats.pop("total_analyzed_area", None)
        
        if changed_area is not None:
            stats["changed_area"] = changed_area
        if total_analyzed_area is not None:
            stats["total_analyzed_area"] = total_analyzed_area

        # 6. Change Regions
        regions = self.analytics_engine.extract_change_regions(
            change_mask, diff_array, min_region_size=min_region_size,
            pixel_resolution=align_result["pixel_resolution"],
            is_projected=align_result["is_projected"]
        )

        # 7. Artifact Generation
        artifact_id = f"change_{int(start_time)}"
        mask_path = os.path.join(self.artifact_dir, f"{artifact_id}_mask.tif")
        rgb_t1_path = os.path.join(self.artifact_dir, f"{artifact_id}_t1.png")
        rgb_t2_path = os.path.join(self.artifact_dir, f"{artifact_id}_t2.png")
        
        # Save change mask GeoTIFF
        with rasterio.open(
            mask_path, 'w', driver='GTiff',
            height=change_mask.shape[0], width=change_mask.shape[1],
            count=1, dtype=rasterio.uint8,
            crs=align_result["target_crs"],
            transform=align_result["overlap_transform"]
        ) as dst:
            dst.write((change_mask.astype(np.uint8) * 255), 1)

        # Generate RGB representations for VLM/UI
        try:
            t1_rgb = self.rgb_converter.to_rgb_image(t1_data, t1_asset.band_semantics)
            t2_rgb = self.rgb_converter.to_rgb_image(t2_data, t2_asset.band_semantics)
            t1_rgb.save(rgb_t1_path)
            t2_rgb.save(rgb_t2_path)
            visual_artifacts = [mask_path, rgb_t1_path, rgb_t2_path]
            provenance.append("Generated RGB visualization artifacts for T1 and T2.")
        except Exception as e:
            visual_artifacts = [mask_path]
            provenance.append(f"Failed to generate RGB artifacts: {str(e)}")

        # Construct structured response
        return {
            "success": True,
            "outputs": {
                "change_fraction": stats.get("change_fraction", 0.0),
                "changed_pixel_count": stats.get("changed_pixel_count", 0),
                "region_count": len(regions),
                "threshold": threshold,
                "analysis_type": analysis_type,
                "area_units": area_units
            },
            "metrics": stats,
            "spatial_artifacts": regions[:10], # Limit to top 10 regions to avoid payload bloat
            "visual_artifacts": visual_artifacts,
            "provenance": provenance
        }
