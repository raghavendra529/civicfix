"""
CivicFix Lightweight Edge / Fallback Classifier Trainer
======================================================
Trains an ultra-fast Scikit-Learn Random Forest on color, texture, and spatial
moments so local CPU development environments can perform instant, accurate
7-class inference without needing GPU drivers or TensorFlow installed.
"""

import os
import json
from pathlib import Path
from PIL import Image
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASET_DIR = BASE_DIR / "dataset"
MODELS_DIR = BASE_DIR / "machine_learning" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

CLASSES = [
    "broken_streetlight",
    "crack",
    "garbage",
    "manhole",
    "normal",
    "pipeline_leakage",
    "pothole"
]


def extract_features(img_path):
    """Extracts 24 perceptual color, gradient, and spatial moment descriptors."""
    img = Image.open(img_path).convert("RGB").resize((128, 128))
    arr = np.array(img, dtype=np.float32)
    
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    
    # 1. Color moments (mean and std for R, G, B)
    mean_r, std_r = np.mean(r), np.std(r)
    mean_g, std_g = np.mean(g), np.std(g)
    mean_b, std_b = np.mean(b), np.std(b)
    
    # 2. Luminance & Variance
    mean_lum = np.mean(lum)
    std_lum = np.std(lum)
    var_total = np.var(arr)
    
    # 3. Color ratios
    rg_ratio = mean_r / (mean_g + 1e-5)
    rb_ratio = mean_r / (mean_b + 1e-5)
    br_ratio = mean_b / (mean_r + 1e-5)
    
    # 4. Spatial center vs border contrast (crater/pothole/manhole)
    center = lum[40:88, 40:88]
    border = np.concatenate([lum[:25, :].flatten(), lum[-25:, :].flatten(), lum[:, :25].flatten(), lum[:, -25:].flatten()])
    center_contrast = np.mean(border) - np.mean(center)
    
    # 5. Top vs bottom contrast (sky vs ground for streetlight)
    top_half = np.mean(lum[:64, :])
    bottom_half = np.mean(lum[64:, :])
    vertical_gradient = top_half - bottom_half
    
    # 6. High frequency gradients (cracks, clutter, edges)
    dx = np.diff(lum, axis=1)
    dy = np.diff(lum, axis=0)
    edge_energy = np.mean(np.abs(dx)) + np.mean(np.abs(dy))
    
    # 7. Sub-quadrant variations
    q1 = np.mean(lum[:64, :64])
    q2 = np.mean(lum[:64, 64:])
    q3 = np.mean(lum[64:, :64])
    q4 = np.mean(lum[64:, 64:])
    quadrant_var = np.var([q1, q2, q3, q4])

    features = [
        mean_r, std_r, mean_g, std_g, mean_b, std_b,
        mean_lum, std_lum, var_total,
        rg_ratio, rb_ratio, br_ratio,
        center_contrast, vertical_gradient, edge_energy, quadrant_var,
        q1, q2, q3, q4,
        np.percentile(lum, 10), np.percentile(lum, 90),
        np.std(dx), np.std(dy)
    ]
    return features


def train_edge_classifier():
    print("Extracting features from training split...")
    X_train, y_train = [], []
    for cls in CLASSES:
        cls_dir = DATASET_DIR / "train" / cls
        for f in cls_dir.glob("*.*"):
            try:
                feat = extract_features(f)
                X_train.append(feat)
                y_train.append(cls)
            except Exception:
                pass

    print(f"Loaded {len(X_train)} training feature vectors.")

    print("Extracting features from test split...")
    X_test, y_test = [], []
    for cls in CLASSES:
        cls_dir = DATASET_DIR / "test" / cls
        for f in cls_dir.glob("*.*"):
            try:
                feat = extract_features(f)
                X_test.append(feat)
                y_test.append(cls)
            except Exception:
                pass

    print(f"Loaded {len(X_test)} testing feature vectors.")

    # Train Random Forest Classifier
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf.fit(X_train, y_train)

    y_pred = rf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n[Edge Random Forest] Test Accuracy: {acc*100:.2f}%")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Save model and feature extractor config
    out_model_path = MODELS_DIR / "civicfix_fallback.joblib"
    joblib.dump({"model": rf, "classes": rf.classes_.tolist()}, out_model_path)
    print(f"[Model Saved] {out_model_path}")


if __name__ == "__main__":
    train_edge_classifier()
