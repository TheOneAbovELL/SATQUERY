import rasterio
import os
from typing import Dict, Any
from app.domain.models import AssetFormat, AssetModality

class InputValidator:
    def validate(self, filepath: str) -> Dict[str, Any]:
        result = {
            "valid": False,
            "format": AssetFormat.UNKNOWN,
            "modality": AssetModality.UNKNOWN,
            "band_count": 0,
            "crs": None,
            "transform": None,
            "resolution": None,
            "geospatial_bounds": None,
            "band_semantics": {},
            "capabilities": {
                "can_vqa": True,
                "can_caption": True,
                "can_ground": True,
                "can_segmentation": True,
                "can_ndvi": False,
                "can_area_measurement": False,
                "can_change_analysis": False
            },
            "warnings": [],
            "errors": []
        }
        
        if not os.path.exists(filepath):
            result["errors"].append("File not found.")
            return result

        try:
            with rasterio.open(filepath) as src:
                result["valid"] = True
                result["band_count"] = src.count
                result["dimensions"] = (src.width, src.height)
                
                driver = src.driver
                if driver in ["GTiff", "COG", "VRT"]:
                    result["format"] = AssetFormat.GEOTIFF
                elif driver == "PNG":
                    result["format"] = AssetFormat.PNG
                elif driver == "JPEG":
                    result["format"] = AssetFormat.JPEG
                
                if src.crs:
                    result["crs"] = src.crs.to_string()
                    result["transform"] = list(src.transform)[:6]
                    result["resolution"] = (abs(src.transform.a), abs(src.transform.e))
                    b = src.bounds
                    result["geospatial_bounds"] = {"min_x": b.left, "min_y": b.bottom, "max_x": b.right, "max_y": b.top}
                    if src.crs.is_projected:
                        result["capabilities"]["can_area_measurement"] = True
                    else:
                        result["warnings"].append("CRS is geographic; direct physical area measurements disabled.")
                else:
                    result["warnings"].append("No CRS found. Geospatial capabilities disabled.")
                
                semantics = {}
                for i in range(1, src.count + 1):
                    ci = src.colorinterp[i-1].name.upper()
                    if ci not in ["UNDEFINED", "UNSUPPORTED"]:
                        semantics[i] = ci
                
                if src.count == 1:
                    result["modality"] = AssetModality.GRAYSCALE
                    if not semantics: semantics[1] = "GRAY"
                elif src.count == 3:
                    result["modality"] = AssetModality.RGB
                    if not semantics: semantics = {1: "RED", 2: "GREEN", 3: "BLUE"}
                elif src.count >= 4:
                    result["modality"] = AssetModality.MULTISPECTRAL
                    if not semantics:
                        semantics = {1: "BLUE", 2: "GREEN", 3: "RED", 4: "NIR"}
                        result["warnings"].append("Inferred 4-band semantics (B, G, R, NIR) as defaults. Verify sensor.")
                
                result["band_semantics"] = semantics
                
                sem_values = list(semantics.values())
                if "RED" in sem_values and "NIR" in sem_values:
                    result["capabilities"]["can_ndvi"] = True

        except rasterio.errors.RasterioIOError:
            result["errors"].append("Corrupted or unreadable raster file.")
        except Exception as e:
            result["errors"].append(f"Validation exception: {str(e)}")
            
        return result
