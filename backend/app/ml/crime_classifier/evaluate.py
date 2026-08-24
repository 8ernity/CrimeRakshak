"""Evaluation, Temperature Calibration, and Threshold Optimization for Crime Classifier."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, f1_score
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from app.ml.crime_classifier.dataset import (
    CLASSES,
    IDX_TO_CLASS,
    CrimeDataset,
    get_data_transforms,
)
from app.ml.crime_classifier.model import (
    AbstentionClassifier,
    CrimeResNet18,
    TemperatureScaler,
)
from app.ml.crime_classifier.train import MODEL_PATH


def compute_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error (ECE)."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    confidences = np.max(probs, axis=1)
    predictions = np.argmax(probs, axis=1)
    accuracies = predictions == labels

    ece = 0.0
    total_samples = len(labels)

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = np.mean(in_bin)

        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(accuracies[in_bin])
            avg_confidence_in_bin = np.mean(confidences[in_bin])
            ece += np.abs(accuracy_in_bin - avg_confidence_in_bin) * prop_in_bin

    return float(ece)


def evaluate_baseline():
    print("=" * 60)
    print("3. MODEL EVALUATION, CALIBRATION & ABSTENTION THRESHOLDING")
    print("=" * 60)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = CrimeResNet18(num_classes=len(CLASSES), pretrained=False).to(device)

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model checkpoint not found at '{MODEL_PATH}'. Run train.py first.")

    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.eval()

    _, val_test_transform = get_data_transforms()
    val_dataset = CrimeDataset(split="val", transform=val_test_transform)
    test_dataset = CrimeDataset(split="test", transform=val_test_transform)

    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    # 1. Collect Validation Logits & Labels
    val_logits_list, val_labels_list = [], []
    with torch.no_grad():
        for imgs, lbls in val_loader:
            imgs = imgs.to(device)
            logits = model(imgs)
            val_logits_list.append(logits.cpu())
            val_labels_list.append(lbls)

    val_logits = torch.cat(val_logits_list, dim=0)
    val_labels = torch.cat(val_labels_list, dim=0)

    # 2. Temperature Scaling Calibration
    scaler = TemperatureScaler()
    uncalibrated_val_probs = F.softmax(val_logits, dim=1).numpy()
    val_labels_np = val_labels.numpy()
    ece_before = compute_ece(uncalibrated_val_probs, val_labels_np)

    scaler.calibrate(val_logits, val_labels)
    with torch.no_grad():
        calibrated_val_logits = scaler(val_logits)
        calibrated_val_probs = F.softmax(calibrated_val_logits, dim=1).detach().numpy()
    ece_after = compute_ece(calibrated_val_probs, val_labels_np)

    print(f"Calibration ECE (Before Temperature Scaling): {ece_before:.4f}")
    print(f"Calibration ECE (After Temperature Scaling):  {ece_after:.4f}")

    # 3. Grid Search Thresholds on Pre-computed Calibrated Validation Probabilities
    best_conf_thresh = 0.65
    best_margin_thresh = 0.15
    best_val_score = -1.0

    val_top1_probs = np.max(calibrated_val_probs, axis=1)
    val_sorted_probs = np.sort(calibrated_val_probs, axis=1)[:, ::-1]
    val_margins = val_sorted_probs[:, 0] - val_sorted_probs[:, 1]
    val_top1_indices = np.argmax(calibrated_val_probs, axis=1)

    val_true_super = np.array([
        "crime_related" if IDX_TO_CLASS[l].startswith("crime_") else "non_crime"
        for l in val_labels_np
    ])

    for c_thresh in [0.55, 0.60, 0.65, 0.70, 0.75]:
        for m_thresh in [0.05, 0.10, 0.15, 0.20]:
            pred_statuses = []
            for i in range(len(val_labels_np)):
                p_cls = IDX_TO_CLASS[val_top1_indices[i]]
                if val_top1_probs[i] < c_thresh or val_margins[i] < m_thresh:
                    pred_statuses.append("uncertain")
                elif p_cls.startswith("crime_"):
                    pred_statuses.append("crime_related")
                else:
                    pred_statuses.append("non_crime")
            
            pred_statuses = np.array(pred_statuses)
            decided_mask = pred_statuses != "uncertain"
            if np.sum(decided_mask) > 0:
                acc_score = float(np.mean(pred_statuses[decided_mask] == val_true_super[decided_mask]))
                if acc_score > best_val_score:
                    best_val_score = acc_score
                    best_conf_thresh = c_thresh
                    best_margin_thresh = m_thresh

    print(f"\nSelected Thresholds from Validation Grid Search:")
    print(f"  Confidence Threshold (T_conf): {best_conf_thresh:.2f}")
    print(f"  Margin Threshold (T_margin):    {best_margin_thresh:.2f}")

    # 4. Final Evaluation on Test Dataset
    final_ab_classifier = AbstentionClassifier(
        model=model,
        temperature_scaler=scaler,
        confidence_threshold=best_conf_thresh,
        margin_threshold=best_margin_thresh,
        device=device,
    )

    test_raw_preds, test_true_indices, test_states = [], [], []
    for imgs, lbls in test_loader:
        preds = final_ab_classifier.predict(imgs)
        test_states.extend([p["status"] for p in preds])
        test_raw_preds.extend([CLASSES.index(p["category"]) for p in preds])
        test_true_indices.extend(lbls.numpy())

    test_true_indices = np.array(test_true_indices)
    test_raw_preds = np.array(test_raw_preds)

    # Calculate Core Metrics
    accuracy = float(np.mean(test_raw_preds == test_true_indices))
    macro_f1 = float(f1_score(test_true_indices, test_raw_preds, average="macro"))

    # Crime vs Non-Crime Metrics
    crime_indices = [i for i, c in enumerate(CLASSES) if c.startswith("crime_")]
    is_true_crime = np.isin(test_true_indices, crime_indices)
    is_pred_crime = np.isin(test_raw_preds, crime_indices)

    tp = float(np.sum(is_true_crime & is_pred_crime))
    fn = float(np.sum(is_true_crime & ~is_pred_crime))
    fp = float(np.sum(~is_true_crime & is_pred_crime))
    tn = float(np.sum(~is_true_crime & ~is_pred_crime))

    crime_recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    cm = confusion_matrix(test_true_indices, test_raw_preds)
    report = classification_report(test_true_indices, test_raw_preds, target_names=CLASSES)

    # State Distribution Output Breakdown
    state_counts = {
        "crime_related": test_states.count("crime_related"),
        "non_crime": test_states.count("non_crime"),
        "uncertain": test_states.count("uncertain"),
    }

    print("\n" + "=" * 60)
    print("FINAL MODEL EVALUATION REPORT")
    print("=" * 60)
    print(f"Accuracy:        {accuracy * 100:.2f}%")
    print(f"Macro F1 Score:  {macro_f1:.4f}")
    print(f"Crime Recall:    {crime_recall * 100:.2f}% (Sensitivity)")
    print(f"False Neg Rate:  {fnr * 100:.2f}% (FNR - Critical Miss Rate)")
    print(f"False Pos Rate:  {fpr * 100:.2f}% (FPR - False Alarm Rate)")
    print(f"False Positives: {int(fp)} | False Negatives: {int(fn)}")
    print(f"Calibration ECE: {ece_after:.4f} (Calibrated T = {scaler.temperature.item():.4f})")

    print("\nAbstention Decision Breakdown:")
    for st, count in state_counts.items():
        pct = (count / len(test_states)) * 100
        print(f"  {st:15s}: {count:3d} samples ({pct:.1f}%)")

    print("\nConfusion Matrix (Rows=True, Cols=Pred):")
    print(cm)

    print("\nDetailed Sklearn Classification Report:")
    print(report)
    print("=" * 60 + "\n")

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "crime_recall": crime_recall,
        "fnr": fnr,
        "fpr": fpr,
        "fp": int(fp),
        "fn": int(fn),
        "ece": ece_after,
        "temperature": scaler.temperature.item(),
        "confidence_threshold": best_conf_thresh,
        "margin_threshold": best_margin_thresh,
        "confusion_matrix": cm.tolist(),
        "saved_model_path": os.path.abspath(MODEL_PATH),
    }


if __name__ == "__main__":
    evaluate_baseline()
