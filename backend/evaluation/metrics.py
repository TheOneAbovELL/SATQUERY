import re

def compute_exact_match(prediction: str, ground_truth: str) -> float:
    """Exact string match (normalized)."""
    def normalize(text):
        return re.sub(r'\W+', '', str(text).lower())
    
    return 1.0 if normalize(prediction) == normalize(ground_truth) else 0.0

def compute_count_error(prediction: str, ground_truth: str) -> float:
    """Calculates absolute error for counting tasks."""
    try:
        # Extract first number found
        pred_num = float(re.findall(r'\d+', str(prediction))[0])
        gt_num = float(re.findall(r'\d+', str(ground_truth))[0])
        return abs(pred_num - gt_num)
    except:
        return -1.0 # Invalid numeric response

def compute_vqa_accuracy(prediction: str, ground_truth: str, task_type: str = "general") -> dict:
    """
    Dispatcher for different benchmark metric rules.
    """
    metrics = {
        "exact_match": compute_exact_match(prediction, ground_truth)
    }
    
    if task_type == "count":
        metrics["count_error"] = compute_count_error(prediction, ground_truth)
        
    return metrics
