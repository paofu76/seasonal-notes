from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class NoteListItem(QFrame):
    """信息密度适中的笔记摘要卡片。"""

    def __init__(self, note, parent=None):
        super().__init__(parent)
        self.setObjectName("noteItem")
        self.setProperty("selected", False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(3)

        top = QHBoxLayout()
        top.setSpacing(8)
        title = QLabel(note.get("title") or "无标题笔记")
        title.setObjectName("noteItemTitle")
        title.setTextInteractionFlags(Qt.NoTextInteraction)
        top.addWidget(title, 1)
        if note.get("favorite"):
            favorite = QLabel("★")
            favorite.setObjectName("noteFavorite")
            top.addWidget(favorite)
        layout.addLayout(top)

        preview_text = " ".join((note.get("body") or "").split()) or "还没有写下内容"
        preview = QLabel(preview_text)
        preview.setObjectName("notePreview")
        preview.setMaximumHeight(17)
        layout.addWidget(preview)

        tags = " ".join(f"#{tag}" for tag in note.get("tags", [])[:2])
        meta_parts = [
            note.get("date", ""),
            note.get("season", "春日"),
            note.get("folder", "随手记"),
        ]
        if tags:
            meta_parts.append(tags)
        meta = QLabel("   ·   ".join(meta_parts))
        meta.setObjectName("noteItemMeta")
        layout.addWidget(meta)

    def set_selected(self, selected):
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)
