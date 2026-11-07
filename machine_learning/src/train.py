"""
CivicFix Training Script
========================
Trains Custom CNN, MobileNetV2, or EfficientNetB0 on the 7-class infrastructure dataset.

Usage:
  python train.py --model mobilenet --epochs 25 --batch_size 32
"""

import os
import sys
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASET_DIR = BASE_DIR / "dataset"
MODELS_DIR = BASE_DIR / "machine_learning" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

try:
    import tensorflow as tf
    from tensorflow.keras import callbacks
    from models import get_custom_cnn, get_mobilenet_v2, get_efficientnet_b0, CLASS_NAMES
    HAS_TF = True
except ImportError:
    HAS_TF = False


def train_model(model_name="mobilenet", epochs=20, batch_size=32):
    if not HAS_TF:
        print("\n" + "=" * 65)
        print("TENSORFLOW NOT DETECTED IN LOCAL ENVIRONMENT")
        print("=" * 65)
        print("For training full deep transfer learning models on GPU:")
        print("1. Open the included Google Colab notebook:")
        print("   machine_learning/notebooks/CivicFix_Infrastructure_Classification.ipynb")
        print("2. Or install TensorFlow locally:")
        print("   pip install tensorflow")
        print("=" * 65 + "\n")
        return

    print(f"\nInitializing {model_name} training on GPU/CPU...")
    train_dir = DATASET_DIR / "train"
    val_dir = DATASET_DIR / "validation"

    train_ds = tf.keras.utils.image_dataset_from_directory(
        str(train_dir),
        image_size=(224, 224),
        batch_size=batch_size,
        label_mode="int",
        shuffle=True
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        str(val_dir),
        image_size=(224, 224),
        batch_size=batch_size,
        label_mode="int",
        shuffle=False
    )

    if model_name == "custom_cnn":
        model = get_custom_cnn(len(CLASS_NAMES))
    elif model_name == "mobilenet":
        model = get_mobilenet_v2(len(CLASS_NAMES))
    elif model_name == "efficientnet":
        model = get_efficientnet_b0(len(CLASS_NAMES))
    else:
        raise ValueError(f"Unknown model architecture: {model_name}")

    save_path = MODELS_DIR / f"civicfix_{model_name}_best.keras"
    cb = [
        callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
        callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2),
        callbacks.ModelCheckpoint(str(save_path), monitor="val_accuracy", save_best_only=True)
    ]

    print(f"Starting training for {epochs} epochs...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=cb
    )

    # Save final best model
    final_best_path = MODELS_DIR / "civicfix_best_model.keras"
    model.save(str(final_best_path))
    print(f"\n[Training Complete] Model saved to {final_best_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CivicFix Model Training")
    parser.add_argument("--model", type=str, default="mobilenet", choices=["custom_cnn", "mobilenet", "efficientnet"])
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=32)
    args = parser.parse_args()

    train_model(args.model, args.epochs, args.batch_size)
