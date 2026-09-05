import requests, os, sys, json, time
sys.stdout.reconfigure(encoding='utf-8')

DATA = 'mock_data/real_samples'
flows = {}

def upload(path):
    with open(path, 'rb') as f:
        r = requests.post('http://127.0.0.1:8000/api/v1/upload',
            files={'file': (os.path.basename(path), f, 'image/tiff')})
    return r.json()

def analyze(query, ids):
    r = requests.post('http://127.0.0.1:8000/api/v1/analyze',
        json={'query': query, 'asset_ids': ids}, timeout=120)
    return r.json()

# Health
h = requests.get('http://127.0.0.1:8000/health').json()
print(f'Health: {h}')

# Upload
print('\n=== UPLOAD ===')
opt1 = upload(f'{DATA}/landsat7_rgb_sample.tif')
opt2 = upload(f'{DATA}/landsat7_rgb_t2_simulated.tif')
sar1 = upload(f'{DATA}/simulated_sar_sample.tif')
print(f'opt1: {opt1[\"asset_id\"]} modality={opt1[\"modality\"]}')
print(f'opt2: {opt2[\"asset_id\"]} modality={opt2[\"modality\"]}')
print(f'sar1: {sar1[\"asset_id\"]} modality={sar1[\"modality\"]}')

assert opt1['modality'] == 'RGB', 'opt1 must be RGB'
assert opt2['modality'] == 'RGB', 'opt2 must be RGB'
assert sar1['modality'] == 'SAR', f'sar1 must be SAR, got {sar1[\"modality\"]}'

# Flow 2 (deterministic - test first, faster than VLM)
print('\n=== FLOW 2: Bi-temporal Change ===')
t0 = time.time()
r2 = analyze('What changed between these two images?', [opt1['asset_id'], opt2['asset_id']])
elapsed = time.time() - t0
m = r2.get('metrics', {})
cp = m.get('changed_pixel_count', 0)
vp = m.get('valid_pixel_count', 0)
cf = m.get('change_fraction', 0)
print(f'  status={r2.get(\"status\")} time={elapsed:.1f}s')
print(f'  changed={cp} valid={vp} fraction={cf:.4f}')
if vp > 0:
    calc = cp / vp
    ok = abs(calc - cf) < 1e-4
    print(f'  Invariant check: {cp}/{vp}={calc:.4f} == {cf:.4f} -> {\"PASS\" if ok else \"FAIL\"}')
flows['flow2'] = 'PASS' if r2.get('status') == 'SUCCESS' else 'FAIL'

# Flow 3: SAR
print('\n=== FLOW 3: SAR Analysis ===')
t0 = time.time()
r3 = analyze('What are the strongest backscatter regions?', [sar1['asset_id']])
elapsed = time.time() - t0
m3 = r3.get('metrics', {})
print(f'  status={r3.get(\"status\")} time={elapsed:.1f}s')
print(f'  mean={m3.get(\"mean\",0):.3f} p99={m3.get(\"p99\",0):.3f}')
flows['flow3'] = 'PASS' if r3.get('status') == 'SUCCESS' else 'FAIL'

# Flow 4: Cross-modal
print('\n=== FLOW 4: Optical + SAR Cross-Modal ===')
t0 = time.time()
r4 = analyze('Compare the optical and SAR evidence.', [opt1['asset_id'], sar1['asset_id']])
elapsed = time.time() - t0
m4 = r4.get('metrics', {})
print(f'  status={r4.get(\"status\")} time={elapsed:.1f}s')
print(f'  bbox_iou={m4.get(\"bbox_iou\", m4.get(\"iou\", \"N/A\"))}')
print(f'  summary={r4.get(\"summary\",\"\")[:100]}')
flows['flow4'] = 'PASS' if r4.get('status') == 'SUCCESS' else 'FAIL'

# Flow 1: VLM (slowest - do last, non-blocking)
print('\n=== FLOW 1: Single Optical VQA (Qwen2-VL) ===')
print('  (Submitting - may take 60-90s on CPU)')
t0 = time.time()
r1 = analyze('What does this satellite image show?', [opt1['asset_id']])
elapsed = time.time() - t0
prov = r1.get('provenance', [])
print(f'  status={r1.get(\"status\")} time={elapsed:.1f}s')
print(f'  summary={r1.get(\"summary\",\"\")[:120]}')
print(f'  provenance={prov[:2]}')
flows['flow1'] = 'PASS' if r1.get('status') == 'SUCCESS' else 'FAIL'

print('\n=== FINAL DEMO FLOW RESULTS ===')
for k,v in flows.items():
    print(f'  {k}: {v}')
all_pass = all(v == 'PASS' for v in flows.values())
print(f'\nOverall: {\"ALL PASS\" if all_pass else \"SOME FLOWS FAILED\"}')
