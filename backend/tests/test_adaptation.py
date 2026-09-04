"""
Tests for Build Conversation 12 — VLM Adaptation Infrastructure

Tests cover:
  - Dataset manifest validation
  - Adapter path detection and fallback
  - Training configuration validation
  - CPU smoke-test mode (no actual model weights required)
  - Qwen adapter inference_mode provenance
  - Adapter fallback when path is invalid
"""
import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


# ─────────────────────────────────────────────────────────────────────────────
# 1. Dataset Manifest Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDatasetManifest:
    def test_empty_manifest_returns_data_pending(self, tmp_path, monkeypatch):
        """If no images exist, prepare_dataset reports DATA_PENDING."""
        monkeypatch.chdir(tmp_path)
        # Patch DATA_DIR and MANIFEST_PATH to use tmp_path
        import training.adapt_qwen_rs as pipeline
        monkeypatch.setattr(pipeline, "DATA_DIR", tmp_path / "data" / "rs_adaptation")
        monkeypatch.setattr(pipeline, "MANIFEST_PATH", tmp_path / "data" / "rs_adaptation" / "metadata" / "manifest.jsonl")
        monkeypatch.setattr(pipeline, "ADAPTER_DIR", tmp_path / "models" / "rs_lora_adapter")

        result = pipeline.prepare_dataset(max_samples=10, seed=42)
        assert result["status"] == "DATA_PENDING"
        assert result["samples"] == 0

    def test_manifest_with_images(self, tmp_path, monkeypatch):
        """With images but no captions, records have empty captions."""
        import training.adapt_qwen_rs as pipeline

        raw_dir = tmp_path / "data" / "rs_adaptation" / "raw" / "UCM"
        raw_dir.mkdir(parents=True)
        # Create fake image files
        for i in range(5):
            (raw_dir / f"img_{i:03d}.jpg").write_bytes(b"FAKE_JPEG")

        monkeypatch.setattr(pipeline, "DATA_DIR", tmp_path / "data" / "rs_adaptation")
        monkeypatch.setattr(pipeline, "MANIFEST_PATH", tmp_path / "data" / "rs_adaptation" / "metadata" / "manifest.jsonl")
        monkeypatch.setattr(pipeline, "ADAPTER_DIR", tmp_path / "models" / "rs_lora_adapter")
        monkeypatch.setattr(pipeline, "ROOT", tmp_path)

        result = pipeline.prepare_dataset(max_samples=10, seed=42)
        # Without captions JSON, records will have empty text — so no records
        # (the pipeline only includes records with non-empty captions)
        assert result["status"] in ("DATA_PENDING", "READY")

    def test_manifest_with_captions(self, tmp_path, monkeypatch):
        """With images AND captions, manifest is populated correctly."""
        import training.adapt_qwen_rs as pipeline

        raw_dir = tmp_path / "data" / "rs_adaptation" / "raw" / "UCM"
        raw_dir.mkdir(parents=True)

        # Create fake images
        img_names = [f"img_{i:03d}.jpg" for i in range(6)]
        for name in img_names:
            (raw_dir / name).write_bytes(b"FAKE_JPEG")

        # Create caption JSON
        caption_data = {
            "images": [
                {"filename": name, "sentences": [{"raw": f"A remote sensing image of category {i}"}]}
                for i, name in enumerate(img_names)
            ]
        }
        (raw_dir / "dataset_ucm.json").write_text(json.dumps(caption_data))

        monkeypatch.setattr(pipeline, "DATA_DIR", tmp_path / "data" / "rs_adaptation")
        monkeypatch.setattr(pipeline, "MANIFEST_PATH", tmp_path / "data" / "rs_adaptation" / "metadata" / "manifest.jsonl")
        monkeypatch.setattr(pipeline, "ADAPTER_DIR", tmp_path / "models" / "rs_lora_adapter")
        monkeypatch.setattr(pipeline, "ROOT", tmp_path)

        result = pipeline.prepare_dataset(max_samples=10, seed=42)
        assert result["status"] == "READY"
        assert result["samples"] == 6
        assert result["train"] + result["val"] == 6

    def test_manifest_reproducibility(self, tmp_path, monkeypatch):
        """Same seed must produce identical split."""
        import training.adapt_qwen_rs as pipeline

        raw_dir = tmp_path / "data" / "rs_adaptation" / "raw" / "UCM"
        raw_dir.mkdir(parents=True)
        img_names = [f"img_{i:03d}.jpg" for i in range(10)]
        for name in img_names:
            (raw_dir / name).write_bytes(b"FAKE")
        caption_data = {"images": [
            {"filename": n, "sentences": [{"raw": f"Caption {i}"}]} for i, n in enumerate(img_names)
        ]}
        (raw_dir / "dataset_ucm.json").write_text(json.dumps(caption_data))

        manifest_path = tmp_path / "data" / "rs_adaptation" / "metadata" / "manifest.jsonl"
        monkeypatch.setattr(pipeline, "DATA_DIR", tmp_path / "data" / "rs_adaptation")
        monkeypatch.setattr(pipeline, "MANIFEST_PATH", manifest_path)
        monkeypatch.setattr(pipeline, "ADAPTER_DIR", tmp_path / "models" / "rs_lora_adapter")
        monkeypatch.setattr(pipeline, "ROOT", tmp_path)

        pipeline.prepare_dataset(max_samples=10, seed=99)
        r1 = manifest_path.read_text()

        # Reset by clearing and re-running
        manifest_path.write_text("")
        pipeline.prepare_dataset(max_samples=10, seed=99)
        r2 = manifest_path.read_text()

        assert r1 == r2, "Manifest is not reproducible with the same seed"

    def test_load_manifest_split_filter(self, tmp_path, monkeypatch):
        """load_manifest correctly filters by split."""
        import training.adapt_qwen_rs as pipeline

        records = [
            {"image_path": "a.jpg", "text": "x", "split": "train"},
            {"image_path": "b.jpg", "text": "y", "split": "validation"},
            {"image_path": "c.jpg", "text": "z", "split": "train"},
        ]
        manifest_path = tmp_path / "manifest.jsonl"
        with manifest_path.open("w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        monkeypatch.setattr(pipeline, "MANIFEST_PATH", manifest_path)

        train = pipeline.load_manifest("train")
        val = pipeline.load_manifest("validation")
        assert len(train) == 2
        assert len(val) == 1


# ─────────────────────────────────────────────────────────────────────────────
# 2. Adapter Configuration Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAdapterConfiguration:
    def test_default_lora_config_valid(self):
        """LoRA defaults are reasonable for CPU-safe operation."""
        from training.adapt_qwen_rs import DEFAULT_LORA_CONFIG
        assert DEFAULT_LORA_CONFIG["r"] <= 16, "Rank too large for CPU-safe defaults"
        assert DEFAULT_LORA_CONFIG["task_type"] == "CAUSAL_LM"
        assert "q_proj" in DEFAULT_LORA_CONFIG["target_modules"]

    def test_training_config_has_required_keys(self):
        from training.adapt_qwen_rs import DEFAULT_TRAINING_CONFIG
        required = ["learning_rate", "epochs", "batch_size", "gradient_accumulation_steps",
                    "max_seq_length", "checkpoint_interval", "seed"]
        for k in required:
            assert k in DEFAULT_TRAINING_CONFIG, f"Missing key: {k}"

    def test_training_config_cpu_safe_batch_size(self):
        from training.adapt_qwen_rs import DEFAULT_TRAINING_CONFIG
        assert DEFAULT_TRAINING_CONFIG["batch_size"] == 1, "Default batch_size must be 1 for CPU safety"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Qwen2VLAdapter Fallback Tests (no actual model weights)
# ─────────────────────────────────────────────────────────────────────────────

class TestQwen2VLAdapterFallback:
    def test_inference_mode_base_when_no_adapter_path(self, monkeypatch):
        """Without QWEN_ADAPTER_PATH, adapter reports base inference mode."""
        monkeypatch.delenv("QWEN_ADAPTER_PATH", raising=False)
        from app.analytics.models import Qwen2VLAdapter
        adapter = Qwen2VLAdapter()
        assert adapter.adapter_path == ""
        assert adapter.adapter_loaded is False
        assert adapter.inference_mode == "Qwen2-VL-2B base"

    def test_inference_mode_with_env_var(self, monkeypatch):
        """With QWEN_ADAPTER_PATH set, adapter reads the path."""
        monkeypatch.setenv("QWEN_ADAPTER_PATH", "/some/adapter/path")
        from importlib import reload
        import app.analytics.models as m
        reload(m)  # re-import to pick up env var
        adapter = m.Qwen2VLAdapter()
        assert adapter.adapter_path == "/some/adapter/path"
        assert adapter.adapter_loaded is False  # Not loaded yet
        assert adapter.inference_mode == "Qwen2-VL-2B base"
        monkeypatch.delenv("QWEN_ADAPTER_PATH", raising=False)

    def test_adapter_path_invalid_falls_back_to_base(self, monkeypatch, tmp_path):
        """If adapter path exists but has no adapter_config.json, uses base model."""
        monkeypatch.setenv("QWEN_ADAPTER_PATH", str(tmp_path))  # dir exists but empty

        from importlib import reload
        import app.analytics.models as m
        reload(m)
        adapter = m.Qwen2VLAdapter()

        # Mock transformers to avoid downloading weights
        mock_model = MagicMock()
        mock_processor = MagicMock()

        with patch("transformers.Qwen2VLForConditionalGeneration.from_pretrained", return_value=mock_model), \
             patch("transformers.AutoProcessor.from_pretrained", return_value=mock_processor):
            adapter.load()

        assert adapter.adapter_loaded is False
        assert adapter.inference_mode == "Qwen2-VL-2B base"
        monkeypatch.delenv("QWEN_ADAPTER_PATH", raising=False)

    def test_adapter_path_with_config_tries_peft(self, monkeypatch, tmp_path):
        """If adapter_config.json exists, PeftModel is attempted."""
        adapter_dir = tmp_path / "my_lora"
        adapter_dir.mkdir()
        (adapter_dir / "adapter_config.json").write_text(json.dumps({
            "peft_type": "LORA", "r": 8, "task_type": "CAUSAL_LM"
        }))
        (adapter_dir / "training_manifest.json").write_text(json.dumps({
            "status": "SMOKE_TEST_PASSED",
            "dataset": {"name": "UCM-Captions"}
        }))

        monkeypatch.setenv("QWEN_ADAPTER_PATH", str(adapter_dir))
        from importlib import reload
        import app.analytics.models as m
        reload(m)
        adapter = m.Qwen2VLAdapter()

        mock_model = MagicMock()
        mock_peft_model = MagicMock()

        with patch("transformers.Qwen2VLForConditionalGeneration.from_pretrained", return_value=mock_model), \
             patch("transformers.AutoProcessor.from_pretrained", return_value=MagicMock()), \
             patch("peft.PeftModel.from_pretrained", return_value=mock_peft_model):
            adapter.load()

        assert adapter.adapter_loaded is True
        assert "LoRA adapter" in adapter.inference_mode
        assert adapter._adaptation_meta.get("status") == "SMOKE_TEST_PASSED"
        monkeypatch.delenv("QWEN_ADAPTER_PATH", raising=False)

    def test_adapter_load_failure_graceful_fallback(self, monkeypatch, tmp_path):
        """If PeftModel.from_pretrained raises, falls back to base model gracefully."""
        adapter_dir = tmp_path / "broken_lora"
        adapter_dir.mkdir()
        (adapter_dir / "adapter_config.json").write_text("{}")

        monkeypatch.setenv("QWEN_ADAPTER_PATH", str(adapter_dir))
        from importlib import reload
        import app.analytics.models as m
        reload(m)
        adapter = m.Qwen2VLAdapter()

        mock_model = MagicMock()
        with patch("transformers.Qwen2VLForConditionalGeneration.from_pretrained", return_value=mock_model), \
             patch("transformers.AutoProcessor.from_pretrained", return_value=MagicMock()), \
             patch("peft.PeftModel.from_pretrained", side_effect=RuntimeError("PEFT error")):
            adapter.load()  # Should NOT raise

        assert adapter.adapter_loaded is False
        assert adapter.inference_mode == "Qwen2-VL-2B base"
        monkeypatch.delenv("QWEN_ADAPTER_PATH", raising=False)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Provenance / Trace Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAdapterProvenance:
    def test_predict_returns_inference_mode(self):
        """predict() must return inference_mode key for provenance."""
        from app.analytics.models import Qwen2VLAdapter
        from PIL import Image
        import numpy as np

        adapter = Qwen2VLAdapter()
        adapter.adapter_loaded = False

        # Build processor mock — must support .to() (returns MagicMock again)
        mock_inputs = MagicMock()
        mock_inputs.input_ids = MagicMock()
        mock_inputs.__iter__ = MagicMock(return_value=iter([]))
        mock_inputs.items = MagicMock(return_value={}.items())  # avoid unpacking issues
        mock_inputs.to.return_value = mock_inputs

        mock_processor = MagicMock()
        mock_processor.apply_chat_template.return_value = "prompt"
        mock_processor.return_value = mock_inputs
        mock_processor.batch_decode.return_value = ["A parking lot with several cars."]

        mock_model = MagicMock()
        mock_model.generate.return_value = [MagicMock()]

        adapter.model = mock_model
        adapter.processor = mock_processor

        with patch("qwen_vl_utils.process_vision_info", return_value=([], [])):
            img = Image.fromarray(np.zeros((64, 64, 3), dtype=np.uint8))
            result = adapter.predict({"image": img, "query": "What is this?"})

        assert "inference_mode" in result
        assert result["inference_mode"] == "Qwen2-VL-2B base"
        assert isinstance(result["provenance"], list)
        assert len(result["provenance"]) >= 1

    def test_training_manifest_written(self, tmp_path, monkeypatch):
        """Training manifest must be written with no fabricated loss."""
        import training.adapt_qwen_rs as pipeline

        monkeypatch.setattr(pipeline, "ADAPTER_DIR", tmp_path / "adapter")
        (tmp_path / "adapter").mkdir()

        class FakeArgs:
            base_model = "Qwen/Qwen2-VL-2B-Instruct"
            lr = 2e-4
            epochs = 1
            batch_size = 1
            seed = 42

        pipeline._write_training_manifest(
            FakeArgs(),
            {"status": "DATA_PENDING", "samples": 0},
            status="DATA_PENDING",
            final_loss=None
        )

        manifest_path = tmp_path / "adapter" / "training_manifest.json"
        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text())
        assert data["status"] == "DATA_PENDING"
        assert data["final_loss"] is None  # Must NOT fabricate a loss
        assert data["base_model"] == "Qwen/Qwen2-VL-2B-Instruct"
