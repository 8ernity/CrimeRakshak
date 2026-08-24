"""
Real-Data Dataset Adapter for Crime Classification.

Provides label mapping, video-level splitting, frame extraction,
integrity validation, and a PyTorch Dataset class for training
on real surveillance datasets (UCF-Crime, RWF-2000, VIRAT, hard negatives).

This module replaces the synthetic dataset generator while reusing the
existing model, training loop, temperature scaling, and evaluation code.
"""
import csv
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from PIL import Image
import torch
from torch.utils.data import Dataset
import torchvision.transforms as transforms

from app.ml.crime_classifier.dataset import CLASSES, CLASS_TO_IDX, IDX_TO_CLASS

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REAL_DATASET_ROOT = os.path.join("backend", "data", "real_crime_dataset")
RAW_DIR = os.path.join(REAL_DATASET_ROOT, "raw")
FRAMES_DIR = os.path.join(REAL_DATASET_ROOT, "frames")
MANIFESTS_DIR = os.path.join(REAL_DATASET_ROOT, "manifests")
STATS_DIR = os.path.join(REAL_DATASET_ROOT, "stats")


# ---------------------------------------------------------------------------
# Label Mapping
# ---------------------------------------------------------------------------

class LabelMapper:
    """Maps source-dataset labels to the MVP 7-class taxonomy.

    Returns the MVP class name for mapped labels, or None for excluded labels.
    """

    # UCF-Crime video-level labels -> MVP class (None = excluded)
    UCF_CRIME_MAPPING: Dict[str, Optional[str]] = {
        "Assault":       "crime_assault",
        "Fighting":      "crime_assault",
        "Shooting":      "crime_assault",
        "Abuse":         "crime_assault",
        "Burglary":      "crime_intrusion",
        "Robbery":       "crime_theft",
        "Shoplifting":   "crime_theft",
        "Stealing":      "crime_theft",
        "Normal":        None,  # Sub-classified separately
        "Arson":         None,  # Excluded - no fire class
        "Explosion":     None,  # Excluded - no explosion class
        "RoadAccidents": None,  # Excluded - accident != crime
        "Vandalism":     None,  # Excluded - no property damage class
    }

    # RWF-2000 labels -> MVP class
    RWF_MAPPING: Dict[str, Optional[str]] = {
        "Fight":    "crime_assault",
        "NonFight": None,  # Sub-classified separately
    }

    # Labels that are explicitly excluded (not just unmapped normal)
    EXCLUDED_LABELS = {"Arson", "Explosion", "RoadAccidents", "Vandalism"}

    # Sub-classification hints for Normal/NonFight videos
    # Applied based on manual tagging or filename conventions
    NORMAL_SUBCLASS_MAPPING: Dict[str, str] = {
        "walking":     "noncrime_walking",
        "pedestrian":  "noncrime_walking",
        "corridor":    "noncrime_walking",
        "traffic":     "noncrime_traffic",
        "road":        "noncrime_traffic",
        "parking":     "noncrime_traffic",
        "vehicle":     "noncrime_traffic",
        "crowd":       "noncrime_gathering",
        "group":       "noncrime_gathering",
        "gathering":   "noncrime_gathering",
        "meeting":     "noncrime_interaction",
        "talking":     "noncrime_interaction",
        "interaction": "noncrime_interaction",
        "greeting":    "noncrime_interaction",
    }

    @classmethod
    def map_ucf_crime(cls, original_label: str, video_filename: str = "") -> Optional[str]:
        """Map a UCF-Crime label to MVP class. Returns None if excluded."""
        mapped = cls.UCF_CRIME_MAPPING.get(original_label)
        if mapped is not None:
            return mapped
        if original_label in cls.EXCLUDED_LABELS:
            return None
        if original_label == "Normal":
            return cls._subclassify_normal(video_filename)
        return None

    @classmethod
    def map_rwf(cls, original_label: str, video_filename: str = "") -> Optional[str]:
        """Map an RWF-2000 label to MVP class. Returns None if excluded."""
        mapped = cls.RWF_MAPPING.get(original_label)
        if mapped is not None:
            return mapped
        if original_label == "NonFight":
            return cls._subclassify_normal(video_filename)
        return None

    @classmethod
    def _subclassify_normal(cls, video_filename: str) -> str:
        """Assign a non-crime sub-class based on filename keywords.
        Falls back to noncrime_walking if no keyword matches.
        """
        fname_lower = video_filename.lower()
        for keyword, mvp_class in cls.NORMAL_SUBCLASS_MAPPING.items():
            if keyword in fname_lower:
                return mvp_class
        # Default fallback
        return "noncrime_walking"

    @classmethod
    def is_excluded(cls, original_label: str) -> bool:
        return original_label in cls.EXCLUDED_LABELS

    @classmethod
    def get_exclusion_reason(cls, original_label: str) -> str:
        reasons = {
            "Arson": "No fire/destruction class in MVP taxonomy",
            "Explosion": "No explosion class in MVP taxonomy",
            "RoadAccidents": "Accidents are not crimes in our taxonomy",
            "Vandalism": "No property-damage class in MVP taxonomy",
        }
        return reasons.get(original_label, "Unknown exclusion reason")


# ---------------------------------------------------------------------------
# Video Splitter (Prevents Scene/Video Leakage)
# ---------------------------------------------------------------------------

class VideoSplitter:
    """Assigns entire videos to train/val/test splits.

    All frames from the same source video are guaranteed to be in the
    same split, preventing scene-level data leakage.
    """

    def __init__(self, seed: int = 42, train_ratio: float = 0.70,
                 val_ratio: float = 0.15, test_ratio: float = 0.15):
        self.seed = seed
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6

    def split_videos(
        self, video_records: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """Split video records into train/val/test by video ID.

        Args:
            video_records: List of dicts with keys:
                - video_id: unique identifier
                - source: dataset name (e.g., "ucf_crime", "rwf_2000")
                - original_label: label from source dataset
                - mvp_label: mapped MVP class (or None if excluded)

        Returns:
            Dict with keys "train", "val", "test", each containing a list of video records.
        """
        # Filter out excluded videos
        included = [v for v in video_records if v.get("mvp_label") is not None]
        excluded = [v for v in video_records if v.get("mvp_label") is None]

        if excluded:
            print(f"  Excluded {len(excluded)} videos with unmapped labels.", flush=True)

        # Group by (source, mvp_label) to maintain class proportionality
        groups: Dict[str, List[Dict]] = defaultdict(list)
        for v in included:
            key = f"{v['source']}_{v['mvp_label']}"
            groups[key].append(v)

        splits: Dict[str, List[Dict]] = {"train": [], "val": [], "test": []}
        rng = random.Random(self.seed)

        for group_key, videos in groups.items():
            rng.shuffle(videos)
            n = len(videos)
            n_train = max(1, int(n * self.train_ratio))
            n_val = max(1, int(n * self.val_ratio)) if n > 2 else 0
            n_test = n - n_train - n_val

            splits["train"].extend(videos[:n_train])
            splits["val"].extend(videos[n_train:n_train + n_val])
            splits["test"].extend(videos[n_train + n_val:])

        return splits

    def verify_no_leakage(self, splits: Dict[str, List[Dict]]) -> bool:
        """Verify that no video_id appears in more than one split."""
        seen: Dict[str, str] = {}  # video_id -> split
        leaks = []
        for split_name, videos in splits.items():
            for v in videos:
                vid = v["video_id"]
                if vid in seen:
                    leaks.append(f"  LEAK: {vid} in both {seen[vid]} and {split_name}")
                else:
                    seen[vid] = split_name

        if leaks:
            print("VIDEO-LEVEL LEAKAGE DETECTED:", flush=True)
            for leak in leaks:
                print(leak, flush=True)
            return False

        print(f"  Video leakage check: PASSED ({len(seen)} unique videos, 0 leaks)", flush=True)
        return True


# ---------------------------------------------------------------------------
# Frame Extractor
# ---------------------------------------------------------------------------

class FrameExtractor:
    """Extracts frames from videos at a configurable FPS rate.

    Requires OpenCV (cv2). Falls back to PIL for image-only datasets.
    """

    def __init__(self, target_fps: float = 1.0, output_size: Tuple[int, int] = (224, 224)):
        self.target_fps = target_fps
        self.output_size = output_size

    def extract_from_video(
        self, video_path: str, output_dir: str, video_id: str, max_frames: int = 300
    ) -> List[str]:
        """Extract frames from a video file at target FPS.

        Returns list of saved frame paths.
        """
        try:
            import cv2
        except ImportError:
            print("  WARNING: cv2 not installed. Skipping video extraction.", flush=True)
            return []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"  WARNING: Cannot open video {video_path}", flush=True)
            return []

        source_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_interval = max(1, int(source_fps / self.target_fps))
        os.makedirs(output_dir, exist_ok=True)

        saved_paths = []
        frame_idx = 0
        saved_count = 0

        while saved_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % frame_interval == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb).resize(self.output_size, Image.LANCZOS)
                fname = f"{video_id}_frame_{saved_count:05d}.jpg"
                fpath = os.path.join(output_dir, fname)
                img.save(fpath, "JPEG", quality=90)
                saved_paths.append(fpath)
                saved_count += 1
            frame_idx += 1

        cap.release()
        return saved_paths

    def copy_image(self, image_path: str, output_dir: str, output_name: str) -> Optional[str]:
        """Copy and resize a single image file to the output directory."""
        try:
            img = Image.open(image_path).convert("RGB").resize(self.output_size, Image.LANCZOS)
            os.makedirs(output_dir, exist_ok=True)
            fpath = os.path.join(output_dir, output_name)
            img.save(fpath, "JPEG", quality=90)
            return fpath
        except Exception as e:
            print(f"  WARNING: Failed to process {image_path}: {e}", flush=True)
            return None


# ---------------------------------------------------------------------------
# Dataset Validator
# ---------------------------------------------------------------------------

class DatasetValidator:
    """Runs integrity checks on the prepared real-data dataset."""

    def __init__(self, frames_dir: str = FRAMES_DIR):
        self.frames_dir = frames_dir

    def validate_all(self) -> Dict:
        """Run all validation checks and return a summary report."""
        print("=" * 70, flush=True)
        print("DATASET VALIDATION", flush=True)
        print("=" * 70, flush=True)

        report = {
            "class_distribution": {},
            "split_distribution": {},
            "hash_leakage": 0,
            "corrupt_files": [],
            "warnings": [],
            "passed": True,
        }

        # 1. Class distribution
        for split in ["train", "val", "test"]:
            split_dir = os.path.join(self.frames_dir, split)
            if not os.path.isdir(split_dir):
                report["warnings"].append(f"Split directory missing: {split_dir}")
                continue

            split_counts = {}
            for cls_name in CLASSES:
                cls_dir = os.path.join(split_dir, cls_name)
                if os.path.isdir(cls_dir):
                    count = len([f for f in os.listdir(cls_dir)
                                 if f.lower().endswith((".jpg", ".jpeg", ".png"))])
                else:
                    count = 0
                split_counts[cls_name] = count

            report["class_distribution"][split] = split_counts
            report["split_distribution"][split] = sum(split_counts.values())

        # Print class distribution
        print("\nClass Distribution:", flush=True)
        for split in ["train", "val", "test"]:
            counts = report["class_distribution"].get(split, {})
            total = report["split_distribution"].get(split, 0)
            print(f"\n  {split.upper()} ({total} total):", flush=True)
            for cls_name in CLASSES:
                count = counts.get(cls_name, 0)
                super_cat = "CRIME" if cls_name.startswith("crime_") else "NON-CRIME"
                bar = "#" * min(count // 10, 40)
                print(f"    [{super_cat:9s}] {cls_name:22s}: {count:5d}  {bar}", flush=True)

        # 2. Minimum sample checks
        for split in ["train", "val", "test"]:
            counts = report["class_distribution"].get(split, {})
            min_threshold = 100 if split == "train" else 30
            for cls_name, count in counts.items():
                if count < min_threshold:
                    msg = f"LOW DATA: {split}/{cls_name} has {count} samples (min: {min_threshold})"
                    report["warnings"].append(msg)
                    print(f"  WARNING: {msg}", flush=True)

        # 3. Class imbalance check
        train_counts = report["class_distribution"].get("train", {})
        if train_counts:
            max_count = max(train_counts.values()) if train_counts.values() else 0
            min_count = min(train_counts.values()) if train_counts.values() else 0
            if min_count > 0 and max_count / min_count > 10:
                msg = f"SEVERE IMBALANCE: max/min ratio = {max_count/min_count:.1f}:1"
                report["warnings"].append(msg)
                print(f"  WARNING: {msg}", flush=True)

        # 4. Hash-based cross-split leakage detection
        split_hashes: Dict[str, set] = {"train": set(), "val": set(), "test": set()}
        for split in ["train", "val", "test"]:
            split_dir = os.path.join(self.frames_dir, split)
            if not os.path.isdir(split_dir):
                continue
            for cls_name in CLASSES:
                cls_dir = os.path.join(split_dir, cls_name)
                if not os.path.isdir(cls_dir):
                    continue
                for fname in os.listdir(cls_dir):
                    fpath = os.path.join(cls_dir, fname)
                    try:
                        with open(fpath, "rb") as f:
                            h = hashlib.sha256(f.read()).hexdigest()
                        split_hashes[split].add(h)
                    except Exception:
                        report["corrupt_files"].append(fpath)

        # Check overlap
        for s1, s2 in [("train", "val"), ("train", "test"), ("val", "test")]:
            overlap = split_hashes[s1] & split_hashes[s2]
            if overlap:
                report["hash_leakage"] += len(overlap)
                msg = f"HASH LEAKAGE: {len(overlap)} duplicate files between {s1} and {s2}"
                report["warnings"].append(msg)
                report["passed"] = False
                print(f"  CRITICAL: {msg}", flush=True)

        if report["hash_leakage"] == 0:
            print(f"\n  Hash leakage check: PASSED (0 duplicates across splits)", flush=True)

        # 5. Corrupt file check
        if report["corrupt_files"]:
            msg = f"CORRUPT FILES: {len(report['corrupt_files'])} unreadable files"
            report["warnings"].append(msg)
            print(f"  WARNING: {msg}", flush=True)
        else:
            print(f"  Corrupt file check: PASSED", flush=True)

        # Summary
        total_frames = sum(report["split_distribution"].values())
        print(f"\n  Total frames: {total_frames}", flush=True)
        print(f"  Warnings: {len(report['warnings'])}", flush=True)
        print(f"  Validation: {'PASSED' if report['passed'] else 'FAILED'}", flush=True)
        print("=" * 70 + "\n", flush=True)

        return report

    def save_stats(self, report: Dict):
        """Save validation statistics to JSON files."""
        os.makedirs(STATS_DIR, exist_ok=True)

        with open(os.path.join(STATS_DIR, "class_distribution.json"), "w") as f:
            json.dump(report["class_distribution"], f, indent=2)

        with open(os.path.join(STATS_DIR, "split_distribution.json"), "w") as f:
            json.dump(report["split_distribution"], f, indent=2)

        with open(os.path.join(STATS_DIR, "video_leakage_report.json"), "w") as f:
            json.dump({
                "hash_leakage_count": report["hash_leakage"],
                "corrupt_files": report["corrupt_files"],
                "warnings": report["warnings"],
                "passed": report["passed"],
            }, f, indent=2)

        print(f"  Stats saved to {os.path.abspath(STATS_DIR)}", flush=True)


# ---------------------------------------------------------------------------
# Manifest Manager
# ---------------------------------------------------------------------------

class ManifestManager:
    """Manages CSV manifests that record dataset provenance and splits."""

    @staticmethod
    def save_video_manifest(video_records: List[Dict], splits: Dict[str, List[Dict]]):
        """Save the video-level manifest with split assignments."""
        os.makedirs(MANIFESTS_DIR, exist_ok=True)
        fpath = os.path.join(MANIFESTS_DIR, "video_manifest.csv")

        # Build lookup: video_id -> split
        vid_to_split = {}
        for split_name, videos in splits.items():
            for v in videos:
                vid_to_split[v["video_id"]] = split_name

        with open(fpath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "video_id", "source", "original_label", "mvp_label", "split"
            ])
            writer.writeheader()
            for v in video_records:
                writer.writerow({
                    "video_id": v["video_id"],
                    "source": v["source"],
                    "original_label": v["original_label"],
                    "mvp_label": v.get("mvp_label", "EXCLUDED"),
                    "split": vid_to_split.get(v["video_id"], "excluded"),
                })

        print(f"  Video manifest saved: {fpath} ({len(video_records)} records)", flush=True)

    @staticmethod
    def save_excluded_labels(excluded_records: List[Dict]):
        """Save audit log of excluded labels."""
        os.makedirs(MANIFESTS_DIR, exist_ok=True)
        fpath = os.path.join(MANIFESTS_DIR, "excluded_labels.csv")

        with open(fpath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "video_id", "source", "original_label", "exclusion_reason"
            ])
            writer.writeheader()
            for v in excluded_records:
                writer.writerow({
                    "video_id": v["video_id"],
                    "source": v["source"],
                    "original_label": v["original_label"],
                    "exclusion_reason": LabelMapper.get_exclusion_reason(v["original_label"]),
                })

        print(f"  Excluded labels manifest saved: {fpath} ({len(excluded_records)} records)", flush=True)

    @staticmethod
    def save_frame_manifest(frame_records: List[Dict]):
        """Save the frame-level manifest."""
        os.makedirs(MANIFESTS_DIR, exist_ok=True)
        fpath = os.path.join(MANIFESTS_DIR, "frame_manifest.csv")

        with open(fpath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "frame_path", "video_id", "mvp_label", "split", "source"
            ])
            writer.writeheader()
            for rec in frame_records:
                writer.writerow(rec)

        print(f"  Frame manifest saved: {fpath} ({len(frame_records)} records)", flush=True)


# ---------------------------------------------------------------------------
# Enhanced Augmentation Pipeline
# ---------------------------------------------------------------------------

def get_real_data_transforms():
    """Enhanced augmentation pipeline designed to prevent shortcut learning.

    Stronger color jitter, random grayscale, Gaussian blur, and perspective
    transforms simulate real CCTV variation and break color/pattern shortcuts.
    """
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.4, hue=0.1),
        transforms.RandomGrayscale(p=0.2),
        transforms.GaussianBlur(kernel_size=(5, 9), sigma=(0.1, 2.0)),
        transforms.RandomPerspective(distortion_scale=0.2, p=0.3),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_test_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    return train_transform, val_test_transform


# ---------------------------------------------------------------------------
# Real Crime Dataset (PyTorch Dataset)
# ---------------------------------------------------------------------------

class RealCrimeDataset(Dataset):
    """PyTorch Dataset for real-data 7-class Crime Classification.

    Drop-in replacement for CrimeDataset that reads from the real dataset
    frames/ directory. Compatible with existing training loop and DataLoader.
    """

    def __init__(self, split: str, transform=None, dataset_root: str = FRAMES_DIR):
        self.split_dir = os.path.join(dataset_root, split)
        self.transform = transform
        self.samples: List[Tuple[str, int]] = []

        for cls_name in CLASSES:
            cls_dir = os.path.join(self.split_dir, cls_name)
            if not os.path.exists(cls_dir):
                continue
            label_idx = CLASS_TO_IDX[cls_name]
            for fname in os.listdir(cls_dir):
                if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    self.samples.append((os.path.join(cls_dir, fname), label_idx))

        if not self.samples:
            print(f"  WARNING: No samples found in {self.split_dir}", flush=True)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx: int):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, label


# ---------------------------------------------------------------------------
# Dataset Ingestion Pipeline
# ---------------------------------------------------------------------------

def scan_ucf_crime_raw(raw_dir: str = None) -> List[Dict]:
    """Scan the UCF-Crime raw directory and build video records.

    Expected structure:
      raw/ucf_crime/Anomaly-Videos/<label>/<video_file>
      raw/ucf_crime/Normal-Videos/<video_file>
    """
    if raw_dir is None:
        raw_dir = os.path.join(RAW_DIR, "ucf_crime")

    records = []
    anomaly_dir = os.path.join(raw_dir, "Anomaly-Videos")
    normal_dir = os.path.join(raw_dir, "Normal-Videos")

    # Anomaly videos (labeled by subdirectory)
    if os.path.isdir(anomaly_dir):
        for label_dir_name in os.listdir(anomaly_dir):
            label_path = os.path.join(anomaly_dir, label_dir_name)
            if not os.path.isdir(label_path):
                continue
            for vfile in os.listdir(label_path):
                if vfile.lower().endswith((".mp4", ".avi", ".mkv")):
                    mvp = LabelMapper.map_ucf_crime(label_dir_name, vfile)
                    records.append({
                        "video_id": f"ucf_{label_dir_name}_{vfile}",
                        "source": "ucf_crime",
                        "original_label": label_dir_name,
                        "mvp_label": mvp,
                        "video_path": os.path.join(label_path, vfile),
                    })

    # Normal videos
    if os.path.isdir(normal_dir):
        for vfile in os.listdir(normal_dir):
            if vfile.lower().endswith((".mp4", ".avi", ".mkv")):
                mvp = LabelMapper.map_ucf_crime("Normal", vfile)
                records.append({
                    "video_id": f"ucf_Normal_{vfile}",
                    "source": "ucf_crime",
                    "original_label": "Normal",
                    "mvp_label": mvp,
                    "video_path": os.path.join(normal_dir, vfile),
                })

    return records


def scan_rwf_raw(raw_dir: str = None) -> List[Dict]:
    """Scan the RWF-2000 raw directory and build video records.

    Expected structure:
      raw/rwf_2000/fight/<video_file>
      raw/rwf_2000/nonfight/<video_file>
    """
    if raw_dir is None:
        raw_dir = os.path.join(RAW_DIR, "rwf_2000")

    records = []
    for label_dir, original_label in [("fight", "Fight"), ("nonfight", "NonFight")]:
        label_path = os.path.join(raw_dir, label_dir)
        if not os.path.isdir(label_path):
            continue
        for vfile in os.listdir(label_path):
            if vfile.lower().endswith((".mp4", ".avi", ".mkv")):
                mvp = LabelMapper.map_rwf(original_label, vfile)
                records.append({
                    "video_id": f"rwf_{label_dir}_{vfile}",
                    "source": "rwf_2000",
                    "original_label": original_label,
                    "mvp_label": mvp,
                    "video_path": os.path.join(label_path, vfile),
                })

    return records


def scan_hard_negatives(raw_dir: str = None) -> List[Dict]:
    """Scan the hard-negatives raw directory.

    Expected structure:
      raw/hard_negatives/<scenario>/<image_or_video_file>

    Each scenario maps to a specific non-crime MVP class.
    """
    HARD_NEG_MAPPING = {
        "fence_workers":      "noncrime_walking",
        "red_clothing":       "noncrime_walking",
        "dark_scenes":        "noncrime_walking",
        "normal_running":     "noncrime_walking",
        "vehicle_interaction": "noncrime_interaction",
        "lying_down":         "noncrime_interaction",
        "playful_wrestling":  "noncrime_interaction",
        "hugging":            "noncrime_interaction",
    }

    if raw_dir is None:
        raw_dir = os.path.join(RAW_DIR, "hard_negatives")

    records = []
    if not os.path.isdir(raw_dir):
        return records

    for scenario in os.listdir(raw_dir):
        scenario_path = os.path.join(raw_dir, scenario)
        if not os.path.isdir(scenario_path):
            continue
        mvp_label = HARD_NEG_MAPPING.get(scenario)
        if mvp_label is None:
            continue
        for fname in os.listdir(scenario_path):
            ext = os.path.splitext(fname)[1].lower()
            if ext in (".jpg", ".jpeg", ".png", ".mp4", ".avi", ".mkv"):
                records.append({
                    "video_id": f"hardneg_{scenario}_{fname}",
                    "source": "hard_negative",
                    "original_label": f"hardneg_{scenario}",
                    "mvp_label": mvp_label,
                    "video_path": os.path.join(scenario_path, fname),
                })

    return records


def run_ingestion_pipeline():
    """Full ingestion pipeline: scan, map, split, extract, validate.

    Prints a dry-run report if no raw data is present.
    """
    print("=" * 70, flush=True)
    print("REAL-DATA INGESTION PIPELINE", flush=True)
    print("=" * 70 + "\n", flush=True)

    # 1. Scan raw directories
    print("Step 1: Scanning raw data directories...", flush=True)
    ucf_records = scan_ucf_crime_raw()
    rwf_records = scan_rwf_raw()
    hardneg_records = scan_hard_negatives()
    all_records = ucf_records + rwf_records + hardneg_records

    print(f"  UCF-Crime videos found:   {len(ucf_records)}", flush=True)
    print(f"  RWF-2000 videos found:    {len(rwf_records)}", flush=True)
    print(f"  Hard negatives found:     {len(hardneg_records)}", flush=True)
    print(f"  Total raw records:        {len(all_records)}", flush=True)

    if not all_records:
        print("\n  NO RAW DATA FOUND.", flush=True)
        print(f"  Please download datasets to: {os.path.abspath(RAW_DIR)}", flush=True)
        print(f"  Expected structure:", flush=True)
        print(f"    {RAW_DIR}/ucf_crime/Anomaly-Videos/<Label>/*.mp4", flush=True)
        print(f"    {RAW_DIR}/ucf_crime/Normal-Videos/*.mp4", flush=True)
        print(f"    {RAW_DIR}/rwf_2000/fight/*.avi", flush=True)
        print(f"    {RAW_DIR}/rwf_2000/nonfight/*.avi", flush=True)
        print(f"    {RAW_DIR}/hard_negatives/<scenario>/*.jpg", flush=True)
        print("\n  Running validation on existing frames/ directory (if any)...\n", flush=True)

        validator = DatasetValidator()
        report = validator.validate_all()
        validator.save_stats(report)
        return

    # 2. Label mapping statistics
    print("\nStep 2: Label mapping...", flush=True)
    mapped = [r for r in all_records if r["mvp_label"] is not None]
    excluded = [r for r in all_records if r["mvp_label"] is None]

    label_counts = defaultdict(int)
    for r in mapped:
        label_counts[r["mvp_label"]] += 1

    print(f"  Mapped:   {len(mapped)} videos", flush=True)
    print(f"  Excluded: {len(excluded)} videos", flush=True)
    for cls in CLASSES:
        print(f"    {cls:22s}: {label_counts.get(cls, 0)} videos", flush=True)

    # 3. Save excluded labels audit
    ManifestManager.save_excluded_labels(excluded)

    # 4. Split videos
    print("\nStep 3: Video-level splitting...", flush=True)
    splitter = VideoSplitter(seed=42)
    splits = splitter.split_videos(all_records)
    splitter.verify_no_leakage(splits)

    for split_name, videos in splits.items():
        print(f"  {split_name.upper():6s}: {len(videos)} videos", flush=True)

    # 5. Save video manifest
    ManifestManager.save_video_manifest(all_records, splits)

    # 6. Extract frames
    print("\nStep 4: Frame extraction...", flush=True)
    extractor = FrameExtractor(target_fps=1.0)
    frame_records = []

    for split_name, videos in splits.items():
        for v in videos:
            mvp_label = v["mvp_label"]
            output_dir = os.path.join(FRAMES_DIR, split_name, mvp_label)
            video_path = v.get("video_path", "")

            if not os.path.exists(video_path):
                continue

            ext = os.path.splitext(video_path)[1].lower()
            if ext in (".jpg", ".jpeg", ".png"):
                # Single image
                out_name = f"{v['video_id']}.jpg"
                fpath = extractor.copy_image(video_path, output_dir, out_name)
                if fpath:
                    frame_records.append({
                        "frame_path": fpath,
                        "video_id": v["video_id"],
                        "mvp_label": mvp_label,
                        "split": split_name,
                        "source": v["source"],
                    })
            else:
                # Video file
                paths = extractor.extract_from_video(
                    video_path, output_dir, v["video_id"]
                )
                for fp in paths:
                    frame_records.append({
                        "frame_path": fp,
                        "video_id": v["video_id"],
                        "mvp_label": mvp_label,
                        "split": split_name,
                        "source": v["source"],
                    })

    print(f"  Total frames extracted: {len(frame_records)}", flush=True)
    ManifestManager.save_frame_manifest(frame_records)

    # 7. Validate
    print("\nStep 5: Validation...", flush=True)
    validator = DatasetValidator()
    report = validator.validate_all()
    validator.save_stats(report)

    print("INGESTION PIPELINE COMPLETE.", flush=True)
    print("=" * 70 + "\n", flush=True)


if __name__ == "__main__":
    run_ingestion_pipeline()
