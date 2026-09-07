"""独立于 Qt 的本地存储；环境变量只用于开发与隔离测试。"""

import json
import os
import shutil
from pathlib import Path

APP_DATA_DIR = Path(
    os.environ.get(
        "SEASONAL_NOTES_DATA_DIR", str(Path.home() / "Library/Application Support/季节笔记")
    )
)
ATTACHMENTS_DIR = APP_DATA_DIR / "attachments"
DATA = APP_DATA_DIR / "notes.json"
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
