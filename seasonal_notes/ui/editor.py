from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QTextEdit


class NoteEditor(QTextEdit):
    """支持点击勾选的富文本编辑器。"""

    def mousePressEvent(self, event):
        cursor = self.cursorForPosition(event.position().toPoint())
        text = cursor.block().text()
        if event.position().x() < 62 and (text.startswith("☐") or text.startswith("☑")):
            cursor.setPosition(cursor.block().position())
            cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
            cursor.insertText("☑" if text.startswith("☐") else "☐")
            self.setTextCursor(cursor)
            return
        super().mousePressEvent(event)
