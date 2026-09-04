import numpy as np
import rasterio
from typing import Dict, Any, Tuple

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
