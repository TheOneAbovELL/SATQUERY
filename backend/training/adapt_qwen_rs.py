#!/usr/bin/env python3
"""
SatQuery AI — Remote-Sensing VLM Adaptation Pipeline
Build Conversation 12

OBJECTIVE:
  Adapt Qwen2-VL-2B-Instruct to remote-sensing image-language understanding
  using LoRA/PEFT on open-source RS image-text data (UCM-Captions subset,
  or RSICD which is CC-licensed and widely used in RS-VLM research).

ADAPTATION OBJECTIVE RATIONALE:
  We use image→caption adaptation (image + RS caption → correct answer).
  This is the most defensible approach because:
  1. Open RS caption datasets (UCM-Captions, Sydney-Captions, RSICD) are
     publicly available under permissive licenses.
  2. Qwen2-VL was trained on general web/natural image captions; RS captions
     introduce domain-specific vocabulary (runway, storage tank, overpass, etc.).
  3. The adaptation objective directly improves the model's RS language grounding,
     which is the weakest failure mode on domain-specific queries.
  4. LoRA can be applied to the language model layers of Qwen2-VL-2B without
     touching the vision encoder, keeping memory footprint manageable.

HARDWARE-AWARE EXECUTION:
  CUDA available  → full LoRA training on GPU
  CUDA absent     → CPU safe-mode: dataset validation + smoke-test (1-2 steps)

USAGE:
  # Full training (requires GPU):
  python training/adapt_qwen_rs.py --mode full --epochs 3 --batch_size 2

  # CPU smoke-test (verifies pipeline, 2 steps only):
  python training/adapt_qwen_rs.py --mode smoke

  # Dataset prep only:
  python training/adapt_qwen_rs.py --mode data_only
"""
import os
import sys
import json
import time
import argparse
import logging
import random
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

logger = logging.getLogger("satquery.adaptation")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

ROOT = Path(__file__).parent.parent  # backend/
DATA_DIR = ROOT / "data" / "rs_adaptation"
ADAPTER_DIR = ROOT / "models" / "rs_lora_adapter"
MANIFEST_PATH = DATA_DIR / "metadata" / "manifest.jsonl"
TRAINING_MANIFEST_PATH = ADAPTER_DIR / "training_manifest.json"

# ─────────────────────────────────────────────────────────────────────────────
# 1. Dataset Preparation
# ─────────────────────────────────────────────────────────────────────────────

def prepare_dataset(max_samples: int = 500, seed: int = 42) -> Dict[str, Any]:
    """
    Prepares a controlled subset from UCM-Captions (University of California
    Merced Land Use dataset with human-written captions).

    Dataset facts:
      Name     : UCM-Captions
      Source   : https://github.com/201528014227051/RSICD_optimal (subset)
      License  : CC BY-NC-SA 4.0 (permissive for research adaptation)
      Modality : Optical aerial imagery, 256×256 px, 0.3m/px
      Classes  : 21 land-use categories (agriculture, forest, harbor, runway...)
      Captions : 5 human-annotated captions per image (~2100 pairs)
      Format   : JPEG images + JSON caption annotations

    NOTE: This function builds the dataset MANIFEST and directory structure.
    It does NOT automatically download the data to avoid uncontrolled bandwidth.
    Download instructions are printed. If images are already present in
    data/rs_adaptation/raw/, they are indexed automatically.
    """
    (DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "train").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "validation").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "metadata").mkdir(parents=True, exist_ok=True)

    # Check if images already exist
    raw_images = list((DATA_DIR / "raw").glob("**/*.jpg")) + \
                 list((DATA_DIR / "raw").glob("**/*.png")) + \
                 list((DATA_DIR / "raw").glob("**/*.tif"))

    if not raw_images:
        logger.warning("No images found in data/rs_adaptation/raw/")
        logger.info("=" * 60)
        logger.info("DATASET DOWNLOAD INSTRUCTIONS")
        logger.info("=" * 60)
        logger.info("Option A: UCM-Captions (recommended, CC BY-NC-SA 4.0)")
        logger.info("  1. Download from: https://drive.google.com/file/d/0B1jt4ijlxQHJVkR0LXJ3dDdldWM")
        logger.info("  2. Extract to: data/rs_adaptation/raw/UCM/")
        logger.info("  3. Download captions JSON:")
        logger.info("     https://github.com/201528014227051/RSICD_optimal")
        logger.info("     Place dataset_ucm.json in data/rs_adaptation/raw/UCM/")
        logger.info("")
        logger.info("Option B: RSICD (larger, CC BY-NC-SA 4.0)")
        logger.info("  1. https://github.com/201528014227051/RSICD_optimal")
        logger.info("  2. Extract to: data/rs_adaptation/raw/RSICD/")
        logger.info("=" * 60)

        # Write an empty but valid manifest so the pipeline structure is verified
        manifest_meta = {
            "status": "DATA_PENDING",
            "dataset_name": "UCM-Captions",
            "source": "https://github.com/201528014227051/RSICD_optimal",
            "license": "CC BY-NC-SA 4.0",
            "modality": "optical_aerial",
            "instructions": "See download instructions above.",
            "samples_ready": 0
        }
        (DATA_DIR / "metadata" / "manifest_meta.json").write_text(
            json.dumps(manifest_meta, indent=2)
        )
        MANIFEST_PATH.write_text("")
        return {"status": "DATA_PENDING", "samples": 0}

    # Build manifest from existing images
    rng = random.Random(seed)
    all_records = []

    for img_path in raw_images:
        # Try to find a matching caption JSON
        caption = _try_load_caption(img_path)
        if caption:
            all_records.append({
                "image_path": str(img_path.relative_to(ROOT)),
                "text": caption,
                "source_dataset": img_path.parent.name,
                "modality": "optical_aerial",
                "license": "CC BY-NC-SA 4.0"
            })

    rng.shuffle(all_records)
    all_records = all_records[:max_samples]

    split = int(len(all_records) * 0.9)
    for i, rec in enumerate(all_records):
        rec["split"] = "train" if i < split else "validation"

    with MANIFEST_PATH.open("w") as f:
        for rec in all_records:
            f.write(json.dumps(rec) + "\n")

    n_train = sum(1 for r in all_records if r["split"] == "train")
    n_val = len(all_records) - n_train

    meta = {
        "dataset_name": "UCM-Captions",
        "source": "https://github.com/201528014227051/RSICD_optimal",
        "license": "CC BY-NC-SA 4.0",
        "modality": "optical_aerial",
        "total_samples": len(all_records),
        "train_samples": n_train,
        "validation_samples": n_val,
        "seed": seed,
        "prepared_at": datetime.now(timezone.utc).isoformat()
    }
    (DATA_DIR / "metadata" / "manifest_meta.json").write_text(json.dumps(meta, indent=2))
    logger.info(f"Manifest written: {len(all_records)} records ({n_train} train, {n_val} val)")
    return {"status": "READY", "samples": len(all_records), "train": n_train, "val": n_val}

def _try_load_caption(img_path: Path) -> str:
    """Attempt to load a caption for the image from a sibling JSON file."""
    # Pattern: dataset_ucm.json or annotations.json in the same directory
    for json_name in ["dataset_ucm.json", "dataset_rsicd.json", "annotations.json"]:
        json_path = img_path.parent / json_name
        if json_path.exists():
            try:
                data = json.loads(json_path.read_text())
                images = data.get("images", [])
                for entry in images:
                    if entry.get("filename") == img_path.name:
                        sentences = entry.get("sentences", [])
                        if sentences:
                            return sentences[0].get("raw", "")
            except Exception:
                pass
    return ""

def load_manifest(split: str = None) -> List[Dict[str, Any]]:
    """Load all manifest records, optionally filtering by split."""
    if not MANIFEST_PATH.exists():
        return []
    records = []
    with MANIFEST_PATH.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                if split is None or rec.get("split") == split:
                    records.append(rec)
    return records


# ─────────────────────────────────────────────────────────────────────────────
# 2. PEFT / LoRA Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_LORA_CONFIG = {
    "r": 8,                        # LoRA rank — low for CPU feasibility
    "lora_alpha": 16,              # scaling = alpha/r
    "target_modules": [            # Language model attention projections only
        "q_proj", "k_proj", "v_proj", "o_proj"
    ],
    "lora_dropout": 0.05,
    "bias": "none",
    "task_type": "CAUSAL_LM"
}

DEFAULT_TRAINING_CONFIG = {
    "learning_rate": 2e-4,
    "epochs": 3,
    "batch_size": 1,               # CPU-safe: 1 sample at a time
    "gradient_accumulation_steps": 8,
    "max_seq_length": 512,
    "checkpoint_interval": 50,     # steps
    "seed": 42,
    "max_new_tokens_eval": 64,
    "warmup_ratio": 0.1
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Model Loading with LoRA
# ─────────────────────────────────────────────────────────────────────────────

def load_model_with_lora(device: str, lora_config: dict, base_model_id: str = "Qwen/Qwen2-VL-2B-Instruct"):
    """
    Loads Qwen2-VL-2B and attaches LoRA adapters.
    The vision encoder is frozen; only LM attention layers are adapted.
    """
    import torch
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    from peft import get_peft_model, LoraConfig, TaskType

    logger.info(f"Loading base model: {base_model_id} on device={device}")
    dtype = torch.bfloat16 if device == "cpu" else torch.float16

    processor = AutoProcessor.from_pretrained(base_model_id, cache_dir="./models")
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        base_model_id,
        torch_dtype=dtype,
        device_map=device,
        cache_dir="./models"
    )

    # Freeze the entire model first, then LoRA will unfreeze only the target modules
    for param in model.parameters():
        param.requires_grad = False

    peft_cfg = LoraConfig(
        r=lora_config["r"],
        lora_alpha=lora_config["lora_alpha"],
        target_modules=lora_config["target_modules"],
        lora_dropout=lora_config["lora_dropout"],
        bias=lora_config["bias"],
        task_type=TaskType.CAUSAL_LM
    )
    model = get_peft_model(model, peft_cfg)
    model.print_trainable_parameters()
    return model, processor


# ─────────────────────────────────────────────────────────────────────────────
# 4. Collation / Prompt Construction
# ─────────────────────────────────────────────────────────────────────────────

def build_prompt_inputs(record: Dict[str, Any], processor, root: Path, max_seq_length: int):
    """
    Constructs a Qwen2-VL chat template for one RS image-caption pair.
    Format: [image] + "Describe this remote-sensing image." → caption
    """
    import torch
    from PIL import Image

    img_path = root / record["image_path"]
    if not img_path.exists():
        return None

    img = Image.open(img_path).convert("RGB")
    caption = record["text"]

    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": img},
            {"type": "text", "text": "Describe this remote-sensing image concisely."}
        ]
    }]

    prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    # Append the target caption as the expected completion
    full_text = prompt + caption + processor.tokenizer.eos_token

    inputs = processor(
        text=[full_text], images=[img], padding="max_length",
        max_length=max_seq_length, truncation=True, return_tensors="pt"
    )
    # Labels: same as input_ids but mask out the prompt portion
    labels = inputs["input_ids"].clone()
    # Find where the prompt ends — mask prompt tokens with -100
    prompt_tokens = processor(text=[prompt], return_tensors="pt")["input_ids"]
    prompt_len = prompt_tokens.shape[-1]
    labels[0, :prompt_len] = -100

    return {**inputs, "labels": labels}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Training Loop
# ─────────────────────────────────────────────────────────────────────────────

def train(args):
    import torch
    import json

    device = "cuda" if (torch.cuda.is_available() and args.mode == "full") else "cpu"
    is_smoke = args.mode == "smoke"

    logger.info(f"Device: {device} | Mode: {args.mode}")
    if device == "cpu" and not is_smoke:
        logger.warning(
            "FULL TRAINING ON CPU IS NOT PRACTICAL FOR LARGE MODELS.\n"
            "This will be extremely slow. Consider running on a GPU machine.\n"
            "Switching to smoke-test mode automatically."
        )
        is_smoke = True

    # Prep data
    data_status = prepare_dataset(max_samples=args.max_samples, seed=args.seed)
    if data_status["status"] == "DATA_PENDING":
        logger.warning("Dataset not yet downloaded. Cannot train. Pipeline structure verified.")
        _write_training_manifest(args, data_status, status="DATA_PENDING", final_loss=None)
        return

    train_records = load_manifest("train")
    val_records = load_manifest("validation")

    if not train_records:
        logger.error("No training records found. Aborting.")
        return

    if is_smoke:
        train_records = train_records[:2]
        val_records = val_records[:1]
        logger.info(f"SMOKE MODE: Using {len(train_records)} train, {len(val_records)} val records")

    lora_cfg = DEFAULT_LORA_CONFIG.copy()
    train_cfg = {**DEFAULT_TRAINING_CONFIG,
                 "learning_rate": args.lr,
                 "epochs": args.epochs,
                 "batch_size": args.batch_size,
                 "seed": args.seed}

    model, processor = load_model_with_lora(device, lora_cfg, args.base_model)
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=train_cfg["learning_rate"]
    )

    ADAPTER_DIR.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(train_cfg["seed"])

    global_step = 0
    final_loss = None
    start_time = time.time()

    epochs = 1 if is_smoke else train_cfg["epochs"]

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        n_steps = 0

        for i, record in enumerate(train_records):
            batch = build_prompt_inputs(
                record, processor, ROOT, train_cfg["max_seq_length"]
            )
            if batch is None:
                continue

            batch = {k: v.to(device) for k, v in batch.items()}

            outputs = model(**batch)
            loss = outputs.loss / train_cfg["gradient_accumulation_steps"]
            loss.backward()
            epoch_loss += loss.item()
            n_steps += 1

            if (i + 1) % train_cfg["gradient_accumulation_steps"] == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                optimizer.zero_grad()
                global_step += 1
                logger.info(f"  Step {global_step} | loss={epoch_loss/n_steps:.4f}")

            if is_smoke:
                break  # Only one step in smoke mode

        final_loss = epoch_loss / max(n_steps, 1)
        logger.info(f"Epoch {epoch+1} complete | avg_loss={final_loss:.4f}")

    # Save adapter
    model.save_pretrained(str(ADAPTER_DIR))
    processor.save_pretrained(str(ADAPTER_DIR))
    logger.info(f"Adapter saved to: {ADAPTER_DIR}")

    duration = time.time() - start_time
    status = "SMOKE_TEST_PASSED" if is_smoke else "FULL_ADAPTER_TRAINED"
    _write_training_manifest(args, data_status, status=status, final_loss=final_loss,
                             duration_sec=duration)
    logger.info(f"Status: {status} | Duration: {duration:.1f}s | Loss: {final_loss:.4f}")


def _write_training_manifest(args, data_status: dict, status: str,
                              final_loss, duration_sec: float = 0.0):
    import torch
    manifest = {
        "base_model": args.base_model,
        "adapter_type": "LoRA (PEFT)",
        "lora_config": DEFAULT_LORA_CONFIG,
        "training_config": {**DEFAULT_TRAINING_CONFIG,
                            "lr": args.lr, "epochs": args.epochs,
                            "batch_size": args.batch_size, "seed": args.seed},
        "dataset": {
            "name": "UCM-Captions",
            "source": "https://github.com/201528014227051/RSICD_optimal",
            "license": "CC BY-NC-SA 4.0",
            **data_status
        },
        "hardware": {
            "device": "cuda" if __import__("torch").cuda.is_available() else "cpu",
            "cuda_available": __import__("torch").cuda.is_available()
        },
        "status": status,
        "final_loss": final_loss,
        "training_duration_sec": duration_sec,
        "adapter_path": str(ADAPTER_DIR),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    ADAPTER_DIR.mkdir(parents=True, exist_ok=True)
    (ADAPTER_DIR / "training_manifest.json").write_text(json.dumps(manifest, indent=2))
    logger.info(f"Training manifest written to {ADAPTER_DIR / 'training_manifest.json'}")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Evaluation
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(args):
    """
    Qualitative evaluation comparing base vs adapted Qwen on the same RS images.
    Metrics: This function produces structured qualitative output only.
    We do NOT claim quantitative improvement from <10 samples.
    """
    import torch
    from peft import PeftModel
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    from qwen_vl_utils import process_vision_info
    from PIL import Image

    val_records = load_manifest("validation")[:3]
    if not val_records:
        logger.warning("No validation records available. Cannot evaluate.")
        return

    device = "cpu"
    dtype = torch.bfloat16

    logger.info("Loading base model for evaluation...")
    processor = AutoProcessor.from_pretrained(args.base_model, cache_dir="./models")
    base_model = Qwen2VLForConditionalGeneration.from_pretrained(
        args.base_model, torch_dtype=dtype, device_map=device, cache_dir="./models"
    )

    adapted_model = None
    if ADAPTER_DIR.exists() and (ADAPTER_DIR / "adapter_config.json").exists():
        logger.info("Loading adapted model...")
        adapted_model = PeftModel.from_pretrained(base_model, str(ADAPTER_DIR))

    results = []
    for rec in val_records:
        img_path = ROOT / rec["image_path"]
        if not img_path.exists():
            continue
        img = Image.open(img_path).convert("RGB")
        prompt_text = "Describe this remote-sensing image concisely."
        messages = [{"role": "user", "content": [
            {"type": "image", "image": img}, {"type": "text", "text": prompt_text}
        ]}]
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, _ = process_vision_info(messages)
        inputs = processor(text=[text], images=image_inputs, return_tensors="pt").to(device)

        def generate(m):
            with torch.no_grad():
                out = m.generate(**inputs, max_new_tokens=64)
            trimmed = out[0][inputs["input_ids"].shape[-1]:]
            return processor.decode(trimmed, skip_special_tokens=True)

        base_answer = generate(base_model)
        adapted_answer = generate(adapted_model) if adapted_model else "ADAPTER_NOT_AVAILABLE"

        results.append({
            "image": rec["image_path"],
            "reference_caption": rec["text"],
            "base_model_output": base_answer,
            "adapted_model_output": adapted_answer
        })
        logger.info(f"\n  Image: {rec['image_path']}")
        logger.info(f"  Reference: {rec['text']}")
        logger.info(f"  Base:     {base_answer}")
        logger.info(f"  Adapted:  {adapted_answer}")

    (ADAPTER_DIR / "eval_results.json").write_text(json.dumps(results, indent=2))
    logger.info(f"\nQUALITATIVE EVALUATION ONLY — {len(results)} samples.")
    logger.info("No quantitative claim of improvement is made from this sample size.")


# ─────────────────────────────────────────────────────────────────────────────
# 7. CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SatQuery RS VLM Adaptation")
    parser.add_argument("--mode", choices=["full", "smoke", "data_only", "eval"],
                        default="smoke", help="Execution mode")
    parser.add_argument("--base_model", default="Qwen/Qwen2-VL-2B-Instruct")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max_samples", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.mode == "data_only":
        prepare_dataset(max_samples=args.max_samples, seed=args.seed)
    elif args.mode == "eval":
        evaluate(args)
    else:
        train(args)

if __name__ == "__main__":
    main()
