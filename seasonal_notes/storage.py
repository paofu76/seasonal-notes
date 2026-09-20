"""独立于 Qt 的本地存储；环境变量只用于开发与隔离测试。"""

import json
import os
import re
import shutil
import zipfile
from datetime import date, datetime
from pathlib import Path

APP_DATA_DIR = Path(
    os.environ.get(
        "SEASONAL_NOTES_DATA_DIR", str(Path.home() / "Library/Application Support/季节笔记")
    )
)
ATTACHMENTS_DIR = APP_DATA_DIR / "attachments"
DATA = APP_DATA_DIR / "notes.json"
SETTINGS = APP_DATA_DIR / "settings.json"
BACKUP_DIR = APP_DATA_DIR / "backups"
LEGACY_DATA = Path(__file__).resolve().parent.parent / "notes.json"


def ensure_storage():
    ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA.exists() and LEGACY_DATA.exists():
        shutil.copy2(LEGACY_DATA, DATA)


def load_notes():
    if not DATA.exists():
        return []
    with DATA.open(encoding="utf-8") as stream:
        notes = json.load(stream)
    if not isinstance(notes, list):
        raise ValueError("笔记数据必须是列表")
    return notes


def save_notes(notes):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    temporary = DATA.with_suffix(".json.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(notes, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, DATA)


def load_settings():
    if not SETTINGS.exists():
        return {}
    try:
        with SETTINGS.open(encoding="utf-8") as stream:
            settings = json.load(stream)
    except (OSError, json.JSONDecodeError):
        return {}
    return settings if isinstance(settings, dict) else {}


def save_settings(settings):
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    temporary = SETTINGS.with_suffix(".json.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(settings, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, SETTINGS)


def export_archive(destination, notes=None):
    """Export notes and managed attachments as one portable archive."""
    notes = load_notes() if notes is None else notes
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("notes.json", json.dumps(notes, ensure_ascii=False, indent=2))
        if ATTACHMENTS_DIR.exists():
            for attachment in ATTACHMENTS_DIR.iterdir():
                if attachment.is_file():
                    archive.write(attachment, f"attachments/{attachment.name}")
    os.replace(temporary, destination)
    return destination


def import_archive(source):
    """Import a trusted seasonal-notes archive and remap attachment locations."""
    source = Path(source)
    try:
        with zipfile.ZipFile(source) as archive:
            notes = json.loads(archive.read("notes.json"))
            if not isinstance(notes, list):
                raise ValueError("备份文件中的笔记数据格式不正确")
            ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
            imported_names = []
            for member in archive.infolist():
                if not member.filename.startswith("attachments/") or member.is_dir():
                    continue
                filename = Path(member.filename).name
                if not filename:
                    continue
                target = ATTACHMENTS_DIR / filename
                with archive.open(member) as source_stream, target.open("wb") as target_stream:
                    shutil.copyfileobj(source_stream, target_stream)
                imported_names.append(filename)
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError, zipfile.BadZipFile) as error:
        raise ValueError("备份文件中没有有效的笔记数据") from error

    for note in notes:
        html = note.get("body_html", "")
        for filename in imported_names:
            pattern = rf'(src=["\'])(?:file://)?[^"\']*/{re.escape(filename)}'
            html = re.sub(
                pattern,
                lambda match: match.group(1) + str(ATTACHMENTS_DIR / filename),
                html,
            )
        note["body_html"] = html
    save_notes(notes)
    cleanup_attachments(notes)
    return notes


def create_daily_backup(notes=None, keep=10, force=False):
    """Create at most one automatic full backup per day and keep recent copies."""
    if notes is None and not DATA.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S") if force else date.today().isoformat()
    destination = BACKUP_DIR / f"季节笔记-{stamp}.snotes"
    if not destination.exists():
        export_archive(destination, notes)
    backups = sorted(BACKUP_DIR.glob("*.snotes"), reverse=True)
    for old_backup in backups[keep:]:
        old_backup.unlink(missing_ok=True)
    return destination


def cleanup_attachments(notes):
    """Remove only app-managed files that are no longer referenced by any note."""
    if not ATTACHMENTS_DIR.exists():
        return []
    html = "\n".join(note.get("body_html", "") for note in notes)
    removed = []
    for attachment in ATTACHMENTS_DIR.iterdir():
        if attachment.is_file() and attachment.name not in html:
            attachment.unlink(missing_ok=True)
            removed.append(attachment)
    return removed
