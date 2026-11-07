import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / "machine_learning" / "src"))

from models import CivicFixPredictor

predictor = CivicFixPredictor()
classes = [
    "broken_streetlight",
    "crack",
    "garbage",
    "manhole",
    "normal",
    "pipeline_leakage",
    "pothole"
]

print("\n" + "=" * 70)
print("CIVICFIX 7-CLASS INFERENCE VERIFICATION TEST")
print("=" * 70)

correct = 0
for cls in classes:
    path = BASE_DIR / "dataset" / "test" / cls / f"{cls}_0019.jpg"
    res = predictor.predict(path)
    pred_cls = res["category"]
    conf = res["confidence"]
    priority = res["priority"]
    match = (pred_cls == cls)
    if match:
        correct += 1
    mark = "[PASS]" if match else "[FAIL]"
    print(f"{mark} Actual: {cls:18} | Predicted: {pred_cls:18} | Conf: {conf*100:5.1f}% | {priority}")

print("=" * 70)
print(f"Accuracy: {correct}/{len(classes)} ({correct/len(classes)*100:.1f}%)")
print("=" * 70 + "\n")
