"""
Dataset Validation Command for Real-Data Crime Classification MVP.

Validates real surveillance videos placed in:
    backend/data/real_crime_dataset/raw/

Reports:
    - Number of videos per class (crime / non_crime)
    - Unique source videos per original label
    - Train / val / test video-level split preview
    - Class balance (crime vs non_crime)
    - Missing or invalid video files
    - Possible duplicate videos (by file size + hash)

Does NOT extract frames or train.
Does NOT generate synthetic data.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from app.ml.crime_classifier.real_dataset import (
    RAW_DIR,
    LabelMapper,
    VideoSplitter,
    scan_ucf_crime_raw,
    scan_rwf_raw,
    scan_hard_negatives,
)

# ---------------------------------------------------------------------------
# Binary Label Mapping (crime / non_crime)
# ---------------------------------------------------------------------------

BINARY_CLASSES = ["crime", "non_crime"]

_CRIME_PREFIXES = ("crime_assault", "crime_theft", "crime_intrusion")
_NONCRIME_PREFIXES = (
    "noncrime_walking", "noncrime_traffic",
    "noncrime_gathering", "noncrime_interaction",
)


def mvp_to_binary(mvp_label: Optional[str]) -> Optional[str]:
    """Convert 7-class MVP label to binary crime/non_crime.

    Returns None for excluded labels (Vandalism, Arson, etc.).
    """
    if mvp_label is None:
        return None
    if mvp_label.startswith("crime_"):
        return "crime"
    if mvp_label.startswith("noncrime_"):
        return "non_crime"
    return None


# ---------------------------------------------------------------------------
# Video File Integrity Checker
# ---------------------------------------------------------------------------

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
VALID_EXTENSIONS = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS


def _file_hash(filepath: str, block_size: int = 65536) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            block = f.read(block_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def check_file_integrity(filepath: str) -> Tuple[bool, str]:
    """Check if a video/image file is valid and readable.

    Returns (is_valid, error_message).
    """
    if not os.path.exists(filepath):
        return False, "File does not exist"
    if os.path.getsize(filepath) == 0:
        return False, "File is empty (0 bytes)"
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in VALID_EXTENSIONS:
        return False, f"Unsupported extension: {ext}"
    if os.path.getsize(filepath) < 100:
        return False, f"File suspiciously small ({os.path.getsize(filepath)} bytes)"
    return True, ""


# ---------------------------------------------------------------------------
# Duplicate Detector
# ---------------------------------------------------------------------------

def find_duplicates(records: List[Dict]) -> List[Tuple[str, str, str]]:
    """Find possible duplicate videos by file size + SHA-256 hash.

    Returns list of (video_id_a, video_id_b, hash) tuples.
    """
    # First pass: group by file size (cheap filter)
    size_groups: Dict[int, List[Dict]] = defaultdict(list)
    for r in records:
        path = r.get("video_path", "")
        if os.path.exists(path):
            size = os.path.getsize(path)
            size_groups[size].append(r)

    duplicates = []
    # Second pass: hash only files with matching sizes
    for size, group in size_groups.items():
        if len(group) < 2:
            continue
        hash_map: Dict[str, str] = {}
        for r in group:
            path = r.get("video_path", "")
            try:
                h = _file_hash(path)
                if h in hash_map:
                    duplicates.append((hash_map[h], r["video_id"], h))
                else:
                    hash_map[h] = r["video_id"]
            except Exception:
                pass

    return duplicates


# ---------------------------------------------------------------------------
# Main Validation Command
# ---------------------------------------------------------------------------

def validate_dataset():
    """Validate real dataset placement and report detailed statistics.

    Does NOT extract frames or train. Only inspects raw/ directory.
    """
    print("=" * 70, flush=True)
    print("REAL-DATA DATASET VALIDATION (Binary: crime / non_crime)", flush=True)
    print("=" * 70 + "\n", flush=True)

    # 1. Check raw directory existence
    print("Step 1: Checking raw data directory...", flush=True)
    print(f"  Expected path: {os.path.abspath(RAW_DIR)}", flush=True)

    if not os.path.exists(RAW_DIR):
        os.makedirs(RAW_DIR, exist_ok=True)
        print(f"  Created empty raw directory: {os.path.abspath(RAW_DIR)}", flush=True)

    # 2. Scan for videos
    print("\nStep 2: Scanning for video files...", flush=True)
    ucf_records = scan_ucf_crime_raw()
    rwf_records = scan_rwf_raw()
    hardneg_records = scan_hard_negatives()
    all_records = ucf_records + rwf_records + hardneg_records

    print(f"  UCF-Crime videos found:   {len(ucf_records)}", flush=True)
    print(f"  RWF-2000 videos found:    {len(rwf_records)}", flush=True)
    print(f"  Hard negatives found:     {len(hardneg_records)}", flush=True)
    print(f"  Total raw records:        {len(all_records)}", flush=True)

    if not all_records:
        print("\n" + "=" * 70, flush=True)
        print("NO RAW DATA FOUND.", flush=True)
        print("=" * 70, flush=True)
        print(f"\nPlease download and place real surveillance videos at:", flush=True)
        print(f"  {os.path.abspath(RAW_DIR)}", flush=True)
        print(f"\nExpected directory structure:", flush=True)
        print(f"  {RAW_DIR}/ucf_crime/Anomaly-Videos/Assault/*.mp4", flush=True)
        print(f"  {RAW_DIR}/ucf_crime/Anomaly-Videos/Fighting/*.mp4", flush=True)
        print(f"  {RAW_DIR}/ucf_crime/Anomaly-Videos/Burglary/*.mp4", flush=True)
        print(f"  {RAW_DIR}/ucf_crime/Anomaly-Videos/Robbery/*.mp4", flush=True)
        print(f"  {RAW_DIR}/ucf_crime/Anomaly-Videos/Shoplifting/*.mp4", flush=True)
        print(f"  {RAW_DIR}/ucf_crime/Anomaly-Videos/Stealing/*.mp4", flush=True)
        print(f"  {RAW_DIR}/ucf_crime/Normal-Videos/*.mp4", flush=True)
        print(f"  {RAW_DIR}/rwf_2000/fight/*.avi", flush=True)
        print(f"  {RAW_DIR}/rwf_2000/nonfight/*.avi", flush=True)
        print(f"\nSupported video formats: {sorted(VIDEO_EXTENSIONS)}", flush=True)
        print(f"Supported image formats: {sorted(IMAGE_EXTENSIONS)}", flush=True)
        print(f"\nExcluded categories (will be ignored if present):", flush=True)
        for label in sorted(LabelMapper.EXCLUDED_LABELS):
            print(f"  - {label}: {LabelMapper.get_exclusion_reason(label)}", flush=True)
        return

    # 3. Apply label mapping
    print("\nStep 3: Label mapping (7-class → binary)...", flush=True)

    mapped = [r for r in all_records if r["mvp_label"] is not None]
    excluded = [r for r in all_records if r["mvp_label"] is None]

    # Add binary label
    for r in mapped:
        r["binary_label"] = mvp_to_binary(r["mvp_label"])

    # Original label distribution
    orig_label_counts: Dict[str, int] = defaultdict(int)
    for r in all_records:
        orig_label_counts[r["original_label"]] += 1

    print(f"\n  Original label distribution:", flush=True)
    for label, count in sorted(orig_label_counts.items(), key=lambda x: -x[1]):
        mapping = LabelMapper.UCF_CRIME_MAPPING.get(label) or LabelMapper.RWF_MAPPING.get(label, "?")
        binary = mvp_to_binary(mapping) if mapping else "EXCLUDED"
        status = "→ " + (binary or "EXCLUDED")
        print(f"    {label:20s}: {count:4d} videos  {status}", flush=True)

    # Binary class distribution
    binary_counts: Dict[str, int] = defaultdict(int)
    for r in mapped:
        binary_counts[r["binary_label"]] += 1

    print(f"\n  Binary class distribution:", flush=True)
    for cls in BINARY_CLASSES:
        count = binary_counts.get(cls, 0)
        bar = "█" * min(count // 5, 40)
        print(f"    {cls:12s}: {count:5d} videos  {bar}", flush=True)

    total_mapped = len(mapped)
    total_excluded = len(excluded)
    print(f"\n  Total mapped:   {total_mapped}", flush=True)
    print(f"  Total excluded: {total_excluded}", flush=True)

    if total_mapped > 0:
        crime_count = binary_counts.get("crime", 0)
        noncrime_count = binary_counts.get("non_crime", 0)
        ratio = crime_count / max(noncrime_count, 1)
        print(f"  Crime/Non-Crime ratio: {ratio:.2f}:1", flush=True)
        if ratio > 5.0 or ratio < 0.2:
            print(f"  ⚠ WARNING: Severe class imbalance detected!", flush=True)

    # 4. File integrity check
    print("\nStep 4: File integrity check...", flush=True)
    invalid_files = []
    valid_count = 0
    for r in all_records:
        path = r.get("video_path", "")
        is_valid, error = check_file_integrity(path)
        if is_valid:
            valid_count += 1
        else:
            invalid_files.append((r["video_id"], path, error))

    print(f"  Valid files:   {valid_count}", flush=True)
    print(f"  Invalid files: {len(invalid_files)}", flush=True)
    if invalid_files:
        for vid, path, error in invalid_files[:10]:
            print(f"    ✗ {vid}: {error}", flush=True)
        if len(invalid_files) > 10:
            print(f"    ... and {len(invalid_files) - 10} more", flush=True)

    # 5. Duplicate detection
    print("\nStep 5: Duplicate detection...", flush=True)
    duplicates = find_duplicates(all_records)
    print(f"  Possible duplicates: {len(duplicates)}", flush=True)
    if duplicates:
        for vid_a, vid_b, h in duplicates[:5]:
            print(f"    ⚠ {vid_a} == {vid_b} (hash: {h[:16]}...)", flush=True)

    # 6. Video-level split preview
    print("\nStep 6: Train / Val / Test split preview (video-level)...", flush=True)
    splitter = VideoSplitter(seed=42)
    splits = splitter.split_videos(mapped)
    splitter.verify_no_leakage(splits)

    for split_name in ["train", "val", "test"]:
        videos = splits.get(split_name, [])
        split_binary: Dict[str, int] = defaultdict(int)
        split_unique_sources: set = set()
        for v in videos:
            split_binary[v.get("binary_label", "?")] += 1
            split_unique_sources.add(v["video_id"])
        print(f"\n  {split_name.upper():6s}: {len(videos)} videos ({len(split_unique_sources)} unique sources)", flush=True)
        for cls in BINARY_CLASSES:
            count = split_binary.get(cls, 0)
            print(f"    {cls:12s}: {count:5d}", flush=True)

    # 7. Summary
    print("\n" + "=" * 70, flush=True)
    print("VALIDATION SUMMARY", flush=True)
    print("=" * 70, flush=True)
    print(f"  Total raw videos:     {len(all_records)}", flush=True)
    print(f"  Mapped to binary:     {total_mapped}", flush=True)
    print(f"  Excluded:             {total_excluded}", flush=True)
    print(f"  Valid files:          {valid_count}", flush=True)
    print(f"  Invalid files:        {len(invalid_files)}", flush=True)
    print(f"  Possible duplicates:  {len(duplicates)}", flush=True)
    print(f"  Crime videos:         {binary_counts.get('crime', 0)}", flush=True)
    print(f"  Non-crime videos:     {binary_counts.get('non_crime', 0)}", flush=True)

    ready = total_mapped > 0 and len(invalid_files) == 0
    if ready:
        print(f"\n  ✓ Dataset is READY for frame extraction and training.", flush=True)
        print(f"  Next step: Run frame extraction when explicitly requested.", flush=True)
    else:
        if total_mapped == 0:
            print(f"\n  ✗ No valid videos found. Download real surveillance data first.", flush=True)
        if invalid_files:
            print(f"\n  ✗ Fix {len(invalid_files)} invalid files before proceeding.", flush=True)

    print("=" * 70 + "\n", flush=True)


if __name__ == "__main__":
    validate_dataset()
