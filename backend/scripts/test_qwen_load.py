import os
import time
import torch
import psutil
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image

def get_ram_mb():
    return psutil.virtual_memory().used / (1024 * 1024)
    
def get_free_ram_mb():
    return psutil.virtual_memory().available / (1024 * 1024)

def test_qwen2_vl():
    print(f"OS: {os.name}")
    print(f"Total RAM: {psutil.virtual_memory().total / (1024*1024*1024):.2f} GB")
    print(f"Free RAM before load: {get_free_ram_mb():.2f} MB")
    
    model_dir = "./models"
    os.makedirs(model_dir, exist_ok=True)
    model_id = "Qwen/Qwen2-VL-2B-Instruct"
    
    print("Loading processor...")
    try:
        processor = AutoProcessor.from_pretrained(model_id, cache_dir=model_dir)
    except Exception as e:
        print(f"Processor load failed: {e}")
        return False
        
    print(f"Free RAM after processor: {get_free_ram_mb():.2f} MB")
    print("Loading model (this will take a while and ~4.5GB RAM)...")
    start_load = time.time()
    try:
        model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_id, 
            torch_dtype=torch.bfloat16, 
            device_map="cpu", 
            cache_dir=model_dir
        )
        load_time = time.time() - start_load
        print(f"Model loaded in {load_time:.2f}s")
        print(f"Free RAM after model load: {get_free_ram_mb():.2f} MB")
        return True
    except Exception as e:
        print(f"Model load FAILED with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
if __name__ == "__main__":
    test_qwen2_vl()
