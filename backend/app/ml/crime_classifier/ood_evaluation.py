"""
Out-of-Distribution (OOD) Generalization Evaluation for Crime Classifier.

This script generates ambiguous, difficult test images that deliberately
break the color/shape shortcuts the model learned from training data,
then evaluates the existing ResNet-18 checkpoint without retraining.

Difficult cases tested:
  - playful wrestling vs assault
  - hugging vs assault
  - person lying down vs assault/injury
  - worker entering restricted area vs intrusion
  - person opening own vehicle/bag vs theft
  - crowd running normally vs violent incident
  - normal vehicle activity vs suspicious vehicle
  - ordinary pedestrian vs suspicious behavior
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import random
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw, ImageFilter
from sklearn.metrics import classification_report, confusion_matrix, f1_score

from app.ml.crime_classifier.dataset import (
    CLASSES,
    CLASS_TO_IDX,
    DATASET_ROOT,
    IDX_TO_CLASS,
    get_data_transforms,
)
from app.ml.crime_classifier.model import CrimeResNet18, TemperatureScaler
from app.ml.crime_classifier.train import MODEL_PATH

OOD_DIR = os.path.join("backend", "data", "crime_classifier_ood")
SAMPLES_PER_SCENARIO = 20


# ---------------------------------------------------------------------------
# OOD Image Generators — deliberately designed to NOT match training shortcuts
# ---------------------------------------------------------------------------

def _gen_playful_wrestling(seed: int) -> Image.Image:
    """Two figures in contact, bright/happy background — should be NON-CRIME but looks like assault."""
    random.seed(seed)
    bg = (random.randint(200, 255), random.randint(220, 255), random.randint(180, 240))
    img = Image.new("RGB", (224, 224), color=bg)
    draw = ImageDraw.Draw(img)
    # Two overlapping figures in warm, friendly colors (NOT red)
    draw.rectangle([50, 50, 110, 180], fill=(100, 180, 100))
    draw.rectangle([80, 60, 140, 175], fill=(80, 160, 120))
    draw.ellipse([60, 30, 100, 60], fill=(200, 180, 150))   # head 1
    draw.ellipse([90, 35, 130, 65], fill=(200, 175, 145))   # head 2
    draw.line([60, 110, 130, 100], fill=(100, 200, 100), width=3)  # arm contact
    return img


def _gen_hugging(seed: int) -> Image.Image:
    """Two figures embracing — should be NON-CRIME but spatial overlap mimics assault."""
    random.seed(seed)
    bg = (random.randint(210, 250), random.randint(200, 240), random.randint(220, 255))
    img = Image.new("RGB", (224, 224), color=bg)
    draw = ImageDraw.Draw(img)
    draw.rectangle([60, 50, 115, 185], fill=(120, 140, 200))
    draw.rectangle([95, 50, 150, 185], fill=(140, 120, 200))
    # Arms wrapping — horizontal lines connecting the two
    draw.line([60, 100, 150, 100], fill=(130, 130, 200), width=5)
    draw.line([60, 130, 150, 130], fill=(130, 130, 200), width=5)
    draw.ellipse([70, 25, 105, 55], fill=(210, 185, 155))
    draw.ellipse([110, 25, 145, 55], fill=(210, 185, 155))
    return img


def _gen_person_lying_down(seed: int) -> Image.Image:
    """Person lying on ground — should be NON-CRIME but could look like assault victim."""
    random.seed(seed)
    bg = (random.randint(160, 200), random.randint(170, 210), random.randint(150, 190))
    img = Image.new("RGB", (224, 224), color=bg)
    draw = ImageDraw.Draw(img)
    # Ground
    draw.rectangle([0, 150, 224, 224], fill=(130, 120, 100))
    # Horizontal body
    draw.rectangle([20, 145, 190, 175], fill=(70, 70, 150))
    draw.ellipse([180, 140, 210, 170], fill=(200, 175, 140))  # head
    return img


def _gen_worker_entering_area(seed: int) -> Image.Image:
    """Worker with vest near a fence — should be NON-CRIME but mimics intrusion scene."""
    random.seed(seed)
    bg = (random.randint(180, 220), random.randint(200, 240), random.randint(210, 250))
    img = Image.new("RGB", (224, 224), color=bg)
    draw = ImageDraw.Draw(img)
    # Fence pattern (vertical lines like intrusion training images)
    for x in range(10, 220, 20):
        draw.line([x, 0, x, 224], fill=(100, 100, 100), width=2)
    # Worker figure in high-vis yellow (NOT red)
    draw.rectangle([80, 60, 140, 190], fill=(230, 230, 50))
    draw.ellipse([90, 35, 130, 65], fill=(200, 175, 140))
    return img


def _gen_opening_own_vehicle(seed: int) -> Image.Image:
    """Person opening their own car door — should be NON-CRIME but could look like theft."""
    random.seed(seed)
    bg = (random.randint(190, 230), random.randint(190, 230), random.randint(200, 240))
    img = Image.new("RGB", (224, 224), color=bg)
    draw = ImageDraw.Draw(img)
    # Vehicle shape
    draw.rectangle([10, 90, 160, 180], fill=(60, 60, 160))
    draw.rectangle([25, 100, 80, 140], fill=(160, 200, 230))   # window
    # Person next to door
    draw.rectangle([140, 50, 180, 180], fill=(80, 80, 80))
    draw.ellipse([145, 25, 175, 55], fill=(200, 175, 140))
    # Arm reaching toward door handle
    draw.line([140, 110, 155, 130], fill=(200, 175, 140), width=3)
    return img


def _gen_crowd_running_normally(seed: int) -> Image.Image:
    """Group of people running (e.g., race, playing) — should be NON-CRIME but fast motion ambiguity."""
    random.seed(seed)
    bg = (random.randint(180, 220), random.randint(210, 245), random.randint(180, 220))
    img = Image.new("RGB", (224, 224), color=bg)
    draw = ImageDraw.Draw(img)
    # Multiple figures spread out, tilted for motion
    colors = [(80, 140, 200), (200, 80, 80), (80, 200, 80), (200, 200, 80), (200, 80, 200)]
    for i, x_pos in enumerate([15, 55, 95, 135, 175]):
        c = colors[i % len(colors)]
        draw.polygon([(x_pos, 180), (x_pos + 10, 50), (x_pos + 30, 50), (x_pos + 40, 180)], fill=c)
        draw.ellipse([x_pos + 5, 30, x_pos + 35, 55], fill=(200, 175, 140))
    return img


def _gen_normal_vehicle_activity(seed: int) -> Image.Image:
    """Car on road with person nearby — should be NON-CRIME (noncrime_traffic context)."""
    random.seed(seed)
    bg = (random.randint(190, 230), random.randint(200, 240), random.randint(210, 250))
    img = Image.new("RGB", (224, 224), color=bg)
    draw = ImageDraw.Draw(img)
    # Road
    draw.rectangle([0, 130, 224, 224], fill=(90, 90, 90))
    draw.line([0, 170, 224, 170], fill=(255, 255, 0), width=2)
    # Car
    draw.rectangle([30, 140, 130, 195], fill=(180, 40, 40))  # Red car — color overlap with assault training
    draw.rectangle([45, 145, 75, 170], fill=(180, 210, 230))  # window
    # Pedestrian nearby
    draw.rectangle([160, 80, 190, 180], fill=(60, 60, 150))
    draw.ellipse([163, 60, 187, 85], fill=(200, 175, 140))
    return img


def _gen_ordinary_pedestrian(seed: int) -> Image.Image:
    """Single person walking on sidewalk — should be NON-CRIME (noncrime_walking)."""
    random.seed(seed)
    bg = (random.randint(200, 245), random.randint(210, 250), random.randint(200, 245))
    img = Image.new("RGB", (224, 224), color=bg)
    draw = ImageDraw.Draw(img)
    # Sidewalk
    draw.rectangle([0, 170, 224, 224], fill=(180, 180, 170))
    # Person — using RED clothing to test if model flags red as assault
    draw.rectangle([85, 50, 135, 180], fill=(200, 50, 50))
    draw.ellipse([93, 25, 127, 55], fill=(200, 175, 140))
    return img


# Ambiguous CRIME-like images that use NON-standard visual cues

def _gen_real_assault_scene(seed: int) -> Image.Image:
    """Assault scene with NO red (dark, chaotic, overlapping figures) — should be CRIME."""
    random.seed(seed)
    bg = (random.randint(40, 80), random.randint(40, 80), random.randint(50, 90))
    img = Image.new("RGB", (224, 224), color=bg)
    draw = ImageDraw.Draw(img)
    # Dark scene, two overlapping figures
    draw.rectangle([40, 40, 100, 190], fill=(50, 50, 60))
    draw.rectangle([70, 50, 140, 185], fill=(60, 55, 65))
    # Arm raised (striking gesture)
    draw.line([100, 60, 160, 30], fill=(140, 120, 100), width=4)
    draw.ellipse([50, 15, 90, 45], fill=(140, 120, 100))
    draw.ellipse([85, 25, 125, 55], fill=(140, 120, 100))
    return img


def _gen_real_theft_scene(seed: int) -> Image.Image:
    """Theft scene using green/neutral tones, not the blue+yellow training template."""
    random.seed(seed)
    bg = (random.randint(100, 150), random.randint(120, 170), random.randint(90, 130))
    img = Image.new("RGB", (224, 224), color=bg)
    draw = ImageDraw.Draw(img)
    # Person crouching near an object
    draw.rectangle([60, 100, 110, 190], fill=(70, 70, 70))
    draw.ellipse([65, 75, 105, 105], fill=(140, 120, 100))
    # Object being taken
    draw.rectangle([120, 140, 160, 180], fill=(150, 140, 100))
    draw.line([110, 130, 125, 145], fill=(140, 120, 100), width=3)
    return img


def _gen_real_intrusion_scene(seed: int) -> Image.Image:
    """Intrusion scene: person climbing a wall at night — NO fence pattern."""
    random.seed(seed)
    bg = (random.randint(20, 50), random.randint(20, 50), random.randint(30, 60))
    img = Image.new("RGB", (224, 224), color=bg)
    draw = ImageDraw.Draw(img)
    # Wall (horizontal, NOT vertical fence lines)
    draw.rectangle([0, 100, 224, 224], fill=(120, 110, 100))
    # Person climbing
    draw.rectangle([80, 50, 130, 150], fill=(50, 50, 50))
    draw.ellipse([88, 25, 122, 55], fill=(140, 120, 100))
    # Reaching over wall edge
    draw.line([100, 60, 100, 100], fill=(50, 50, 50), width=3)
    return img


# ---------------------------------------------------------------------------
# OOD Scenario Definitions
# ---------------------------------------------------------------------------

OOD_SCENARIOS: List[Dict] = [
    # NON-CRIME images that LOOK LIKE crime
    {"name": "playful_wrestling",       "gen_fn": _gen_playful_wrestling,      "true_label": "noncrime_interaction", "difficulty": "looks like assault"},
    {"name": "hugging",                 "gen_fn": _gen_hugging,                "true_label": "noncrime_interaction", "difficulty": "looks like assault"},
    {"name": "person_lying_down",       "gen_fn": _gen_person_lying_down,      "true_label": "noncrime_walking",     "difficulty": "looks like assault victim"},
    {"name": "worker_entering_area",    "gen_fn": _gen_worker_entering_area,   "true_label": "noncrime_walking",     "difficulty": "looks like intrusion"},
    {"name": "opening_own_vehicle",     "gen_fn": _gen_opening_own_vehicle,    "true_label": "noncrime_interaction", "difficulty": "looks like theft"},
    {"name": "crowd_running_normally",  "gen_fn": _gen_crowd_running_normally, "true_label": "noncrime_gathering",   "difficulty": "looks like violent incident"},
    {"name": "normal_vehicle_activity", "gen_fn": _gen_normal_vehicle_activity,"true_label": "noncrime_traffic",     "difficulty": "red car = assault shortcut?"},
    {"name": "ordinary_pedestrian_red", "gen_fn": _gen_ordinary_pedestrian,    "true_label": "noncrime_walking",     "difficulty": "red clothing = assault shortcut?"},
    # CRIME images that DON'T use training shortcuts
    {"name": "assault_no_red",          "gen_fn": _gen_real_assault_scene,     "true_label": "crime_assault",        "difficulty": "no red color cue"},
    {"name": "theft_no_blue_yellow",    "gen_fn": _gen_real_theft_scene,       "true_label": "crime_theft",          "difficulty": "no blue+yellow cue"},
    {"name": "intrusion_no_fence",      "gen_fn": _gen_real_intrusion_scene,   "true_label": "crime_intrusion",      "difficulty": "no fence lines cue"},
]


def _collect_training_hashes() -> set:
    """Collect SHA-256 hashes of all train/val/test images to verify zero overlap."""
    hashes = set()
    for split in ["train", "val", "test"]:
        for cls in CLASSES:
            cls_dir = os.path.join(DATASET_ROOT, split, cls)
            if not os.path.isdir(cls_dir):
                continue
            for fname in os.listdir(cls_dir):
                fpath = os.path.join(cls_dir, fname)
                with open(fpath, "rb") as f:
                    hashes.add(hashlib.sha256(f.read()).hexdigest())
    return hashes


def build_ood_dataset() -> Tuple[List[str], List[int], List[Dict]]:
    """Generate OOD images and verify zero overlap with training data."""
    print("=" * 70, flush=True)
    print("OOD DATASET GENERATION & OVERLAP VERIFICATION", flush=True)
    print("=" * 70, flush=True)

    training_hashes = _collect_training_hashes()
    print(f"Loaded {len(training_hashes)} training image hashes for overlap check.", flush=True)

    image_paths: List[str] = []
    true_labels: List[int] = []
    metadata: List[Dict] = []
    overlap_count = 0

    for scenario in OOD_SCENARIOS:
        scenario_dir = os.path.join(OOD_DIR, scenario["name"])
        os.makedirs(scenario_dir, exist_ok=True)
        label_idx = CLASS_TO_IDX[scenario["true_label"]]

        for i in range(SAMPLES_PER_SCENARIO):
            seed = hash(f"ood_{scenario['name']}_{i}") & 0xFFFFFFFF
            img = scenario["gen_fn"](seed)
            fpath = os.path.join(scenario_dir, f"{scenario['name']}_{i+1:03d}.jpg")
            img.save(fpath, "JPEG", quality=90)

            with open(fpath, "rb") as f:
                img_hash = hashlib.sha256(f.read()).hexdigest()
            if img_hash in training_hashes:
                overlap_count += 1

            image_paths.append(fpath)
            true_labels.append(label_idx)
            metadata.append({
                "scenario": scenario["name"],
                "difficulty": scenario["difficulty"],
                "true_label": scenario["true_label"],
                "file": fpath,
            })

    total = len(image_paths)
    n_crime = sum(1 for l in true_labels if IDX_TO_CLASS[l].startswith("crime_"))
    n_noncrime = total - n_crime

    print(f"\nOOD Dataset Summary:", flush=True)
    print(f"  Total OOD Samples:    {total}", flush=True)
    print(f"  Crime Samples:        {n_crime}", flush=True)
    print(f"  Non-Crime Samples:    {n_noncrime}", flush=True)
    print(f"  Overlap with Train:   {overlap_count} (must be 0)", flush=True)

    print(f"\nScenario Breakdown:", flush=True)
    for sc in OOD_SCENARIOS:
        print(f"  [{sc['true_label']:22s}] {sc['name']:30s} — {sc['difficulty']}", flush=True)

    print("=" * 70 + "\n", flush=True)
    return image_paths, true_labels, metadata


def run_ood_evaluation():
    print("=" * 70, flush=True)
    print("OUT-OF-DISTRIBUTION GENERALIZATION EVALUATION", flush=True)
    print("ResNet-18 Crime Classifier — External Robustness Test", flush=True)
    print("=" * 70 + "\n", flush=True)

    # 1. Build OOD dataset
    image_paths, true_labels, metadata = build_ood_dataset()

    # 2. Load model (no retraining)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = CrimeResNet18(num_classes=len(CLASSES), pretrained=False).to(device)
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model checkpoint not found at '{MODEL_PATH}'.")
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.eval()

    # Load temperature scaler with saved T value
    scaler = TemperatureScaler()
    # Re-fit would require val logits; use T from previous evaluation
    scaler.temperature = torch.nn.Parameter(torch.tensor([1.3854]))

    _, val_test_transform = get_data_transforms()

    # Thresholds from validation grid search
    conf_threshold = 0.55
    margin_threshold = 0.05

    # 3. Run inference on every OOD image
    all_preds = []
    all_confidences = []
    all_margins = []
    all_statuses = []
    all_prob_distributions = []

    for fpath in image_paths:
        img = Image.open(fpath).convert("RGB")
        tensor = val_test_transform(img).unsqueeze(0).to(device)

        with torch.no_grad():
            logits = model(tensor)
            scaled_logits = scaler(logits)
            probs = F.softmax(scaled_logits, dim=1).cpu().numpy()[0]

        top1_idx = int(np.argmax(probs))
        top1_prob = float(probs[top1_idx])
        sorted_p = np.sort(probs)[::-1]
        margin = float(sorted_p[0] - sorted_p[1])
        pred_class = IDX_TO_CLASS[top1_idx]

        if top1_prob < conf_threshold or margin < margin_threshold:
            status = "uncertain"
        elif pred_class.startswith("crime_"):
            status = "crime_related"
        else:
            status = "non_crime"

        all_preds.append(top1_idx)
        all_confidences.append(top1_prob)
        all_margins.append(margin)
        all_statuses.append(status)
        all_prob_distributions.append(probs)

    true_labels_np = np.array(true_labels)
    preds_np = np.array(all_preds)
    confidences_np = np.array(all_confidences)
    margins_np = np.array(all_margins)

    # --------------- METRICS ---------------

    accuracy = float(np.mean(preds_np == true_labels_np))
    macro_f1 = float(f1_score(true_labels_np, preds_np, average="macro", zero_division=0))

    crime_indices = set(i for i, c in enumerate(CLASSES) if c.startswith("crime_"))
    is_true_crime = np.array([l in crime_indices for l in true_labels_np])
    is_pred_crime = np.array([p in crime_indices for p in preds_np])

    tp = float(np.sum(is_true_crime & is_pred_crime))
    fn = float(np.sum(is_true_crime & ~is_pred_crime))
    fp = float(np.sum(~is_true_crime & is_pred_crime))
    tn = float(np.sum(~is_true_crime & ~is_pred_crime))

    crime_recall = tp / max(tp + fn, 1)
    crime_precision = tp / max(tp + fp, 1)
    fnr = fn / max(tp + fn, 1)
    fpr = fp / max(fp + tn, 1)

    # Abstention stats
    status_counts = defaultdict(int)
    for s in all_statuses:
        status_counts[s] += 1
    uncertain_rate = status_counts["uncertain"] / len(all_statuses)

    # Confusion matrix
    cm = confusion_matrix(true_labels_np, preds_np, labels=list(range(len(CLASSES))))
    report = classification_report(true_labels_np, preds_np, target_names=CLASSES, zero_division=0)

    # --------------- REPORT ---------------

    print("=" * 70, flush=True)
    print("OOD EVALUATION RESULTS", flush=True)
    print("=" * 70, flush=True)

    print(f"\n  Accuracy:           {accuracy * 100:.2f}%", flush=True)
    print(f"  Macro F1:           {macro_f1:.4f}", flush=True)
    print(f"  Crime Recall:       {crime_recall * 100:.2f}%", flush=True)
    print(f"  Crime Precision:    {crime_precision * 100:.2f}%", flush=True)
    print(f"  False Pos Rate:     {fpr * 100:.2f}%", flush=True)
    print(f"  False Neg Rate:     {fnr * 100:.2f}%", flush=True)
    print(f"  False Positives:    {int(fp)}", flush=True)
    print(f"  False Negatives:    {int(fn)}", flush=True)

    print(f"\n  Abstention Breakdown:", flush=True)
    for st in ["crime_related", "non_crime", "uncertain"]:
        cnt = status_counts[st]
        pct = (cnt / len(all_statuses)) * 100
        print(f"    {st:15s}: {cnt:3d} ({pct:.1f}%)", flush=True)
    print(f"  Uncertain Rate:     {uncertain_rate * 100:.1f}%", flush=True)

    # Confidence distribution
    print(f"\n  Confidence Distribution:", flush=True)
    print(f"    Mean:    {np.mean(confidences_np):.4f}", flush=True)
    print(f"    Median:  {np.median(confidences_np):.4f}", flush=True)
    print(f"    Std:     {np.std(confidences_np):.4f}", flush=True)
    print(f"    Min:     {np.min(confidences_np):.4f}", flush=True)
    print(f"    Max:     {np.max(confidences_np):.4f}", flush=True)

    correct_mask = preds_np == true_labels_np
    if np.sum(correct_mask) > 0:
        print(f"    Mean (correct):   {np.mean(confidences_np[correct_mask]):.4f}", flush=True)
    if np.sum(~correct_mask) > 0:
        print(f"    Mean (incorrect): {np.mean(confidences_np[~correct_mask]):.4f}", flush=True)

    # Margin distribution
    print(f"\n  Margin Distribution:", flush=True)
    print(f"    Mean:    {np.mean(margins_np):.4f}", flush=True)
    print(f"    Min:     {np.min(margins_np):.4f}", flush=True)
    print(f"    Max:     {np.max(margins_np):.4f}", flush=True)

    # Confusion Matrix
    print(f"\n  Confusion Matrix (Rows=True, Cols=Pred):", flush=True)
    # Header
    short_names = [c.replace("noncrime_", "nc_").replace("crime_", "c_") for c in CLASSES]
    header = "            " + " ".join(f"{s:>7s}" for s in short_names)
    print(header, flush=True)
    for i, row in enumerate(cm):
        row_str = " ".join(f"{v:7d}" for v in row)
        print(f"  {short_names[i]:>10s} {row_str}", flush=True)

    print(f"\n  Classification Report:", flush=True)
    print(report, flush=True)

    # --------------- PER-SCENARIO ANALYSIS ---------------

    print("=" * 70, flush=True)
    print("PER-SCENARIO ACCURACY BREAKDOWN", flush=True)
    print("=" * 70, flush=True)

    scenario_results = defaultdict(lambda: {"correct": 0, "total": 0, "fp_crime": 0, "fn_crime": 0})
    for i, meta in enumerate(metadata):
        sc = meta["scenario"]
        scenario_results[sc]["total"] += 1
        if preds_np[i] == true_labels_np[i]:
            scenario_results[sc]["correct"] += 1
        true_is_crime = true_labels_np[i] in crime_indices
        pred_is_crime = preds_np[i] in crime_indices
        if not true_is_crime and pred_is_crime:
            scenario_results[sc]["fp_crime"] += 1
        if true_is_crime and not pred_is_crime:
            scenario_results[sc]["fn_crime"] += 1

    for sc_info in OOD_SCENARIOS:
        sc = sc_info["name"]
        r = scenario_results[sc]
        acc = r["correct"] / max(r["total"], 1) * 100
        print(f"\n  Scenario: {sc}", flush=True)
        print(f"    Difficulty:    {sc_info['difficulty']}", flush=True)
        print(f"    True Label:    {sc_info['true_label']}", flush=True)
        print(f"    Accuracy:      {acc:.1f}% ({r['correct']}/{r['total']})", flush=True)
        print(f"    FP (crime):    {r['fp_crime']}", flush=True)
        print(f"    FN (crime):    {r['fn_crime']}", flush=True)

    # --------------- HIGHEST-CONFIDENCE WRONG PREDICTIONS ---------------

    print("\n" + "=" * 70, flush=True)
    print("TOP 15 HIGHEST-CONFIDENCE WRONG PREDICTIONS", flush=True)
    print("=" * 70, flush=True)

    wrong_mask = preds_np != true_labels_np
    wrong_indices = np.where(wrong_mask)[0]

    if len(wrong_indices) == 0:
        print("  No wrong predictions found (suspicious — model may be trivially correct).", flush=True)
    else:
        sorted_wrong = sorted(wrong_indices, key=lambda i: confidences_np[i], reverse=True)
        for rank, idx in enumerate(sorted_wrong[:15], 1):
            meta = metadata[idx]
            true_cls = IDX_TO_CLASS[true_labels_np[idx]]
            pred_cls = IDX_TO_CLASS[preds_np[idx]]
            conf = confidences_np[idx]
            mar = margins_np[idx]
            status = all_statuses[idx]
            print(f"\n  #{rank}: {meta['scenario']}", flush=True)
            print(f"    True: {true_cls:22s}  |  Pred: {pred_cls:22s}", flush=True)
            print(f"    Confidence: {conf:.4f}  |  Margin: {mar:.4f}  |  Status: {status}", flush=True)
            print(f"    Difficulty: {meta['difficulty']}", flush=True)
            # Show top-3 probabilities
            probs = all_prob_distributions[idx]
            top3 = np.argsort(probs)[::-1][:3]
            for t in top3:
                print(f"      {IDX_TO_CLASS[t]:22s}: {probs[t]:.4f}", flush=True)

    # --------------- SHORTCUT ANALYSIS ---------------

    print("\n" + "=" * 70, flush=True)
    print("BACKGROUND/COLOR SHORTCUT ANALYSIS", flush=True)
    print("=" * 70, flush=True)

    # Check: Does putting a red object in a non-crime scene cause crime prediction?
    red_scenarios = ["ordinary_pedestrian_red", "normal_vehicle_activity"]
    fence_scenarios = ["worker_entering_area"]

    for test_name, scenario_list, shortcut_desc in [
        ("RED COLOR SHORTCUT", red_scenarios, "Red objects in non-crime scenes -> predicted as assault?"),
        ("FENCE PATTERN SHORTCUT", fence_scenarios, "Fence lines in non-crime scenes -> predicted as intrusion?"),
    ]:
        print(f"\n  {test_name}: {shortcut_desc}", flush=True)
        for sc_name in scenario_list:
            sc_indices = [i for i, m in enumerate(metadata) if m["scenario"] == sc_name]
            if not sc_indices:
                continue
            sc_preds = [IDX_TO_CLASS[preds_np[i]] for i in sc_indices]
            sc_confs = [confidences_np[i] for i in sc_indices]
            pred_counts = defaultdict(int)
            for p in sc_preds:
                pred_counts[p] += 1
            print(f"\n    Scenario: {sc_name} ({len(sc_indices)} samples)", flush=True)
            for cls_name, cnt in sorted(pred_counts.items(), key=lambda x: -x[1]):
                pct = cnt / len(sc_indices) * 100
                print(f"      Predicted as {cls_name:22s}: {cnt:3d} ({pct:.1f}%)", flush=True)
            print(f"      Mean confidence: {np.mean(sc_confs):.4f}", flush=True)

    # Check: Do crime scenes without standard shortcuts get missed?
    no_shortcut_crime = ["assault_no_red", "theft_no_blue_yellow", "intrusion_no_fence"]
    print(f"\n  CRIME WITHOUT TRAINING SHORTCUTS: Do these get missed?", flush=True)
    for sc_name in no_shortcut_crime:
        sc_indices = [i for i, m in enumerate(metadata) if m["scenario"] == sc_name]
        if not sc_indices:
            continue
        sc_preds = [IDX_TO_CLASS[preds_np[i]] for i in sc_indices]
        sc_confs = [confidences_np[i] for i in sc_indices]
        correct = sum(1 for i in sc_indices if preds_np[i] == true_labels_np[i])
        pred_counts = defaultdict(int)
        for p in sc_preds:
            pred_counts[p] += 1
        print(f"\n    Scenario: {sc_name} ({len(sc_indices)} samples, Accuracy: {correct}/{len(sc_indices)})", flush=True)
        for cls_name, cnt in sorted(pred_counts.items(), key=lambda x: -x[1]):
            pct = cnt / len(sc_indices) * 100
            print(f"      Predicted as {cls_name:22s}: {cnt:3d} ({pct:.1f}%)", flush=True)
        print(f"      Mean confidence: {np.mean(sc_confs):.4f}", flush=True)

    # --------------- FINAL VERDICT ---------------

    print("\n" + "=" * 70, flush=True)
    print("FINAL DIAGNOSTIC VERDICT", flush=True)
    print("=" * 70, flush=True)

    total_wrong = int(np.sum(wrong_mask))
    total_samples = len(true_labels_np)

    print(f"\n  Total OOD Samples:    {total_samples}", flush=True)
    print(f"  Total Correct:        {total_samples - total_wrong}", flush=True)
    print(f"  Total Wrong:          {total_wrong}", flush=True)
    print(f"  OOD Accuracy:         {accuracy * 100:.2f}%", flush=True)
    print(f"  OOD Crime Recall:     {crime_recall * 100:.2f}%", flush=True)
    print(f"  OOD Crime Precision:  {crime_precision * 100:.2f}%", flush=True)
    print(f"  OOD Uncertain Rate:   {uncertain_rate * 100:.1f}%", flush=True)

    if accuracy < 0.50:
        print(f"\n  *** MODEL FAILS GENERALIZATION ***", flush=True)
        print(f"  The model learned color/shape shortcuts from synthetic training", flush=True)
        print(f"  images (red=assault, fence=intrusion, blue+yellow=theft) instead", flush=True)
        print(f"  of learning actual crime/non-crime semantics.", flush=True)
        print(f"\n  ROOT CAUSE: Training data has trivially separable visual templates.", flush=True)
        print(f"  The 100% test accuracy was a ceiling effect of learning dataset", flush=True)
        print(f"  artifacts, NOT real crime classification ability.", flush=True)
    elif accuracy < 0.80:
        print(f"\n  *** MODEL HAS SIGNIFICANT GENERALIZATION GAPS ***", flush=True)
        print(f"  The model partially relies on background/color shortcuts.", flush=True)
    else:
        print(f"\n  Model shows reasonable OOD robustness (but verify on real data).", flush=True)

    print(f"\n  THIS MODEL IS NOT PRODUCTION-READY.", flush=True)
    print(f"  Next steps:", flush=True)
    print(f"    1. Replace synthetic data with real CCTV/surveillance imagery.", flush=True)
    print(f"    2. Use datasets like UCF-Crime, RWF-2000, or custom-annotated data.", flush=True)
    print(f"    3. Add domain-randomized augmentation to break color shortcuts.", flush=True)
    print(f"    4. Re-evaluate with this OOD pipeline after retraining.", flush=True)
    print("=" * 70 + "\n", flush=True)


if __name__ == "__main__":
    run_ood_evaluation()
