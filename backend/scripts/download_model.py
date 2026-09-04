import os
import time
import argparse
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
import torch

def download_qwen2_vl(model_dir: str):
    """
    Downloads Qwen2-VL-2B-Instruct to the specified local directory.
    Configured for CPU-safe FP32/BF16 downloading, avoiding GPU allocation.
    """
    model_id = "Qwen/Qwen2-VL-2B-Instruct"
    
    print(f"Starting download of {model_id} to {model_dir}")
    print("This will download approximately 4.5 GB of weights. Please wait...")
    
    start_time = time.time()
    
    # We use torch.bfloat16 or float32 depending on CPU capabilities.
    # Qwen2-VL natively uses bfloat16, which modern CPUs support well.
    processor = AutoProcessor.from_pretrained(model_id, cache_dir=model_dir)
    print(f"Processor downloaded. Loading model...")
    
    # Download weights
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="cpu",
        cache_dir=model_dir
    )
    
    duration = time.time() - start_time
    print(f"Download complete! Time taken: {duration:.2f} seconds.")
    print("Model cached successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Qwen2-VL model")
    parser.add_argument("--model-dir", type=str, default="./models", help="Directory to store model weights")
    args = parser.parse_args()
    
    os.makedirs(args.model_dir, exist_ok=True)
    download_qwen2_vl(args.model_dir)
