"""Training script for 7-class ResNet-18 Crime Classifier."""
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from app.ml.crime_classifier.dataset import (
    CLASSES,
    CrimeDataset,
    build_and_validate_dataset,
    get_data_transforms,
)
from app.ml.crime_classifier.model import CrimeResNet18

MODEL_SAVE_DIR = os.path.join("backend", "models")
MODEL_PATH = os.path.join(MODEL_SAVE_DIR, "resnet18_crime_classifier.pth")


def compute_class_weights(dataset: CrimeDataset) -> torch.Tensor:
    """Compute class-weighted loss weights: w_c = N / (K * N_c)."""
    counts = [0] * len(CLASSES)
    for _, label in dataset.samples:
        counts[label] += 1
    total_samples = len(dataset)
    num_classes = len(CLASSES)
    weights = [total_samples / (num_classes * max(c, 1)) for c in counts]
    return torch.tensor(weights, dtype=torch.float32)


def train_model(epochs: int = 8, batch_size: int = 32, lr: float = 0.001) -> float:
    print("=" * 60)
    print("2. TRAINING RESNET-18 CRIME CLASSIFIER")
    print("=" * 60)

    # 1. Build and validate dataset first
    build_and_validate_dataset(samples_per_class=150)

    train_transform, val_test_transform = get_data_transforms()
    train_dataset = CrimeDataset(split="train", transform=train_transform)
    val_dataset = CrimeDataset(split="val", transform=val_test_transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training Device: {device}")

    model = CrimeResNet18(num_classes=len(CLASSES), pretrained=True).to(device)
    class_weights = compute_class_weights(train_dataset).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)

    best_val_acc = 0.0
    start_time = time.time()

    for epoch in range(1, epochs + 1):
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

        epoch_train_loss = running_loss / total_train
        epoch_train_acc = correct_train / total_train

        # Validation Phase
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

        epoch_val_loss = val_loss / total_val
        epoch_val_acc = correct_val / total_val

        print(
            f"Epoch [{epoch:02d}/{epochs:02d}] "
            f"Train Loss: {epoch_train_loss:.4f} Acc: {epoch_train_acc*100:.2f}% | "
            f"Val Loss: {epoch_val_loss:.4f} Acc: {epoch_val_acc*100:.2f}%",
            flush=True
        )

        if epoch_val_acc >= best_val_acc:
            best_val_acc = epoch_val_acc
            os.makedirs(MODEL_SAVE_DIR, exist_ok=True)
            torch.save(model.state_dict(), MODEL_PATH)

    total_training_time = time.time() - start_time
    print("-" * 60, flush=True)
    print(f"Training completed in: {total_training_time:.2f} seconds", flush=True)
    print(f"Best Validation Accuracy: {best_val_acc*100:.2f}%", flush=True)
    print(f"Saved best model checkpoint to: '{os.path.abspath(MODEL_PATH)}'", flush=True)
    print("=" * 60 + "\n", flush=True)

    return total_training_time


if __name__ == "__main__":
    train_model(epochs=5)
