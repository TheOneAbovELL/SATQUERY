"""
Raster alignment and preprocessing for bi-temporal analysis.
Handles CRS reprojection, grid alignment, overlap extraction, and RGB conversion.
"""
import numpy as np
import rasterio
from rasterio.warp import reproject, calculate_default_transform, Resampling
from rasterio.windows import from_bounds
from typing import Dict, Any, Tuple, Optional
from PIL import Image


class RasterAligner:
    """
    Aligns two rasters onto a common grid for pixel-level comparison.
    Handles CRS differences, resolution differences, and partial overlap.
    """

    def align_rasters(self, t1_path: str, t2_path: str,
                      band_indices: list = None,
                      resampling: Resampling = Resampling.bilinear) -> Dict[str, Any]:
        """
        Reads and aligns two rasters to T1's grid within their overlap region.
        
        Returns dict with:
            t1_data: np.ndarray (bands, rows, cols)
            t2_data: np.ndarray (bands, rows, cols) — aligned to T1's grid
            valid_mask: np.ndarray (rows, cols) — True where both have valid data
            overlap_transform: Affine — transform of the overlap window
            overlap_bounds: tuple — (left, bottom, right, top)
            target_crs: str
            nodata_t1: float or None
            nodata_t2: float or None
            provenance: dict — full processing metadata
        """
        with rasterio.open(t1_path) as src1, rasterio.open(t2_path) as src2:
            # Determine bands to read
            if band_indices is None:
                max_bands = min(src1.count, src2.count)
                band_indices = list(range(1, max_bands + 1))

            target_crs = src1.crs
            nodata1 = src1.nodata
            nodata2 = src2.nodata

            # Get bounds in T1's CRS
            if src1.crs != src2.crs:
                t2_bounds = rasterio.warp.transform_bounds(
                    src2.crs, src1.crs,
                    src2.bounds.left, src2.bounds.bottom,
                    src2.bounds.right, src2.bounds.top
                )
            else:
                t2_bounds = (src2.bounds.left, src2.bounds.bottom,
                             src2.bounds.right, src2.bounds.top)

            t1_bounds = (src1.bounds.left, src1.bounds.bottom,
                         src1.bounds.right, src1.bounds.top)

            # Compute intersection
            overlap_left = max(t1_bounds[0], t2_bounds[0])
            overlap_bottom = max(t1_bounds[1], t2_bounds[1])
            overlap_right = min(t1_bounds[2], t2_bounds[2])
            overlap_top = min(t1_bounds[3], t2_bounds[3])

            if overlap_left >= overlap_right or overlap_bottom >= overlap_top:
                return {"error": "no_spatial_overlap"}

            overlap_bounds = (overlap_left, overlap_bottom, overlap_right, overlap_top)

            # Read T1 within overlap window
            t1_window = from_bounds(*overlap_bounds, src1.transform)
            # Ensure integer pixel boundaries
            t1_window = t1_window.round_offsets().round_lengths()
            
            if t1_window.width < 1 or t1_window.height < 1:
                return {"error": "no_spatial_overlap"}

            t1_data = src1.read(band_indices, window=t1_window)
            overlap_transform = rasterio.windows.transform(t1_window, src1.transform)

            # Read T2 — reproject onto T1's grid if needed
            t2_data = np.empty_like(t1_data)
            
            needs_reprojection = (src1.crs != src2.crs or
                                  src1.res != src2.res or
                                  src1.transform != src2.transform)

            if needs_reprojection:
                for i, band_idx in enumerate(band_indices):
                    reproject(
                        source=rasterio.band(src2, band_idx),
                        destination=t2_data[i],
                        src_transform=src2.transform,
                        src_crs=src2.crs,
                        dst_transform=overlap_transform,
                        dst_crs=target_crs,
                        dst_nodata=nodata2,
                        resampling=resampling
                    )
            else:
                t2_window = from_bounds(*overlap_bounds, src2.transform)
                t2_window = t2_window.round_offsets().round_lengths()
                # Ensure dimensions match after rounding
                t2_read = src2.read(band_indices, window=t2_window)
                min_h = min(t1_data.shape[1], t2_read.shape[1])
                min_w = min(t1_data.shape[2], t2_read.shape[2])
                t1_data = t1_data[:, :min_h, :min_w]
                t2_data = np.empty_like(t1_data)
                t2_data[:] = t2_read[:, :min_h, :min_w]

            # Build combined valid mask
            valid_mask = np.ones((t1_data.shape[1], t1_data.shape[2]), dtype=bool)
            for i in range(t1_data.shape[0]):
                if nodata1 is not None:
                    valid_mask &= (t1_data[i] != nodata1)
                if nodata2 is not None:
                    valid_mask &= (t2_data[i] != nodata2)

            provenance = {
                "t1_path": t1_path,
                "t2_path": t2_path,
                "target_crs": str(target_crs),
                "t1_original_crs": str(src1.crs),
                "t2_original_crs": str(src2.crs),
                "reprojection_applied": needs_reprojection,
                "resampling_method": resampling.name,
                "overlap_bounds": overlap_bounds,
                "overlap_shape": (int(t1_data.shape[1]), int(t1_data.shape[2])),
                "bands_read": band_indices,
                "t1_resolution": src1.res,
                "t2_resolution": src2.res,
            }

            return {
                "t1_data": t1_data,
                "t2_data": t2_data,
                "valid_mask": valid_mask,
                "overlap_transform": overlap_transform,
                "overlap_bounds": overlap_bounds,
                "target_crs": str(target_crs),
                "nodata_t1": nodata1,
                "nodata_t2": nodata2,
                "pixel_resolution": src1.res,
                "is_projected": src1.crs.is_projected if src1.crs else False,
                "provenance": provenance,
            }


class RasterRGBConverter:
    """
    Converts multi-band rasters to RGB PIL images for VLM consumption.
    Clearly marked as RGB REPRESENTATION — not raw multispectral data.
    """

    def to_rgb_image(self, raster_data: np.ndarray, band_semantics: Dict[int, str] = None) -> Image.Image:
        """
        Converts raster array (bands, H, W) to an RGB PIL Image.
        Uses band semantics to select R, G, B channels where available.
        Falls back to first 3 bands or grayscale conversion.
        """
        num_bands = raster_data.shape[0]

        if band_semantics:
            rgb_indices = []
            for color in ["RED", "GREEN", "BLUE"]:
                found = None
                for k, v in band_semantics.items():
                    if v == color:
                        found = k - 1  # 0-indexed
                        break
                if found is not None:
                    rgb_indices.append(found)

            if len(rgb_indices) == 3:
                r = raster_data[rgb_indices[0]]
                g = raster_data[rgb_indices[1]]
                b = raster_data[rgb_indices[2]]
                rgb = np.stack([
                    self._normalize_band(r),
                    self._normalize_band(g),
                    self._normalize_band(b)
                ], axis=-1)
                return Image.fromarray(rgb)

        # Fallback: use first 3 bands or grayscale
        if num_bands >= 3:
            rgb = np.stack([
                self._normalize_band(raster_data[0]),
                self._normalize_band(raster_data[1]),
                self._normalize_band(raster_data[2])
            ], axis=-1)
        else:
            gray = self._normalize_band(raster_data[0])
            rgb = np.stack([gray, gray, gray], axis=-1)

        return Image.fromarray(rgb)

    @staticmethod
    def _normalize_band(band: np.ndarray) -> np.ndarray:
        """Normalizes a single band to 0-255 uint8."""
        b = band.astype(float)
        bmin, bmax = b.min(), b.max()
        if bmax - bmin < 1e-10:
            return np.zeros_like(b, dtype=np.uint8)
        return np.clip((b - bmin) / (bmax - bmin) * 255, 0, 255).astype(np.uint8)


class RasterSARConverter:
    """
    Safely converts SAR raster data (often with extreme dynamic ranges or linear power units)
    to a physically justified 0-255 grayscale PNG suitable for visualization.
    """

    def to_visualization(self, raster_data: np.ndarray, to_db: bool = True, clip_percentiles: tuple = (2, 98), nodata: float = None) -> Image.Image:
        """
        Takes a single band of SAR data.
        Applies optional dB conversion, then clips to percentiles to handle speckle/corner reflectors,
        and scales to 0-255 uint8.
        """
        # Take first band if 3D
        if raster_data.ndim == 3:
            data = raster_data[0]
        else:
            data = raster_data

        data_f = data.astype(float)
        
        # Mask out nodata and <= 0 for dB
        if nodata is not None:
            valid_mask = (data != nodata)
        else:
            valid_mask = np.ones_like(data_f, dtype=bool)

        if to_db:
            # Avoid log(0) or log(negative)
            valid_mask &= (data_f > 0)
            
        if not np.any(valid_mask):
            return Image.fromarray(np.zeros_like(data_f, dtype=np.uint8))

        valid_data = data_f[valid_mask]

        if to_db:
            valid_data = 10 * np.log10(valid_data)
            # Reconstruct array
            data_db = np.zeros_like(data_f)
            data_db[valid_mask] = valid_data
            data_f = data_db

        # Percentile clipping
        vmin, vmax = np.percentile(valid_data, clip_percentiles)
        
        if vmax - vmin < 1e-10:
            scaled = np.zeros_like(data_f, dtype=np.uint8)
        else:
            scaled = np.clip((data_f - vmin) / (vmax - vmin) * 255, 0, 255).astype(np.uint8)
            
        # Ensure invalid pixels are black
        scaled[~valid_mask] = 0

        # Create RGB image (grayscale repeated across channels)
        rgb = np.stack([scaled, scaled, scaled], axis=-1)
        return Image.fromarray(rgb)
