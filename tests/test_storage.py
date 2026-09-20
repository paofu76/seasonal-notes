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

    def test_settings_round_trip_and_corrupt_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            with patch.object(storage, "SETTINGS", path):
                self.assertEqual(storage.load_settings(), {})
                settings = {"theme": "盛夏", "motion": False, "split_sizes": [300, 700]}
                storage.save_settings(settings)
                self.assertEqual(storage.load_settings(), settings)
                path.write_text("broken", encoding="utf-8")
                self.assertEqual(storage.load_settings(), {})

    def test_full_archive_round_trip_with_attachment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            attachments = root / "attachments"
            attachments.mkdir()
            image = attachments / "image.png"
            image.write_bytes(b"fake-image")
            notes = [
                {
                    "id": "1",
                    "title": "带图片的笔记",
                    "body_html": f'<img src="{image}">',
                }
            ]
            archive = root / "backup.snotes"
            with patch.multiple(
                storage,
                APP_DATA_DIR=root,
                ATTACHMENTS_DIR=attachments,
                DATA=root / "notes.json",
                SETTINGS=root / "settings.json",
                BACKUP_DIR=root / "backups",
            ):
                storage.save_notes(notes)
                storage.export_archive(archive, notes)
                storage.save_notes([])
                image.unlink()
                restored = storage.import_archive(archive)
                self.assertEqual(restored[0]["title"], "带图片的笔记")
                self.assertTrue(image.exists())
                self.assertIn(str(image), restored[0]["body_html"])
