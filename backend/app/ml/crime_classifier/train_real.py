"""
Training script for 7-class ResNet-18 Crime Classifier on REAL data.

Uses the real-data dataset adapter (real_dataset.py) instead of synthetic
templates. Reuses existing model, class-weighted loss, and AdamW training loop.

The trained model is saved as a SEPARATE checkpoint (resnet18_crime_real.pth)
to preserve the existing synthetic baseline for comparison.
"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from app.ml.crime_classifier.dataset import CLASSES
from app.ml.crime_classifier.model import CrimeResNet18
from app.ml.crime_classifier.real_dataset import (
    FRAMES_DIR,
    DatasetValidator,
    RealCrimeDataset,
    get_real_data_transforms,
    run_ingestion_pipeline,
)

MODEL_SAVE_DIR = os.path.join("backend", "models")
REAL_MODEL_PATH = os.path.join(MODEL_SAVE_DIR, "resnet18_crime_real.pth")


def compute_class_weights(dataset: RealCrimeDataset) -> torch.Tensor:
    """Compute inverse-frequency class weights: w_c = N / (K * N_c)."""
    counts = [0] * len(CLASSES)
    for _, label in dataset.samples:
        counts[label] += 1
    total_samples = len(dataset)
    num_classes = len(CLASSES)
    weights = [total_samples / (num_classes * max(c, 1)) for c in counts]

    print("  Class weights:", flush=True)
    for i, cls_name in enumerate(CLASSES):
        print(f"    {cls_name:22s}: count={counts[i]:5d}  weight={weights[i]:.4f}", flush=True)

    return torch.tensor(weights, dtype=torch.float32)


def train_real_model(
    epochs: int = 20,
    batch_size: int = 32,
    lr: float = 0.0005,
    patience: int = 5,
) -> float:
    """Train ResNet-18 on real surveillance data with early stopping.

    Args:
        epochs: Maximum training epochs.
        batch_size: Batch size.
        lr: Learning rate for AdamW.
        patience: Early stopping patience (epochs without improvement).

    Returns:
        Total training time in seconds.
    """
    print("=" * 70, flush=True)
    print("TRAINING RESNET-18 ON REAL SURVEILLANCE DATA", flush=True)
    print("=" * 70 + "\n", flush=True)

    # 1. Validate dataset exists and is healthy
    print("Step 1: Validating dataset...", flush=True)
    validator = DatasetValidator()
    report = validator.validate_all()

    total_frames = sum(report["split_distribution"].values())
    if total_frames == 0:
        print("ERROR: No frames found. Run the ingestion pipeline first:", flush=True)
        print("  python backend/app/ml/crime_classifier/real_dataset.py", flush=True)
        return 0.0

    if not report["passed"]:
        print("ERROR: Dataset validation failed. Fix issues before training.", flush=True)
        return 0.0

    # 2. Create datasets and loaders
    print("Step 2: Creating data loaders...", flush=True)
    train_transform, val_test_transform = get_real_data_transforms()

    train_dataset = RealCrimeDataset(split="train", transform=train_transform)
    val_dataset = RealCrimeDataset(split="val", transform=val_test_transform)

    if len(train_dataset) == 0:
        print("ERROR: Training dataset is empty.", flush=True)
        return 0.0

    print(f"  Train samples: {len(train_dataset)}", flush=True)
    print(f"  Val samples:   {len(val_dataset)}", flush=True)

    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True,
        num_workers=0, pin_memory=True,
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False,
        num_workers=0, pin_memory=True,
    )

    # 3. Model, loss, optimizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Device: {device}", flush=True)

    model = CrimeResNet18(num_classes=len(CLASSES), pretrained=True).to(device)
    class_weights = compute_class_weights(train_dataset).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)

    # Learning rate scheduler: ReduceLROnPlateau
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=2, verbose=True,
    )

    # 4. Training loop with early stopping
    print(f"\nStep 3: Training ({epochs} max epochs, patience={patience})...\n", flush=True)

    best_val_acc = 0.0
    epochs_without_improvement = 0
    start_time = time.time()

    for epoch in range(1, epochs + 1):
        # -- Train --
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct_train += (preds == labels).sum().item()
            total_train += labels.size(0)

        epoch_train_loss = running_loss / max(total_train, 1)
        epoch_train_acc = correct_train / max(total_train, 1)

        # -- Validate --
        model.eval()
        val_loss = 0.0
        correct_val = 0
        total_val = 0

        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                _, preds = torch.max(outputs, 1)
                correct_val += (preds == labels).sum().item()
                total_val += labels.size(0)

        epoch_val_loss = val_loss / max(total_val, 1)
        epoch_val_acc = correct_val / max(total_val, 1)

        current_lr = optimizer.param_groups[0]["lr"]
        print(
            f"  Epoch [{epoch:02d}/{epochs:02d}] "
            f"Train Loss: {epoch_train_loss:.4f} Acc: {epoch_train_acc*100:.2f}% | "
            f"Val Loss: {epoch_val_loss:.4f} Acc: {epoch_val_acc*100:.2f}% | "
            f"LR: {current_lr:.6f}",
            flush=True,
        )

        scheduler.step(epoch_val_acc)

        # Early stopping
        if epoch_val_acc > best_val_acc:
            best_val_acc = epoch_val_acc
            epochs_without_improvement = 0
            os.makedirs(MODEL_SAVE_DIR, exist_ok=True)
            torch.save(model.state_dict(), REAL_MODEL_PATH)
            print(f"    -> New best model saved ({best_val_acc*100:.2f}%)", flush=True)
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= patience:
                print(f"\n  Early stopping at epoch {epoch} (no improvement for {patience} epochs)", flush=True)
                break

    total_training_time = time.time() - start_time
    print("-" * 70, flush=True)
    print(f"  Training completed in: {total_training_time:.2f} seconds", flush=True)
    print(f"  Best Validation Accuracy: {best_val_acc*100:.2f}%", flush=True)
    print(f"  Model saved to: '{os.path.abspath(REAL_MODEL_PATH)}'", flush=True)
    print("=" * 70 + "\n", flush=True)

    return total_training_time


if __name__ == "__main__":
    train_real_model()
