# Remote-Sensing VLM Adaptation

## Why adaptation is required

Qwen2-VL-2B-Instruct is a general-purpose vision-language model trained on web-scale natural image data. Remote-sensing imagery differs from natural photography in critical ways:

- **Domain vocabulary**: "runway", "storage tank", "overpass", "agricultural land", "harbor" are not common in web caption training data
- **Scale and resolution**: Aerial 0.3m/px overhead views differ structurally from photos
- **Multi-spectral semantics**: NIR, NDVI, backscatter have no natural-image analogues
- **Top-down perspective**: Spatial relationships are entirely different

Without adaptation, Qwen2-VL generates generic or incorrect descriptions for RS imagery. SIH 26167 explicitly requires at least one VLM component to be fine-tuned using BigEarthNet or open-source RS training data.

## Dataset

**UCM-Captions** (University of California Merced Land Use + human captions)
- **Source**: https://github.com/201528014227051/RSICD_optimal
- **License**: CC BY-NC-SA 4.0
- **Modality**: Optical aerial imagery, 256×256 px, ~0.3m/px
- **Classes**: 21 land-use categories (agriculture, forest, harbor, runway, storage tank...)
- **Captions**: 5 human-annotated captions per image (~2100 image-text pairs)
- **Format**: JPEG images + JSON caption annotations

**Why UCM-Captions?**
- Permissive research license (CC BY-NC-SA 4.0)
- Human-annotated, domain-specific RS captions
- Small enough to process locally (256×256 px images)
- Well-established benchmark in RS-VLM research

**If BigEarthNet is preferred**: The pipeline can ingest BigEarthNet labels as pseudo-captions (e.g., "This Sentinel-2 image contains: [class labels]..."). The dataset module is designed to be swappable.

## Adaptation Objective

**Image → Remote-sensing caption** (generative adaptation)

This was chosen over alternatives because:
1. RS captioning datasets are openly available
2. This is the correct adaptation objective for improving RS image-text grounding
3. LoRA can be applied to LM attention layers only, keeping GPU memory feasible

## Preprocessing

```text
RS GeoTIFF / JPEG aerial image
         ↓
  PIL Image (RGB, converted from GeoTIFF via Rasterio band selection)
         ↓
  Qwen2-VL processor (dynamic resolution resize)
         ↓
  Chat template: [image] + "Describe this remote-sensing image..."
         ↓
  Token IDs with label masking (prompt tokens masked, caption tokens supervised)
```

Scientific raster data is never destroyed. The preprocessing converts only at the model input boundary and the original GeoTIFF is preserved.

## Base Model

`Qwen/Qwen2-VL-2B-Instruct` (Apache 2.0)

## PEFT Method

**LoRA (Low-Rank Adaptation)** via the `peft` library (v0.11.1)

```
Target modules: q_proj, k_proj, v_proj, o_proj (LM attention only)
Rank (r): 8
Alpha: 16
Dropout: 0.05
Trainable parameters: ~8M out of 2000M (0.4%)
```

The vision encoder is frozen. Only the language model attention layers are adapted.

## How to Run Training

### Step 1: Download dataset

```bash
# Download UCM images and captions from:
# https://drive.google.com/file/d/0B1jt4ijlxQHJVkR0LXJ3dDdldWM
# Extract to: backend/data/rs_adaptation/raw/UCM/
# Download dataset_ucm.json from RSICD_optimal repo
# Place in: backend/data/rs_adaptation/raw/UCM/dataset_ucm.json
```

### Step 2: Validate dataset pipeline

```bash
cd backend
python training/adapt_qwen_rs.py --mode data_only
```

### Step 3: CPU smoke test (verifies pipeline, 2 gradient steps)

```bash
python training/adapt_qwen_rs.py --mode smoke
```

### Step 4: Full training (requires GPU)

```bash
# On GPU machine:
CUDA_VISIBLE_DEVICES=0 python training/adapt_qwen_rs.py \
  --mode full \
  --epochs 3 \
  --batch_size 4 \
  --lr 2e-4 \
  --max_samples 2000
```

## Hardware Requirements

| Mode | Hardware | RAM | Time |
|------|----------|-----|------|
| data_only | CPU | <2GB | <1 min |
| smoke | CPU (16GB) | ~8GB | ~10-20 min |
| full training | GPU 16GB+ VRAM | 16GB+ | ~2-4 hours |

## Where the Adapter is Stored

```
backend/models/rs_lora_adapter/
  adapter_config.json       # LoRA configuration
  adapter_model.bin         # Adapter weights (~32MB for r=8)
  training_manifest.json    # Full provenance record
  eval_results.json         # Qualitative evaluation outputs
```

## How SatQuery Loads the Adapter

Set environment variable before starting the FastAPI server:

```bash
export QWEN_ADAPTER_PATH=./models/rs_lora_adapter
uvicorn app.main:app --reload
```

The `Qwen2VLAdapter` automatically:
1. Loads the base model
2. Detects `adapter_config.json` in `QWEN_ADAPTER_PATH`
3. Loads the adapter via `PeftModel.from_pretrained`
4. Records inference mode and dataset provenance in every ToolResult

If `QWEN_ADAPTER_PATH` is unset or invalid, it falls back to base model inference without crashing.

## What Was Actually Trained

| Item | Status |
|------|--------|
| Training pipeline implementation | DONE |
| PEFT/LoRA configuration | DONE |
| Dataset manifest and preprocessing | DONE |
| CPU smoke-test mode | IMPLEMENTED |
| Adapter runtime loading with fallback | DONE |
| Provenance in ToolResult | DONE |
| Actual LoRA adapter artifact | PENDING (GPU required for practical training, CPU smoke test requires Qwen base model download ~4.5GB) |

## Limitations

1. **Full training requires GPU** — CPU-mode training at 2B parameters is not practical for >2 steps
2. **Dataset download manual** — UCM-Captions is not auto-downloaded to avoid uncontrolled bandwidth
3. **Adapter not yet trained** — The pipeline is GPU-ready but the actual LoRA artifact has not been produced on the current HP ProBook hardware
4. **Quantitative eval pending** — Proper BLEU/CIDEr evaluation requires a held-out labeled test set

## Reproducibility Command Sequence

```bash
# 1. Install dependencies
pip install peft==0.11.1

# 2. Download UCM-Captions (manual — see instructions above)

# 3. Validate dataset pipeline
cd backend
python training/adapt_qwen_rs.py --mode data_only

# 4. Smoke test (requires Qwen base model, ~4.5GB download)
python training/adapt_qwen_rs.py --mode smoke

# 5. Full training (GPU required)
CUDA_VISIBLE_DEVICES=0 python training/adapt_qwen_rs.py --mode full --epochs 3

# 6. Evaluate
python training/adapt_qwen_rs.py --mode eval

# 7. Enable adapted inference
export QWEN_ADAPTER_PATH=./models/rs_lora_adapter
uvicorn app.main:app
```
