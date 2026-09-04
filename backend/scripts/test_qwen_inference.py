import os
import time
import torch
import psutil
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image

def get_free_ram_mb():
    return psutil.virtual_memory().available / (1024 * 1024)

def test_qwen_inference():
    model_dir = "./models"
    model_id = "Qwen/Qwen2-VL-2B-Instruct"
    
    print("Loading processor & model...")
    processor = AutoProcessor.from_pretrained(model_id, cache_dir=model_dir)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_id, 
        torch_dtype=torch.bfloat16, 
        device_map="cpu", 
        cache_dir=model_dir
    )
    
    img_path = "dummy_test.jpg"
    if not os.path.exists(img_path):
        Image.new('RGB', (256, 256), color = (73, 109, 137)).save(img_path)
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": img_path},
                {"type": "text", "text": "Describe this image."},
            ],
        }
    ]
    
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to("cpu")
    
    print("Starting Inference 1...")
    start_inf = time.time()
    generated_ids = model.generate(**inputs, max_new_tokens=50)
    generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
    output_text = processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    print(f"Inf 1 Time: {time.time()-start_inf:.2f}s")
    print(f"Output: {output_text[0]}")
    
    print("Starting Inference 2...")
    start_inf2 = time.time()
    generated_ids2 = model.generate(**inputs, max_new_tokens=50)
    generated_ids_trimmed2 = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids2)]
    output_text2 = processor.batch_decode(generated_ids_trimmed2, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    print(f"Inf 2 Time: {time.time()-start_inf2:.2f}s")
    print(f"Output 2: {output_text2[0]}")

if __name__ == "__main__":
    test_qwen_inference()
