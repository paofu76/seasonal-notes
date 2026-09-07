from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QWidget


class TablePreview(QWidget):
    """轻量表格预览，避免用户插入后才发现尺寸不合适。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = 3
        self.columns = 3
        self.header = True
        self.setMinimumHeight(132)

    def configure(self, rows, columns, header):
        self.rows = rows
        self.columns = columns
        self.header = header
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        area = self.rect().adjusted(10, 10, -10, -10)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#fffaf4"))
        p.drawRoundedRect(area, 12, 12)
        rows = min(self.rows + (1 if self.header else 0), 6)
        columns = min(self.columns, 6)
        cw = area.width() / columns
        rh = area.height() / rows
        for row in range(rows):
            for column in range(columns):
                cell = area.adjusted(
                    int(column * cw),
                    int(row * rh),
                    -int(area.width() - (column + 1) * cw),
                    -int(area.height() - (row + 1) * rh),
                )
                color = (
                    QColor("#f8d7bd")
                    if self.header and row == 0
                    else QColor("#fffdf9" if row % 2 else "#fff3e8")
                )
                p.setBrush(color)
                p.drawRoundedRect(cell.adjusted(2, 2, -2, -2), 5, 5)
        label_width = 158
        label_area = area.adjusted(
            (area.width() - label_width) // 2,
            area.height() - 34,
            -(area.width() - label_width) // 2,
            -4,
        )
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 226))
        p.drawRoundedRect(label_area, 10, 10)
        p.setPen(QColor("#9f7057"))
        font = p.font()
        font.setPointSize(9)
        font.setBold(True)
        p.setFont(font)
        text = f"{self.rows} 行 × {self.columns} 列" + (" · 含表头" if self.header else "")
        p.drawText(label_area, Qt.AlignCenter, text)
        p.end()
