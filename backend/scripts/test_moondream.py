import os
import time
import torch
import psutil
from PIL import Image

def get_free_ram_mb():
    return psutil.virtual_memory().available / (1024 * 1024)

def test_moondream():
    print(f"OS: {os.name}")
    print(f"Total RAM: {psutil.virtual_memory().total / (1024*1024*1024):.2f} GB")
    print(f"Free RAM before load: {get_free_ram_mb():.2f} MB")
    
    model_dir = "./models_fallback"
    os.makedirs(model_dir, exist_ok=True)
    model_id = "vikhyatk/moondream2"
    
    print("Loading processor & model...")
    start_load = time.time()
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        # Moondream2 recommends trust_remote_code=True and standard initialization
        model = AutoModelForCausalLM.from_pretrained(
            model_id, trust_remote_code=True, cache_dir=model_dir
        )
        tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=model_dir)
        load_time = time.time() - start_load
        print(f"Model loaded in {load_time:.2f}s")
        print(f"Free RAM after model load: {get_free_ram_mb():.2f} MB")
    except Exception as e:
        print(f"Model load FAILED with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    print("Creating test image...")
    img_path = "dummy_test_moondream.jpg"
    img = Image.new('RGB', (256, 256), color = (73, 109, 137))
    img.save(img_path)
    
    print("First inference...")
    start_inf1 = time.time()
    try:
        enc_image = model.encode_image(img)
        answer = model.answer_question(enc_image, "Describe this image and identify the main visible objects or land-cover features.", tokenizer)
        inf1_time = time.time() - start_inf1
        print(f"First inference time: {inf1_time:.2f}s")
        print(f"Output: {answer}")
    except Exception as e:
        print(f"Inference 1 FAILED: {str(e)}")
        return False
        
    print("Second inference...")
    start_inf2 = time.time()
    try:
        answer2 = model.answer_question(enc_image, "What are the most prominent features visible in this image?", tokenizer)
        inf2_time = time.time() - start_inf2
        print(f"Second inference time: {inf2_time:.2f}s")
        print(f"Output 2: {answer2}")
    except Exception as e:
        print(f"Inference 2 FAILED: {str(e)}")
        return False
        
    print(f"Free RAM after inference: {get_free_ram_mb():.2f} MB")
    return True

if __name__ == "__main__":
    test_moondream()
