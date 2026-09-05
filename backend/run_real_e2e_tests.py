import requests
import os
import sys
import json
sys.stdout.reconfigure(encoding='utf-8')

# Ensure we use the real dataset
DATA_DIR = os.path.join('mock_data', 'real_samples')
OPTICAL_PATH = os.path.join(DATA_DIR, 'landsat7_rgb_sample.tif')
OPTICAL_T2_PATH = os.path.join(DATA_DIR, 'landsat7_rgb_t2_simulated.tif')
SAR_PATH = os.path.join(DATA_DIR, 'simulated_sar_sample.tif')

if not os.path.exists(OPTICAL_PATH):
    print("Run python scripts/download_sample_data.py first!")
    sys.exit(1)

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

print("============================================================")
print("REAL DATA UPLOAD PHASE")
print("============================================================")
opt1 = upload(OPTICAL_PATH, 'T1')
opt2 = upload(OPTICAL_T2_PATH, 'T2')
sar1 = upload(SAR_PATH, 'SAR')
print(f"opt1: {opt1.get('asset_id')}, modality={opt1.get('modality')}")
print(f"opt2: {opt2.get('asset_id')}, modality={opt2.get('modality')}")
print(f"sar1: {sar1.get('asset_id')}, modality={sar1.get('modality')}")

print("\n============================================================")
print("FLOW A: Single Optical Image (Landsat 7 RGB) - VLM Query")
print("============================================================")
ra = analyze('What does this satellite image show?', [opt1['asset_id']])
print(f"  Task:    {ra.get('task')}")
print(f"  Status:  {ra.get('status')}")
print(f"  Summary: {ra.get('summary')}")
RESULTS['flow_a'] = ra

print("\n============================================================")
print("FLOW B: Bi-temporal Change Detection (Landsat 7 T1 vs T2)")
print("============================================================")
rb = analyze('What changed between these two images?', [opt1['asset_id'], opt2['asset_id']])
print(f"  Task:    {rb.get('task')}")
print(f"  Status:  {rb.get('status')}")
print(f"  Summary: {rb.get('summary')}")
m = rb.get('metrics', {})
print(f"  Metrics: change_fraction={m.get('change_fraction')}, changed_pixel_count={m.get('changed_pixel_count')}")
RESULTS['flow_b'] = rb

print("\n============================================================")
print("FLOW C: Optical + SAR Cross-Modal")
print("============================================================")
rc = analyze('Compare optical and SAR observations.', [opt1['asset_id'], sar1['asset_id']])
print(f"  Task:    {rc.get('task')}")
print(f"  Status:  {rc.get('status')}")
print(f"  Summary: {rc.get('summary')}")
m = rc.get('metrics', {})
print(f"  Metrics: bbox_iou={m.get('bbox_iou', m.get('iou'))}")
RESULTS['flow_c'] = rc

print("\n============================================================")
print("FLOW D: Real SAR Analysis (Thresholding/Stats)")
print("============================================================")
# We need to trigger the SAR tool directly. Since HeuristicLLMProvider triggers SAR tool for 1 asset if modality is SAR:
rsar = analyze('Analyze the SAR backscatter properties.', [sar1['asset_id']])
print(f"  Task:    {rsar.get('task')}")
print(f"  Status:  {rsar.get('status')}")
print(f"  Summary: {rsar.get('summary')}")
m = rsar.get('metrics', {})
print(f"  Metrics: mean_backscatter={m.get('mean_backscatter', 0):.2f} dB, p99={m.get('p99', 0):.2f}")
RESULTS['flow_d'] = rsar
