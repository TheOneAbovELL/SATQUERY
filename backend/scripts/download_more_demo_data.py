import os
import requests
import math
import rasterio
from rasterio.transform import from_bounds
import numpy as np
from PIL import Image
import io

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile

def fetch_area(name, lat, lon, zoom, width_tiles, height_tiles, out_dir):
    filename = os.path.join(out_dir, f"{name}.tif")
    print(f"Generating {name} ({width_tiles*256}x{height_tiles*256} pixels)...")
    
    x_center, y_center = deg2num(lat, lon, zoom)
    
    x_start = x_center - width_tiles // 2
    y_start = y_center - height_tiles // 2
    
    img_width = width_tiles * 256
    img_height = height_tiles * 256
    
    out_img = np.zeros((3, img_height, img_width), dtype=np.uint8)
    
    for i in range(width_tiles):
        for j in range(height_tiles):
            x = x_start + i
            y = y_start + j
            url = f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y}/{x}'
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    tile = Image.open(io.BytesIO(resp.content)).convert('RGB')
                    tile_np = np.array(tile).transpose(2, 0, 1) # to CHW
                    out_img[:, j*256:(j+1)*256, i*256:(i+1)*256] = tile_np
            except Exception as e:
                print('  [!] Error fetching a tile, skipping part of image.')

    # Spherical Mercator EPSG:3857 projection bounds
    def tile_to_mercator(tx, ty, tz):
        n = 2.0 ** tz
        lon_deg = tx / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ty / n)))
        lat_deg = math.degrees(lat_rad)
        x_m = lon_deg * 20037508.34 / 180
        y_m = math.log(math.tan((90 + lat_deg) * math.pi / 360)) / (math.pi / 180)
        y_m = y_m * 20037508.34 / 180
        return x_m, y_m
        
    w, n_bound = tile_to_mercator(x_start, y_start, zoom)
    e, s_bound = tile_to_mercator(x_start + width_tiles, y_start + height_tiles, zoom)
    
    transform = from_bounds(w, s_bound, e, n_bound, img_width, img_height)
    
    with rasterio.open(
        filename, 'w', driver='GTiff', width=img_width, height=img_height, count=3,
        dtype=out_img.dtype, crs='EPSG:3857', transform=transform
    ) as dst:
        dst.write(out_img)
        dst.update_tags(SENSOR='ESRI_WORLD_IMAGERY')
        dst.set_band_description(1, 'Red')
        dst.set_band_description(2, 'Green')
        dst.set_band_description(3, 'Blue')
        
    print(f"  -> Saved to {filename}\n")

if __name__ == "__main__":
    out_dir = os.path.join("mock_data", "real_samples")
    os.makedirs(out_dir, exist_ok=True)
    
    print("Downloading high-quality demo GeoTIFFs...\n")
    
    # 1. City View (Mumbai, India)
    fetch_area("mumbai_city_view", 19.0760, 72.8777, 15, 3, 3, out_dir)
    
    # 2. Water / Coastal View (Venice, Italy)
    fetch_area("venice_water_view", 45.4408, 12.3155, 15, 3, 3, out_dir)
    
    # 3. Terrain / Mountains View (Grand Canyon, USA)
    fetch_area("grand_canyon_terrain", 36.1069, -112.1129, 14, 3, 3, out_dir)
    
    print("All additional demo data has been generated successfully!")
