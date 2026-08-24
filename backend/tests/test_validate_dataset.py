"""Tests for validate_dataset.py and synthetic data guards in train_real.py."""
import hashlib
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PIL import Image
import unittest


class TestBinaryLabelMapping(unittest.TestCase):
    """Test binary crime/non_crime label mapping."""

    def test_crime_labels(self):
        from app.ml.crime_classifier.validate_dataset import mvp_to_binary
        self.assertEqual(mvp_to_binary("crime_assault"), "crime")
        self.assertEqual(mvp_to_binary("crime_theft"), "crime")
        self.assertEqual(mvp_to_binary("crime_intrusion"), "crime")

    def test_noncrime_labels(self):
        from app.ml.crime_classifier.validate_dataset import mvp_to_binary
        self.assertEqual(mvp_to_binary("noncrime_walking"), "non_crime")
        self.assertEqual(mvp_to_binary("noncrime_traffic"), "non_crime")
        self.assertEqual(mvp_to_binary("noncrime_gathering"), "non_crime")
        self.assertEqual(mvp_to_binary("noncrime_interaction"), "non_crime")

    def test_excluded_labels_return_none(self):
        from app.ml.crime_classifier.validate_dataset import mvp_to_binary
        self.assertIsNone(mvp_to_binary(None))
        self.assertIsNone(mvp_to_binary("some_unknown"))


class TestUCFCrimeLabelExclusions(unittest.TestCase):
    """Verify Vandalism, Arson, Explosion, RoadAccidents are excluded."""

    def test_excluded_categories(self):
        from app.ml.crime_classifier.real_dataset import LabelMapper
        for label in ["Vandalism", "Arson", "Explosion", "RoadAccidents"]:
            self.assertTrue(LabelMapper.is_excluded(label), f"{label} should be excluded")
            result = LabelMapper.map_ucf_crime(label)
            self.assertIsNone(result, f"{label} should map to None (excluded)")

    def test_included_crime_categories(self):
        from app.ml.crime_classifier.real_dataset import LabelMapper
        self.assertEqual(LabelMapper.map_ucf_crime("Assault"), "crime_assault")
        self.assertEqual(LabelMapper.map_ucf_crime("Fighting"), "crime_assault")
        self.assertEqual(LabelMapper.map_ucf_crime("Burglary"), "crime_intrusion")
        self.assertEqual(LabelMapper.map_ucf_crime("Robbery"), "crime_theft")
        self.assertEqual(LabelMapper.map_ucf_crime("Shoplifting"), "crime_theft")
        self.assertEqual(LabelMapper.map_ucf_crime("Stealing"), "crime_theft")

    def test_normal_category(self):
        from app.ml.crime_classifier.real_dataset import LabelMapper
        result = LabelMapper.map_ucf_crime("Normal", "test_video.mp4")
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith("noncrime_"))


class TestFileIntegrityCheck(unittest.TestCase):
    """Test file integrity checking."""

    def test_nonexistent_file(self):
        from app.ml.crime_classifier.validate_dataset import check_file_integrity
        valid, msg = check_file_integrity("/nonexistent/path.mp4")
        self.assertFalse(valid)
        self.assertIn("does not exist", msg)

    def test_empty_file(self):
        from app.ml.crime_classifier.validate_dataset import check_file_integrity
        tmpdir = tempfile.mkdtemp()
        try:
            empty_file = os.path.join(tmpdir, "empty.mp4")
            with open(empty_file, "w") as f:
                pass  # empty file
            valid, msg = check_file_integrity(empty_file)
            self.assertFalse(valid)
            self.assertIn("empty", msg.lower())
        finally:
            shutil.rmtree(tmpdir)

    def test_unsupported_extension(self):
        from app.ml.crime_classifier.validate_dataset import check_file_integrity
        tmpdir = tempfile.mkdtemp()
        try:
            bad_file = os.path.join(tmpdir, "file.txt")
            with open(bad_file, "w") as f:
                f.write("not a video")
            valid, msg = check_file_integrity(bad_file)
            self.assertFalse(valid)
            self.assertIn("Unsupported", msg)
        finally:
            shutil.rmtree(tmpdir)

    def test_valid_video_file(self):
        from app.ml.crime_classifier.validate_dataset import check_file_integrity
        tmpdir = tempfile.mkdtemp()
        try:
            video_file = os.path.join(tmpdir, "test.mp4")
            with open(video_file, "wb") as f:
                f.write(b"\x00" * 200)  # dummy but sufficient size
            valid, msg = check_file_integrity(video_file)
            self.assertTrue(valid, f"Expected valid, got error: {msg}")
        finally:
            shutil.rmtree(tmpdir)


class TestDuplicateDetection(unittest.TestCase):
    """Test duplicate video detection by hash."""

    def test_find_duplicates_identical_files(self):
        from app.ml.crime_classifier.validate_dataset import find_duplicates
        tmpdir = tempfile.mkdtemp()
        try:
            content = b"\x00\x01\x02" * 100
            file_a = os.path.join(tmpdir, "a.mp4")
            file_b = os.path.join(tmpdir, "b.mp4")
            with open(file_a, "wb") as f:
                f.write(content)
            with open(file_b, "wb") as f:
                f.write(content)

            records = [
                {"video_id": "vid_a", "video_path": file_a},
                {"video_id": "vid_b", "video_path": file_b},
            ]
            dups = find_duplicates(records)
            self.assertEqual(len(dups), 1)
            self.assertIn("vid_a", dups[0])
            self.assertIn("vid_b", dups[0])
        finally:
            shutil.rmtree(tmpdir)

    def test_no_duplicates(self):
        from app.ml.crime_classifier.validate_dataset import find_duplicates
        tmpdir = tempfile.mkdtemp()
        try:
            file_a = os.path.join(tmpdir, "a.mp4")
            file_b = os.path.join(tmpdir, "b.mp4")
            with open(file_a, "wb") as f:
                f.write(b"\x00" * 100)
            with open(file_b, "wb") as f:
                f.write(b"\x01" * 100)

            records = [
                {"video_id": "vid_a", "video_path": file_a},
                {"video_id": "vid_b", "video_path": file_b},
            ]
            dups = find_duplicates(records)
            self.assertEqual(len(dups), 0)
        finally:
            shutil.rmtree(tmpdir)


class TestSyntheticDataGuard(unittest.TestCase):
    """Test that the synthetic data guard correctly identifies geometric shapes."""

    def test_synthetic_images_detected(self):
        """Solid-color geometric shape images should be flagged as synthetic."""
        from app.ml.crime_classifier.train_real import _is_synthetic_dataset

        tmpdir = tempfile.mkdtemp()
        try:
            train_dir = os.path.join(tmpdir, "train", "crime_assault")
            os.makedirs(train_dir, exist_ok=True)

            # Create 10 synthetic geometric-shape images
            for i in range(10):
                img = Image.new("RGB", (224, 224), (200, 180, 220))
                from PIL import ImageDraw
                draw = ImageDraw.Draw(img)
                draw.rectangle([20, 40, 100, 180], fill=(220, 50, 50))
                img.save(os.path.join(train_dir, f"synth_{i}.jpg"), "JPEG")

            result = _is_synthetic_dataset.__wrapped__(max_samples=10) if hasattr(_is_synthetic_dataset, '__wrapped__') else True

            # Directly test with our tmpdir by patching FRAMES_DIR
            import app.ml.crime_classifier.train_real as tr_mod
            old_frames = tr_mod.FRAMES_DIR
            tr_mod.FRAMES_DIR = tmpdir
            try:
                is_synth = _is_synthetic_dataset(max_samples=10)
                self.assertTrue(is_synth, "Solid-color geometric images should be detected as synthetic")
            finally:
                tr_mod.FRAMES_DIR = old_frames
        finally:
            shutil.rmtree(tmpdir)

    def test_real_photo_not_flagged(self):
        """An image with high color variance should NOT be flagged as synthetic."""
        import numpy as np
        from app.ml.crime_classifier.train_real import _is_synthetic_dataset

        tmpdir = tempfile.mkdtemp()
        try:
            train_dir = os.path.join(tmpdir, "train", "crime_assault")
            os.makedirs(train_dir, exist_ok=True)

            # Create 10 images with realistic color variance (random noise)
            for i in range(10):
                arr = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
                img = Image.fromarray(arr)
                img.save(os.path.join(train_dir, f"real_{i}.jpg"), "JPEG")

            import app.ml.crime_classifier.train_real as tr_mod
            old_frames = tr_mod.FRAMES_DIR
            tr_mod.FRAMES_DIR = tmpdir
            try:
                is_synth = _is_synthetic_dataset(max_samples=10)
                self.assertFalse(is_synth, "High-variance images should NOT be flagged as synthetic")
            finally:
                tr_mod.FRAMES_DIR = old_frames
        finally:
            shutil.rmtree(tmpdir)

    def test_empty_directory_not_flagged(self):
        """Empty dataset should not be flagged as synthetic (other guards handle it)."""
        from app.ml.crime_classifier.train_real import _is_synthetic_dataset

        tmpdir = tempfile.mkdtemp()
        try:
            import app.ml.crime_classifier.train_real as tr_mod
            old_frames = tr_mod.FRAMES_DIR
            tr_mod.FRAMES_DIR = tmpdir
            try:
                is_synth = _is_synthetic_dataset(max_samples=10)
                self.assertFalse(is_synth)
            finally:
                tr_mod.FRAMES_DIR = old_frames
        finally:
            shutil.rmtree(tmpdir)


class TestValidationCommandEmptyData(unittest.TestCase):
    """Test that validation command handles empty raw/ directory gracefully."""

    def test_validate_with_empty_raw(self):
        """validate_dataset() should not crash when raw/ is empty."""
        from app.ml.crime_classifier.validate_dataset import validate_dataset
        # Should complete without exceptions
        try:
            validate_dataset()
        except Exception as e:
            self.fail(f"validate_dataset() raised {type(e).__name__}: {e}")


if __name__ == "__main__":
    results = unittest.main(exit=False, verbosity=2)
    if results.result.wasSuccessful():
        print("\n[PASS] ALL DATASET VALIDATION TESTS PASSED!")
    else:
        print("\n[FAIL] Some tests failed.")
        sys.exit(1)
