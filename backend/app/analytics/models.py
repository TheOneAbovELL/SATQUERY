import os
from pathlib import Path

# Repo root is three levels up from app/analytics/models.py
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DEFAULT_ADAPTER_PATH = _REPO_ROOT / "models" / "rs_lora_adapter"
from typing import Dict, Any, List
from app.domain.models import ModelAdapterDefinition, AssetModality, ToolRequest, ToolResult, ImageAsset, ToolDefinition, ToolErrorCode
from app.agent.interfaces import BaseModelAdapter, BaseTool

class DummySceneClassifierAdapter(BaseModelAdapter):
    def __init__(self):
        definition = ModelAdapterDefinition(
            model_id="test_dummy_scene_resnet",
            model_version="0.1.0-mock",
            task="scene_classification",
            modality=AssetModality.RGB,
            input_requirements={"dimensions": (256, 256), "channels": 3},
            preprocessing_requirements={"normalization": "imagenet"},
            output_type="classification_logits",
            hardware_requirements="CPU",
            inference_method="local_heuristic_mock",
            availability="AVAILABLE"
        )
        super().__init__(definition)
        self.is_loaded = False
        
    def load(self):
        self.is_loaded = True
        
    def unload(self):
        self.is_loaded = False
        
    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")
        return {
            "predicted_class": "Urban",
            "confidence_score": 0.85,
            "logits": [2.3, 0.1, -1.0, 0.4]
        }

class SceneClassificationTool(BaseTool):
    def __init__(self, adapter: DummySceneClassifierAdapter):
        definition = ToolDefinition(
            tool_id="scene_classifier",
            name="TEST ADAPTER - Scene Classifier",
            description="TEST ADAPTER: Simulates scene classification.",
            task_capabilities=["scene_classification"],
            accepted_modalities=[AssetModality.RGB, AssetModality.MULTISPECTRAL],
            required_capabilities=[],
            output_schema={"type": "object", "properties": {"class": {"type": "string"}}},
            version="1.0.0"
        )
        super().__init__(definition)
        self.adapter = adapter
        
    def execute(self, request: ToolRequest, assets: List[ImageAsset]) -> ToolResult:
        if not self.adapter.is_loaded:
            self.adapter.load()
            
        try:
            predictions = self.adapter.predict({"mock_tensor": True})
            return ToolResult(
                request_id=request.request_id,
                tool_id=self.definition.tool_id,
                tool_version=self.definition.version,
                success=True,
                execution_duration_sec=0.0,
                outputs={"scene_class": predictions["predicted_class"]},
                confidence={"MODEL_CONFIDENCE": predictions["confidence_score"]},
                provenance=["test_adapter: local_heuristic_mock"]
            )
        except Exception as e:
            return ToolResult(
                request_id=request.request_id,
                tool_id=self.definition.tool_id,
                tool_version=self.definition.version,
                success=False,
                execution_duration_sec=0.0,
                error_code=ToolErrorCode.EXECUTION_FAILED,
                error_message=str(e)
            )

class Qwen2VLAdapter(BaseModelAdapter):
    """
    PRIMARY LOCAL MODEL: Qwen2-VL-2B-Instruct
    Supports optional LoRA adapter for remote-sensing domain adaptation.

    Configuration:
      QWEN_ADAPTER_PATH  env var  → override path to trained LoRA adapter directory.
      Default              → <repo_root>/models/rs_lora_adapter (auto-detected).
      If adapter directory contains adapter_config.json, loads base + adapter.
      If absent/invalid, loads base model only (graceful fallback).
    """
    def __init__(self):
        definition = ModelAdapterDefinition(
            model_id="Qwen/Qwen2-VL-2B-Instruct",
            model_version="2b-instruct",
            task="vqa_and_grounding",
            modality=AssetModality.RGB,
            input_requirements={"format": "PIL.Image"},
            preprocessing_requirements={"resize": "dynamic_resolution"},
            output_type="text_string",
            hardware_requirements="CPU/Integrated GPU",
            parameter_count="2.0B",
            quantization="FP16/INT8",
            memory_estimate="~4.5GB (FP16), ~2.5GB (INT8)",
            license="Apache 2.0",
            source="HuggingFace",
            inference_method="local_transformers",
            availability="AVAILABLE"
        )
        super().__init__(definition)
        self.model = None
        self.processor = None
        # Prefer explicit env var; fall back to project-relative default
        env_override = os.environ.get("QWEN_ADAPTER_PATH", "")
        self.adapter_path: str = env_override if env_override else str(_DEFAULT_ADAPTER_PATH)
        self.adapter_loaded: bool = False
        self._adaptation_meta: Dict[str, Any] = {}

    @property
    def inference_mode(self) -> str:
        if self.adapter_loaded:
            return "Qwen2-VL-2B + remote-sensing LoRA adapter"
        return "Qwen2-VL-2B base"

    def load(self):
        try:
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
            import torch

            dtype = torch.bfloat16
            self.processor = AutoProcessor.from_pretrained(
                self.definition.model_id, cache_dir="./models"
            )
            base_model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.definition.model_id,
                torch_dtype=dtype,
                device_map="cpu",
                cache_dir="./models"
            )

            # Try to load LoRA adapter
            if self.adapter_path and os.path.isdir(self.adapter_path):
                adapter_config = os.path.join(self.adapter_path, "adapter_config.json")
                if os.path.exists(adapter_config):
                    try:
                        from peft import PeftModel
                        self.model = PeftModel.from_pretrained(base_model, self.adapter_path)
                        self.adapter_loaded = True

                        # Load training manifest for provenance
                        manifest_path = os.path.join(self.adapter_path, "training_manifest.json")
                        if os.path.exists(manifest_path):
                            import json
                            self._adaptation_meta = json.loads(
                                open(manifest_path).read()
                            )
                    except Exception as e:
                        # Adapter load failed — fall back to base model, never crash
                        import warnings
                        warnings.warn(f"LoRA adapter load failed ({e}), using base model.")
                        self.model = base_model
                        self.adapter_loaded = False
                else:
                    self.model = base_model
            else:
                self.model = base_model

        except ImportError:
            raise ImportError("Qwen2-VL requires `transformers`, `qwen-vl-utils`, and `torch`.")

    def unload(self):
        self.model = None
        self.processor = None
        self.adapter_loaded = False
        import gc
        gc.collect()

    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if not self.model or not self.processor:
            raise RuntimeError("Model not loaded")

        from qwen_vl_utils import process_vision_info

        img = inputs['image']
        query_text = inputs['query']

        messages = [{"role": "user", "content": [
            {"type": "image", "image": img},
            {"type": "text", "text": query_text},
        ]}]

        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        model_inputs = self.processor(
            text=[text], images=image_inputs, videos=video_inputs,
            padding=True, return_tensors="pt",
        ).to("cpu")

        generated_ids = self.model.generate(**model_inputs, max_new_tokens=128)
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )

        # Build provenance
        prov = [f"inference_mode: {self.inference_mode}"]
        if self.adapter_loaded and self._adaptation_meta:
            ds = self._adaptation_meta.get("dataset", {})
            prov.append(f"adapter_dataset: {ds.get('name', 'unknown')}")
            prov.append(f"adapter_status: {self._adaptation_meta.get('status', 'unknown')}")

        return {
            "answer": output_text[0],
            "inference_mode": self.inference_mode,
            "adapter_loaded": self.adapter_loaded,
            "provenance": prov
        }


class Moondream2Adapter(BaseModelAdapter):
    """
    FALLBACK LOCAL MODEL
    Moondream2
    Tiny (1.8B) VLM. Faster than Qwen2-VL but weaker at small-object grounding.
    """
    def __init__(self):
        definition = ModelAdapterDefinition(
            model_id="vikhyatk/moondream2",
            model_version="latest",
            task="vqa_and_captioning",
            modality=AssetModality.RGB,
            input_requirements={"format": "PIL.Image"},
            preprocessing_requirements={"resize": False},
            output_type="text_string",
            hardware_requirements="CPU",
            parameter_count="1.8B",
            quantization="FP16/INT8",
            memory_estimate="~3.6GB (FP16)",
            license="Apache 2.0 / MIT",
            source="HuggingFace",
            inference_method="local_transformers",
            availability="AVAILABLE"
        )
        super().__init__(definition)
        self.model = None
        self.tokenizer = None
        
    def load(self):
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            raise RuntimeError("Moondream2 weights not downloaded locally. External model dependency requires explicit fetch.")
        except ImportError:
            raise ImportError("Moondream2 requires `transformers` and `einops` packages.")

    def unload(self):
        self.model = None
        self.tokenizer = None
        
    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if not self.model:
            raise RuntimeError("Model not loaded")
        return {"answer": "Mocked answer due to missing weights"}

class GeoChatAdapter(BaseModelAdapter):
    """
    FUTURE GPU MODEL
    GeoChat (7B)
    Dedicated remote-sensing VLM fine-tuned for geospatial tasks.
    Too heavy and slow for primary CPU-only execution on a 16GB laptop, reserved for GPU worker.
    """
    def __init__(self):
        definition = ModelAdapterDefinition(
            model_id="MBZUAI/GeoChat",
            model_version="7B",
            task="rs_vqa_and_grounding",
            modality=AssetModality.RGB,
            input_requirements={"format": "PIL.Image"},
            preprocessing_requirements={"resize": "fixed_512"},
            output_type="text_string",
            hardware_requirements="Dedicated NVIDIA GPU (16GB+ VRAM)",
            parameter_count="7B",
            quantization="FP16",
            memory_estimate="~14GB (FP16)",
            license="Non-commercial / LLaMA-based",
            source="GitHub/HuggingFace",
            inference_method="remote_gpu_worker",
            availability="UNAVAILABLE"
        )
        super().__init__(definition)
        
    def load(self):
        raise NotImplementedError("GeoChat adapter intended for remote GPU worker deployment.")

    def unload(self):
        pass
        
    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("GeoChat adapter intended for remote GPU worker deployment.")
