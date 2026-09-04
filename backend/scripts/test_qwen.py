import os
import time
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image

def test_qwen2_vl():
    model_dir = "./models"
    os.makedirs(model_dir, exist_ok=True)
    model_id = "Qwen/Qwen2-VL-2B-Instruct"
    
    print("Loading processor...")
    processor = AutoProcessor.from_pretrained(model_id, cache_dir=model_dir)
    
    print("Loading model (this will take a while and ~4.5GB RAM)...")
    start_load = time.time()
    # Using bfloat16 for modern CPUs (or float32 if unavailable, but transformers handles device_map="cpu" well)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_id, 
        torch_dtype=torch.bfloat16, 
        device_map="cpu", 
        cache_dir=model_dir
    )
    load_time = time.time() - start_load
    print(f"Model loaded in {load_time:.2f}s")
    
    # Create a small dummy image
    img_path = "dummy_test.jpg"
    img = Image.new('RGB', (256, 256), color = (73, 109, 137))
    img.save(img_path)
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": img_path},
                {"type": "text", "text": "Describe this image."},
            ],
        }
    ]
    
    print("Preparing inputs...")
    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to("cpu")
    
    print("First inference...")
    start_inf1 = time.time()
    generated_ids = model.generate(**inputs, max_new_tokens=50)
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )
    inf1_time = time.time() - start_inf1
    print(f"First inference time: {inf1_time:.2f}s")
    print(f"Output: {output_text[0]}")
    
    print("Second inference...")
    start_inf2 = time.time()
    generated_ids = model.generate(**inputs, max_new_tokens=50)
    inf2_time = time.time() - start_inf2
    print(f"Second inference time: {inf2_time:.2f}s")
    
if __name__ == "__main__":
    test_qwen2_vl()
