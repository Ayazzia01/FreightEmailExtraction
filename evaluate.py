import json

def evaluate(predictions_path, ground_truth_path):
    with open(predictions_path) as f:
        preds = {item['id']: item for item in json.load(f)}
    with open(ground_truth_path) as f:
        truth = {item['id']: item for item in json.load(f)}

    fields = ["product_line", "origin_port_code", "origin_port_name", 
              "destination_port_code", "destination_port_name", 
              "incoterm", "cargo_weight_kg", "cargo_cbm", "is_dangerous"]
    
    stats = {field: {"correct": 0, "total": 0} for field in fields}

    for email_id, truth_val in truth.items():
        pred_val = preds.get(email_id)
        if not pred_val:
            continue
            
        for field in fields:
            stats[field]["total"] += 1
            if isinstance(truth_val[field], float):
                if round(truth_val[field], 2) == round(pred_val.get(field, 0) or 0, 2):
                    stats[field]["correct"] += 1
            elif str(truth_val[field]).lower() == str(pred_val.get(field)).lower():
                stats[field]["correct"] += 1

    print("--- ACCURACY METRICS ---")
    total_correct = 0
    total_fields = 0
    for field, data in stats.items():
        acc = (data["correct"] / data["total"]) * 100 if data["total"] > 0 else 0
        total_correct += data["correct"]
        total_fields += data["total"]
        print(f"{field:25}: {acc:.2f}%")
    
    print(f"\nOVERALL ACCURACY: {(total_correct / total_fields)*100:.2f}%")

if __name__ == "__main__":
    evaluate("output.json", "ground_truth.json")