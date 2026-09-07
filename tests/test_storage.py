import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from seasonal_notes import storage


class StorageTests(unittest.TestCase):
    def test_unicode_round_trip_and_atomic_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.json"
            with patch.object(storage, "DATA", path):
                self.assertEqual(storage.load_notes(), [])
                notes = [{"id": "1", "body_html": "<b>你好</b>"}]
                storage.save_notes(notes)
                self.assertEqual(storage.load_notes(), notes)
                self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_corrupt_data_is_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.json"
            path.write_text("broken", encoding="utf-8")
            with patch.object(storage, "DATA", path):
                with self.assertRaises(ValueError):
                    storage.load_notes()
            self.assertEqual(path.read_text(), "broken")

    def test_migration_does_not_overwrite_existing_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy, target = root / "legacy.json", root / "notes.json"
            legacy.write_text("[]")
            with patch.multiple(
                storage, DATA=target, LEGACY_DATA=legacy, ATTACHMENTS_DIR=root / "attachments"
            ):
                storage.ensure_storage()
                self.assertEqual(target.read_text(), "[]")
                target.write_text('[{"id":"kept"}]')
                storage.ensure_storage()
                self.assertEqual(target.read_text(), '[{"id":"kept"}]')
