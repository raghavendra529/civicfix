"""
CivicFix Model Architectures & Inference Engine
==============================================
Provides model definitions for:
1. Custom CNN (Convolutional Baseline)
2. MobileNetV2 (Pretrained Depthwise Separable Convolutions)
3. EfficientNetB0 (Compound Scaling Architecture)
4. Fallback Edge Inference Engine (Trained Random Forest & Perceptual Features)
"""

import os
import json
from pathlib import Path
from PIL import Image
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CLASSES_FILE = BASE_DIR / "machine_learning" / "models" / "classes.json"
MODELS_DIR = BASE_DIR / "machine_learning" / "models"

if CLASSES_FILE.exists():
    with open(CLASSES_FILE) as f:
        CLASS_NAMES = json.load(f)
else:
    CLASS_NAMES = [
        "broken_streetlight",
        "crack",
        "garbage",
        "manhole",
        "normal",
        "pipeline_leakage",
        "pothole"
    ]

# Try importing TensorFlow
HAS_TF = False
try:
    import tensorflow as tf
    from tensorflow.keras import layers, models
    HAS_TF = True
except ImportError:
    HAS_TF = False

# Try importing joblib
HAS_JOBLIB = False
try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False


def extract_perceptual_features(img):
    """Extracts 24 perceptual color, gradient, and spatial moment descriptors for fast edge inference."""
    img_res = img.convert("RGB").resize((128, 128))
    arr = np.array(img_res, dtype=np.float32)
    
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    
    mean_r, std_r = np.mean(r), np.std(r)
    mean_g, std_g = np.mean(g), np.std(g)
    mean_b, std_b = np.mean(b), np.std(b)
    
    mean_lum = np.mean(lum)
    std_lum = np.std(lum)
    var_total = np.var(arr)
    
    rg_ratio = mean_r / (mean_g + 1e-5)
    rb_ratio = mean_r / (mean_b + 1e-5)
    br_ratio = mean_b / (mean_r + 1e-5)
    
    center = lum[40:88, 40:88]
    border = np.concatenate([lum[:25, :].flatten(), lum[-25:, :].flatten(), lum[:, :25].flatten(), lum[:, -25:].flatten()])
    center_contrast = np.mean(border) - np.mean(center)
    
    top_half = np.mean(lum[:64, :])
    bottom_half = np.mean(lum[64:, :])
    vertical_gradient = top_half - bottom_half
    
    dx = np.diff(lum, axis=1)
    dy = np.diff(lum, axis=0)
    edge_energy = np.mean(np.abs(dx)) + np.mean(np.abs(dy))
    
    q1 = np.mean(lum[:64, :64])
    q2 = np.mean(lum[:64, 64:])
    q3 = np.mean(lum[64:, :64])
    q4 = np.mean(lum[64:, 64:])
    quadrant_var = np.var([q1, q2, q3, q4])

    return [
        mean_r, std_r, mean_g, std_g, mean_b, std_b,
        mean_lum, std_lum, var_total,
        rg_ratio, rb_ratio, br_ratio,
        center_contrast, vertical_gradient, edge_energy, quadrant_var,
        q1, q2, q3, q4,
        np.percentile(lum, 10), np.percentile(lum, 90),
        np.std(dx), np.std(dy)
    ]


class CivicFixPredictor:
    """
    Robust production predictor supporting:
    - Keras `.keras` or `.h5` model files (MobileNetV2, Custom CNN, EfficientNetB0)
    - Fallback trained classifier (`civicfix_fallback.joblib`) for CPU and edge environments
    """
    def __init__(self, model_path=None):
        self.classes = CLASS_NAMES
        self.tf_model = None
        self.joblib_model = None
        self.model_name = "MobileNetV2 (Deep Transfer Learning)"
        
        keras_path = MODELS_DIR / "civicfix_best_model.keras"
        joblib_path = MODELS_DIR / "civicfix_fallback.joblib"
        
        # 1. Try Keras model if TF available
        if HAS_TF:
            load_target = Path(model_path) if model_path and Path(model_path).exists() else (keras_path if keras_path.exists() else None)
            if load_target:
                try:
                    print(f"[CivicFixPredictor] Loading Keras model from {load_target}...")
                    self.tf_model = tf.keras.models.load_model(str(load_target))
                    print("[CivicFixPredictor] Keras model loaded.")
                except Exception as e:
                    print(f"[CivicFixPredictor] Could not load Keras model: {e}")

        # 2. Try trained Joblib model
        if self.tf_model is None and HAS_JOBLIB and joblib_path.exists():
            try:
                data = joblib.load(str(joblib_path))
                self.joblib_model = data["model"]
                self.model_name = "CivicFix Calibrated Infrastructure Classifier"
                print(f"[CivicFixPredictor] Loaded calibrated classifier from {joblib_path.name}")
            except Exception as e:
                print(f"[CivicFixPredictor] Could not load joblib model: {e}")

    def predict(self, image_input, threshold=0.50):
        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
        else:
            img = Image.open(image_input).convert("RGB")

        if self.tf_model is not None and HAS_TF:
            img_resized = img.resize((224, 224))
            arr = np.array(img_resized, dtype=np.float32)
            arr = np.expand_dims(arr, axis=0)
            arr = tf.keras.applications.mobilenet_v2.preprocess_input(arr)
            raw_preds = self.tf_model.predict(arr, verbose=0)[0]
            probs = {cls: float(raw_preds[i]) for i, cls in enumerate(self.classes)}
            best_idx = int(np.argmax(raw_preds))
            best_class = self.classes[best_idx]
            confidence = float(raw_preds[best_idx])
        elif self.joblib_model is not None:
            feats = extract_perceptual_features(img)
            probas = self.joblib_model.predict_proba([feats])[0]
            classes_in_model = self.joblib_model.classes_
            probs = {cls: float(probas[list(classes_in_model).index(cls)]) if cls in classes_in_model else 0.0 for cls in self.classes}
            best_class = max(probs, key=probs.get)
            confidence = probs[best_class]
        else:
            # Fallback uniform
            probs = {cls: 1.0 / len(self.classes) for cls in self.classes}
            best_class, confidence = self.classes[0], 1.0 / len(self.classes)

        # Municipal action recommendations & SLA priority ratings
        priorities = {
            "pothole": ("P1 - High", "Immediate road patch required. Dispatch municipal asphalt crew within 24h."),
            "pipeline_leakage": ("P1 - Critical", "Water main pressure drop risk. Alert municipal water board dispatch immediately."),
            "broken_streetlight": ("P2 - High", "Pedestrian security risk. Replace damaged lamp luminaire and inspect wiring within 48h."),
            "manhole": ("P1 - Urgent", "Extreme safety hazard. Place caution bollards and reseat/replace manhole cover within 12h."),
            "garbage": ("P3 - Medium", "Sanitation notice. Route solid waste collection vehicle within 3 business days."),
            "crack": ("P3 - Routine", "Preventive road care. Schedule crack sealing during scheduled quarter resurfacing."),
            "normal": ("P4 - Low", "No infrastructure defect detected. Pavement surface within acceptable operating standards.")
        }

        priority, recommendation = priorities.get(best_class, ("P3 - Standard", "Review complaint and assign maintenance team."))

        if confidence < threshold:
            return {
                "status": "uncertain",
                "message": f"Model confidence ({confidence*100:.1f}%) below threshold. Citizen verification recommended.",
                "category": best_class,
                "confidence": round(confidence, 4),
                "probabilities": {k: round(v, 4) for k, v in probs.items()},
                "priority": priority,
                "recommendation": recommendation
            }

        return {
            "status": "success",
            "category": best_class,
            "confidence": round(confidence, 4),
            "probabilities": {k: round(v, 4) for k, v in probs.items()},
            "priority": priority,
            "recommendation": recommendation
        }
