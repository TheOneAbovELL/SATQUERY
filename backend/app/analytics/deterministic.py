import numpy as np
import rasterio
from typing import Dict, Any, Tuple, List
from scipy import ndimage

class DeterministicAnalyticsEngine:
    def calculate_ndvi(self, nir_band: np.ndarray, red_band: np.ndarray, nodata: float = None) -> np.ma.MaskedArray:
        """
        Calculates NDVI using safe masked arrays to properly exclude nodata values.
        """
        nir = np.ma.masked_equal(nir_band, nodata) if nodata is not None else np.ma.array(nir_band)
        red = np.ma.masked_equal(red_band, nodata) if nodata is not None else np.ma.array(red_band)
        
        nir_f = nir.astype(float)
        red_f = red.astype(float)
        
        denominator = nir_f + red_f
        # Mask where denominator is 0
        denominator = np.ma.masked_where(denominator == 0, denominator)
        
        ndvi = (nir_f - red_f) / denominator
        return ndvi
        
    def calculate_mask_area(self, mask: np.ndarray, pixel_resolution: Tuple[float, float], is_projected: bool) -> Dict[str, Any]:
        """
        Calculates physical area from a binary mask.
        Strictly requires a projected CRS to return valid metric area.
        """
        pixel_count = int(np.sum(mask))
        
        if not is_projected:
            return {
                "valid": False,
                "pixel_count": pixel_count,
                "error": "Cannot calculate physical area directly from geographic coordinates (degrees). Reprojection required."
            }
            
        pixel_area = abs(pixel_resolution[0] * pixel_resolution[1])
        total_area = pixel_count * pixel_area
        
        return {
            "valid": True,
            "pixel_count": pixel_count,
            "pixel_area": pixel_area,
            "total_area": float(total_area),
            "units": "square units of CRS (typically sq meters)"
        }

    # ---- Bi-temporal change analysis methods ----

    def compute_pixel_difference(self, t1_band: np.ndarray, t2_band: np.ndarray,
                                  nodata: float = None) -> Dict[str, np.ma.MaskedArray]:
        """
        Computes signed and absolute pixel-level difference between two co-registered bands.
        Returns masked arrays where nodata pixels from either epoch are excluded.
        """
        t1 = np.ma.masked_equal(t1_band, nodata) if nodata is not None else np.ma.array(t1_band)
        t2 = np.ma.masked_equal(t2_band, nodata) if nodata is not None else np.ma.array(t2_band)
        
        t1_f = t1.astype(float)
        t2_f = t2.astype(float)
        
        # Combined mask: invalid if EITHER epoch is masked
        combined_mask = t1_f.mask | t2_f.mask
        
        signed_diff = np.ma.array(t2_f - t1_f, mask=combined_mask)
        absolute_diff = np.ma.array(np.abs(t2_f - t1_f), mask=combined_mask)
        
        return {
            "signed_difference": signed_diff,
            "absolute_difference": absolute_diff,
            "valid_mask": ~combined_mask
        }

    def compute_normalized_change(self, t1_band: np.ndarray, t2_band: np.ndarray,
                                   epsilon: float = 1e-7, nodata: float = None) -> np.ma.MaskedArray:
        """
        Computes normalized change: (T2 - T1) / (|T1| + epsilon).
        Epsilon prevents division by zero for dark/zero-value pixels.
        """
        t1 = np.ma.masked_equal(t1_band, nodata) if nodata is not None else np.ma.array(t1_band)
        t2 = np.ma.masked_equal(t2_band, nodata) if nodata is not None else np.ma.array(t2_band)
        
        t1_f = t1.astype(float)
        t2_f = t2.astype(float)
        
        combined_mask = t1_f.mask | t2_f.mask
        denominator = np.abs(t1_f) + epsilon
        
        result = np.ma.array((t2_f - t1_f) / denominator, mask=combined_mask)
        return result

    def compute_change_mask(self, diff_array: np.ma.MaskedArray, threshold: float) -> np.ndarray:
        """
        Creates a binary change mask where |difference| exceeds the threshold.
        Returns a plain boolean ndarray (masked pixels = False = no change).
        """
        abs_vals = np.abs(diff_array.filled(0))
        mask = abs_vals > threshold
        # Exclude masked (invalid) pixels — they are NOT changes
        if hasattr(diff_array, 'mask') and diff_array.mask is not np.bool_(False):
            mask = mask & (~diff_array.mask)
        return mask

    def compute_change_statistics(self, change_mask: np.ndarray, valid_mask: np.ndarray,
                                   diff_array: np.ma.MaskedArray,
                                   pixel_resolution: Tuple[float, float] = None,
                                   is_projected: bool = False,
                                   threshold: float = 0.0) -> Dict[str, Any]:
        """
        Computes quantitative change statistics from a change mask and difference array.
        Physical area is only reported when CRS supports it.
        """
        valid_count = int(np.sum(valid_mask))
        changed_count = int(np.sum(change_mask))
        unchanged_count = valid_count - changed_count
        
        change_fraction = float(changed_count / valid_count) if valid_count > 0 else 0.0
        
        # Statistics over valid changed pixels only
        changed_values = diff_array[change_mask]
        
        stats = {
            "valid_pixel_count": valid_count,
            "changed_pixel_count": changed_count,
            "unchanged_pixel_count": unchanged_count,
            "change_fraction": round(change_fraction, 6),
            "threshold_used": threshold,
        }
        
        if changed_count > 0 and len(changed_values) > 0:
            stats["mean_change"] = float(np.mean(changed_values))
            stats["min_change"] = float(np.min(changed_values))
            stats["max_change"] = float(np.max(changed_values))
        else:
            stats["mean_change"] = 0.0
            stats["min_change"] = 0.0
            stats["max_change"] = 0.0
        
        # Physical area only if projected CRS
        if pixel_resolution and is_projected:
            pixel_area = abs(pixel_resolution[0] * pixel_resolution[1])
            stats["changed_area"] = float(changed_count * pixel_area)
            stats["total_analyzed_area"] = float(valid_count * pixel_area)
            stats["area_units"] = "square units of CRS (typically sq meters)"
        else:
            stats["changed_area"] = None
            stats["total_analyzed_area"] = None
            stats["area_units"] = "unavailable (geographic CRS or no resolution)"
        
        return stats

    def compute_delta_index(self, t1_index: np.ma.MaskedArray,
                             t2_index: np.ma.MaskedArray) -> np.ma.MaskedArray:
        """
        Computes temporal difference of any spectral index (e.g. NDVI_T2 - NDVI_T1).
        Both inputs must already be computed spectral indices as masked arrays.
        """
        combined_mask = t1_index.mask | t2_index.mask
        delta = np.ma.array(t2_index - t1_index, mask=combined_mask)
        return delta

    def extract_change_regions(self, change_mask: np.ndarray, diff_array: np.ma.MaskedArray,
                                min_region_size: int = 25,
                                pixel_resolution: Tuple[float, float] = None,
                                is_projected: bool = False) -> List[Dict[str, Any]]:
        """
        Finds connected change regions and computes per-region statistics.
        Filters out regions smaller than min_region_size pixels.
        """
        labeled_array, num_features = ndimage.label(change_mask.astype(int))
        
        regions = []
        for region_id in range(1, num_features + 1):
            region_mask = labeled_array == region_id
            pixel_count = int(np.sum(region_mask))
            
            if pixel_count < min_region_size:
                continue
            
            # Bounding box in pixel coordinates
            rows, cols = np.where(region_mask)
            bbox = {
                "row_min": int(rows.min()),
                "row_max": int(rows.max()),
                "col_min": int(cols.min()),
                "col_max": int(cols.max())
            }
            
            centroid = {
                "row": float(rows.mean()),
                "col": float(cols.mean())
            }
            
            region_values = diff_array[region_mask]
            mean_magnitude = float(np.mean(np.abs(region_values))) if len(region_values) > 0 else 0.0
            
            region_info = {
                "region_id": region_id,
                "pixel_count": pixel_count,
                "bbox": bbox,
                "centroid": centroid,
                "mean_magnitude": round(mean_magnitude, 6),
            }
            
            if pixel_resolution and is_projected:
                pixel_area = abs(pixel_resolution[0] * pixel_resolution[1])
                region_info["area"] = float(pixel_count * pixel_area)
                region_info["area_units"] = "square units of CRS"
            else:
                region_info["area"] = None
                region_info["area_units"] = "unavailable"
            
            regions.append(region_info)
        
        regions.sort(key=lambda r: r["pixel_count"], reverse=True)
        return regions

    # ---- SAR analysis methods ----

    def compute_sar_statistics(self, band: np.ndarray, nodata: float = None) -> Dict[str, Any]:
        """
        Computes robust descriptive statistics for SAR data, ignoring nodata.
        """
        data = np.ma.masked_equal(band, nodata) if nodata is not None else np.ma.array(band)
        
        valid_count = int(data.count())
        if valid_count == 0:
            return {
                "valid_pixel_count": 0,
                "mean": 0.0,
                "median": 0.0,
                "std_dev": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p99": 0.0
            }

        valid_data = data.compressed().astype(float)
        
        return {
            "valid_pixel_count": valid_count,
            "mean": float(np.mean(valid_data)),
            "median": float(np.median(valid_data)),
            "std_dev": float(np.std(valid_data)),
            "min": float(np.min(valid_data)),
            "max": float(np.max(valid_data)),
            "p99": float(np.percentile(valid_data, 99))
        }

    def extract_backscatter_regions(self, band: np.ndarray, threshold: float, 
                                    direction: str = "above", min_region_size: int = 25,
                                    nodata: float = None,
                                    pixel_resolution: Tuple[float, float] = None,
                                    is_projected: bool = False) -> List[Dict[str, Any]]:
        """
        Identifies spatial regions where backscatter is above (or below) a threshold.
        Reuses the connected-components region extraction logic.
        """
        data = np.ma.masked_equal(band, nodata) if nodata is not None else np.ma.array(band)
        
        if direction == "above":
            mask = data > threshold
        else:
            mask = data < threshold
            
        # Exclude masked invalid pixels
        mask = mask & (~data.mask)
        
        # We can reuse extract_change_regions but pass the raw data as the diff_array
        # so that it calculates the mean backscatter for each region.
        return self.extract_change_regions(
            change_mask=mask, diff_array=data,
            min_region_size=min_region_size,
            pixel_resolution=pixel_resolution,
            is_projected=is_projected
        )

