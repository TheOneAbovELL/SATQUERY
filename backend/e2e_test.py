import requests
import os
import sys
from rasterio.transform import from_origin

sys.stdout.reconfigure(encoding='utf-8')

# Create mock georeferenced images
os.makedirs('mock_data', exist_ok=True)
import numpy as np
import rasterio

transform = from_origin(10.0, 50.0, 10.0, 10.0) # West, North, xsize, ysize
crs = 'EPSG:4326'

data_opt = np.random.randint(0, 255, (3, 100, 100), dtype=np.uint8)
with rasterio.open('mock_data/t1_opt_geo.tif', 'w', driver='GTiff', width=100, height=100, count=3, dtype=data_opt.dtype, transform=transform, crs=crs) as dst:
    dst.write(data_opt)
    dst.update_tags(1, semantics='RED')
    dst.update_tags(2, semantics='GREEN')
    dst.update_tags(3, semantics='BLUE')

data_sar = np.random.randint(0, 255, (1, 100, 100), dtype=np.uint8)
with rasterio.open('mock_data/t1_sar_geo.tif', 'w', driver='GTiff', width=100, height=100, count=1, dtype=data_sar.dtype, transform=transform, crs=crs) as dst:
    dst.write(data_sar)

def upload_file(path, role=None):
    with open(path, 'rb') as f:
        files = {'file': (os.path.basename(path), f, 'image/tiff')}
        data = {'role': role} if role else {}
        resp = requests.post('http://127.0.0.1:8000/api/v1/upload', files=files, data=data)
        return resp.json()

def analyze(query, asset_ids):
    resp = requests.post('http://127.0.0.1:8000/api/v1/analyze', json={
        "query": query,
        "asset_ids": asset_ids
    })
    return resp.json()

opt_asset = upload_file('mock_data/t1_opt_geo.tif')
sar_asset = upload_file('mock_data/t1_sar_geo.tif')

print("\n--- FLOW B: Bi-temporal (using two opticals here) ---")
res_b = analyze('What changed?', [opt_asset['asset_id'], opt_asset['asset_id']])
print(f"Status: {res_b.get('status')}")
print(f"Metrics: {res_b.get('metrics')}")

print("\n--- FLOW C: Cross-modal (Opt + SAR) ---")
res_c = analyze('Compare optical and SAR', [opt_asset['asset_id'], sar_asset['asset_id']])
print(f"Status: {res_c.get('status')}")
print(f"Metrics: {res_c.get('metrics')}")
