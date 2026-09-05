import os
import json
from typing import List, Dict, Any, Optional

class DatasetAdapter:
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path

    def is_available(self) -> bool:
        return os.path.exists(self.dataset_path)

    def load_records(self, split="val") -> List[Dict[str, Any]]:
        raise NotImplementedError

class VRSBenchAdapter(DatasetAdapter):
    """
    Adapter for VRSBench (Visual Remote Sensing Benchmark).
    Format expected: JSON file with 'images' and 'annotations' (VQA pairs).
    """
    def __init__(self, dataset_path: str = "./data/vrsbench"):
        super().__init__(dataset_path)

    def load_records(self, split="val") -> List[Dict[str, Any]]:
        if not self.is_available():
            print(f"[VRSBench] Dataset not found at {self.dataset_path}. Status = NOT RUN")
            return []
        
        # Skeleton implementation for when data is provided by evaluators
        records = []
        json_path = os.path.join(self.dataset_path, f"vrsbench_{split}.json")
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
                for item in data.get("annotations", []):
                    records.append({
                        "id": item.get("id"),
                        "image_path": os.path.join(self.dataset_path, "images", item.get("image_id") + ".tif"),
                        "question": item.get("question"),
                        "ground_truth": item.get("answer"),
                        "task_type": "single_image_vqa"
                    })
        return records

class RSVQAAdapter(DatasetAdapter):
    """
    Adapter for RSVQA (Remote Sensing Visual Question Answering).
    Supports high-res and low-res variants (RSVQA-LR / RSVQA-HR).
    """
    def __init__(self, dataset_path: str = "./data/rsvqa"):
        super().__init__(dataset_path)

    def load_records(self, split="val") -> List[Dict[str, Any]]:
        if not self.is_available():
            print(f"[RSVQA] Dataset not found at {self.dataset_path}. Status = NOT RUN")
            return []
        
        records = []
        json_path = os.path.join(self.dataset_path, f"rsvqa_{split}.json")
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
                for item in data.get("questions", []):
                    records.append({
                        "id": item.get("id"),
                        "image_path": os.path.join(self.dataset_path, "Images_LR", str(item.get("img_id")) + ".tif"),
                        "question": item.get("question"),
                        "ground_truth": item.get("answers", [item.get("answer")])[0], # Handle various schema versions
                        "task_type": item.get("type", "unknown") # 'count', 'presence', etc.
                    })
        return records

class CDVQAAdapter(DatasetAdapter):
    """
    Adapter for Change Detection VQA (CDVQA).
    Requires processing pairs of images.
    """
    def __init__(self, dataset_path: str = "./data/cdvqa"):
        super().__init__(dataset_path)

    def load_records(self, split="val") -> List[Dict[str, Any]]:
        if not self.is_available():
            print(f"[CDVQA] Dataset not found at {self.dataset_path}. Status = NOT RUN")
            return []
        
        records = []
        json_path = os.path.join(self.dataset_path, f"cdvqa_{split}.json")
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
                for item in data.get("annotations", []):
                    records.append({
                        "id": item.get("id"),
                        "image_path_t1": os.path.join(self.dataset_path, "T1", item.get("image_id_t1") + ".tif"),
                        "image_path_t2": os.path.join(self.dataset_path, "T2", item.get("image_id_t2") + ".tif"),
                        "question": item.get("question"),
                        "ground_truth": item.get("answer"),
                        "task_type": "change_vqa"
                    })
        return records
