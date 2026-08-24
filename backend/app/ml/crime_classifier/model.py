"""ResNet-18 Model Architecture, Temperature Scaler Calibration, and Abstention Logic."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from torchvision.models import ResNet18_Weights

from app.ml.crime_classifier.dataset import CLASSES, IDX_TO_CLASS


class CrimeResNet18(nn.Module):
    """Pretrained ResNet-18 Fine-Tuned for 7-Class Crime vs Non-Crime Classification."""

    def __init__(self, num_classes: int = 7, pretrained: bool = True):
        super().__init__()
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        self.backbone = models.resnet18(weights=weights)
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


class TemperatureScaler(nn.Module):
    """Platt Scaling / Temperature Scaling Module for Logit Calibration."""

    def __init__(self):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        temperature = self.temperature.unsqueeze(1).expand(logits.size(0), logits.size(1))
        return logits / temperature

    def calibrate(self, val_logits: torch.Tensor, val_labels: torch.Tensor):
        """Fit optimal temperature T on validation logits using L-BFGS optimizer."""
        optimizer = torch.optim.LBFGS([self.temperature], lr=0.01, max_iter=50)
        criterion = nn.CrossEntropyLoss()

        def eval_loss():
            optimizer.zero_grad()
            loss = criterion(self.forward(val_logits), val_labels)
            loss.backward()
            return loss

        optimizer.step(eval_loss)
        print(f"Optimal Temperature Scaling T = {self.temperature.item():.4f}")


class AbstentionClassifier:
    """Confidence & Margin-Based Decision Classifier."""

    def __init__(
        self,
        model: nn.Module,
        temperature_scaler: TemperatureScaler = None,
        confidence_threshold: float = 0.65,
        margin_threshold: float = 0.15,
        device: str = "cpu",
    ):
        self.model = model.to(device)
        self.temperature_scaler = temperature_scaler
        self.confidence_threshold = confidence_threshold
        self.margin_threshold = margin_threshold
        self.device = device

    @torch.no_grad()
    def predict(self, inputs: torch.Tensor) -> list:
        """Predict calibrated state: crime_related, non_crime, or uncertain."""
        self.model.eval()
        inputs = inputs.to(self.device)
        logits = self.model(inputs)

        if self.temperature_scaler is not None:
            logits = self.temperature_scaler(logits)

        probs = F.softmax(logits, dim=1).cpu().numpy()
        results = []

        for p_row in probs:
            top1_idx = int(np.argmax(p_row))
            top1_prob = float(p_row[top1_idx])
            sorted_p = np.sort(p_row)[::-1]
            margin = float(sorted_p[0] - sorted_p[1])
            predicted_class = IDX_TO_CLASS[top1_idx]

            # Abstention / Uncertainty Gate Rule
            if top1_prob < self.confidence_threshold or margin < self.margin_threshold:
                status = "uncertain"
            elif predicted_class.startswith("crime_"):
                status = "crime_related"
            else:
                status = "non_crime"

            results.append({
                "status": status,
                "category": predicted_class,
                "confidence": round(top1_prob, 4),
                "margin": round(margin, 4),
                "probabilities": {
                    IDX_TO_CLASS[i]: round(float(p_row[i]), 4) for i in range(len(p_row))
                },
            })

        return results
