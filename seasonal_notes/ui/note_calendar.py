from collections import Counter

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QCalendarWidget


class NoteCalendar(QCalendarWidget):
    """Month calendar that marks days containing one or more notes."""

    def __init__(self, notes=None, accent="#ed8b58", parent=None):
        super().__init__(parent)
        self.counts = Counter(note.get("date", "") for note in (notes or []))
        self.accent = QColor(accent)

    def set_notes(self, notes, accent=None):
        self.counts = Counter(note.get("date", "") for note in notes)
        if accent:
            self.accent = QColor(accent)
        self.updateCells()

    def paintCell(self, painter, rect, selected_date):
        super().paintCell(painter, rect, selected_date)
        count = self.counts.get(selected_date.toString("yyyy-MM-dd"), 0)
        if not count:
            return
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.accent)
        badge = QRectF(rect.right() - 16, rect.bottom() - 15, 13, 13)
        painter.drawEllipse(badge)
        painter.setPen(Qt.white)
        font = QFont(painter.font())
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(badge, Qt.AlignCenter, str(min(count, 9)))
        painter.restore()
