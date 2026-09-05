import requests
import os
import sys
import json
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import rasterio
from rasterio.transform import from_origin

os.makedirs('mock_data', exist_ok=True)

transform = from_origin(10.0, 50.0, 10.0, 10.0)
crs = 'EPSG:4326'

data_opt = np.random.randint(0, 200, (3, 100, 100), dtype=np.uint8)
with rasterio.open('mock_data/t1_opt.tif', 'w', driver='GTiff', width=100, height=100, count=3, dtype=data_opt.dtype, transform=transform, crs=crs) as dst:
    dst.write(data_opt)

data_opt2 = np.random.randint(50, 255, (3, 100, 100), dtype=np.uint8)
with rasterio.open('mock_data/t2_opt.tif', 'w', driver='GTiff', width=100, height=100, count=3, dtype=data_opt2.dtype, transform=transform, crs=crs) as dst:
    dst.write(data_opt2)

data_sar = np.random.randint(0, 255, (1, 100, 100), dtype=np.uint8)
with rasterio.open('mock_data/t1_sar.tif', 'w', driver='GTiff', width=100, height=100, count=1, dtype=data_sar.dtype, transform=transform, crs=crs) as dst:
    dst.write(data_sar)

RESULTS = {}

def upload(path, role=None):
    with open(path, 'rb') as f:
        resp = requests.post('http://127.0.0.1:8000/api/v1/upload',
            files={'file': (os.path.basename(path), f, 'image/tiff')},
            data={'role': role or ''})
    d = resp.json()
    return d

def analyze(query, asset_ids):
    resp = requests.post('http://127.0.0.1:8000/api/v1/analyze',
        json={"query": query, "asset_ids": asset_ids})
    return resp.json()

print("=" * 60)
print("HEALTH CHECK")
print("=" * 60)
h = requests.get('http://127.0.0.1:8000/health').json()
print(json.dumps(h, indent=2))
RESULTS['health'] = h

print()
print("=" * 60)
print("UPLOAD PHASE")
print("=" * 60)
opt1 = upload('mock_data/t1_opt.tif', 'T1')
opt2 = upload('mock_data/t2_opt.tif', 'T2')
sar1 = upload('mock_data/t1_sar.tif', 'SAR')
print(f"opt1: {opt1.get('asset_id')}, modality={opt1.get('modality')}")
print(f"opt2: {opt2.get('asset_id')}, modality={opt2.get('modality')}")
print(f"sar1: {sar1.get('asset_id')}, modality={sar1.get('modality')}")

print()
print("=" * 60)
print("FLOW A: Single Optical Image - VLM Query")
print("=" * 60)
ra = analyze('What does this satellite image show?', [opt1['asset_id']])
print(f"  Task:    {ra.get('task')}")
print(f"  Status:  {ra.get('status')}")
print(f"  Summary: {ra.get('summary')}")
print(f"  Trace steps: {len(ra.get('execution_trace', []))}")
RESULTS['flow_a'] = ra

print()
print("=" * 60)
print("FLOW B: Bi-temporal Change Detection")
print("=" * 60)
rb = analyze('What changed between these two images?', [opt1['asset_id'], opt2['asset_id']])
print(f"  Task:    {rb.get('task')}")
print(f"  Status:  {rb.get('status')}")
print(f"  Summary: {rb.get('summary')}")
m = rb.get('metrics', {})
print(f"  Metrics: change_fraction={m.get('change_fraction')}, changed_pixel_count={m.get('changed_pixel_count')}")
print(f"  Trace steps: {len(rb.get('execution_trace', []))}")
RESULTS['flow_b'] = rb

print()
print("=" * 60)
print("FLOW C: Optical + SAR Cross-Modal")
print("=" * 60)
rc = analyze('Compare optical and SAR observations.', [opt1['asset_id'], sar1['asset_id']])
print(f"  Task:    {rc.get('task')}")
print(f"  Status:  {rc.get('status')}")
print(f"  Summary: {rc.get('summary')}")
m = rc.get('metrics', {})
print(f"  Metrics: iou={m.get('iou')}")
print(f"  Trace steps: {len(rc.get('execution_trace', []))}")
RESULTS['flow_c'] = rc

print()
print("=" * 60)
print("FLOW D: Invalid Input (missing asset_id)")
print("=" * 60)
rd_resp = requests.post('http://127.0.0.1:8000/api/v1/analyze',
    json={"query": "What is this?", "asset_ids": ["nonexistent-id"]})
print(f"  HTTP status: {rd_resp.status_code}")
print(f"  Detail: {rd_resp.json().get('detail')}")
RESULTS['flow_d'] = {'status_code': rd_resp.status_code, 'detail': rd_resp.json().get('detail')}

print()
print("=" * 60)
print("ADAPTER AUDIT")
print("=" * 60)
import json
adapter_path = '../models/rs_lora_adapter/adapter_config.json'
if os.path.exists(adapter_path):
    with open(adapter_path) as f:
        cfg = json.load(f)
    print(f"  r={cfg.get('r')}, lora_alpha={cfg.get('lora_alpha')}")
    print(f"  target_modules={cfg.get('target_modules')}")
    print(f"  peft_type={cfg.get('peft_type')}")
else:
    print("  Adapter not found at expected path")

print()
print("=" * 60)
print("FINAL STATUS SUMMARY")
print("=" * 60)
def classify(r, flow_name):
    st = r.get('status', 'FAILED')
    if st in ('SUCCESS', 'PARTIAL_FAILURE') and r.get('task'):
        if r.get('execution_trace'):
            label = 'STRUCTURAL PASS'
            if st == 'SUCCESS' and r.get('metrics'):
                label = 'REAL PASS'
        else:
            label = 'SYNTHETIC PASS'
    else:
        label = 'FAILED'
    print(f"  {flow_name}: {label} (status={st})")

classify(RESULTS['flow_a'], 'Flow A')
classify(RESULTS['flow_b'], 'Flow B')
classify(RESULTS['flow_c'], 'Flow C')
d_pass = RESULTS['flow_d']['status_code'] == 422
print(f"  Flow D: {'REAL PASS' if d_pass else 'FAILED'} (HTTP {RESULTS['flow_d']['status_code']})")
