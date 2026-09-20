from PySide6.QtCore import Signal
from PySide6.QtGui import QImage, QTextCursor
from PySide6.QtWidgets import QTextEdit


class NoteEditor(QTextEdit):
    """支持点击勾选的富文本编辑器。"""

    imagePasted = Signal(QImage)

    def insertFromMimeData(self, source):
        if source.hasImage():
            image = QImage(source.imageData())
            if not image.isNull():
                self.imagePasted.emit(image)
                return
        super().insertFromMimeData(source)

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
