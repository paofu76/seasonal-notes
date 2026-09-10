import math

from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QBrush, QPainterPath, QRadialGradient
from PySide6.QtWidgets import QWidget

from seasonal_notes.themes import THEMES
from .wind_scene import SeasonalOverlay  # Backward-compatible public import.


class SeasonMood(QWidget):
    """标题区中的动态季节胶囊，提供清晰但不打扰编辑的动画焦点。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.season = "春日"
        self.phase = 0
        self.setFixedSize(158, 50)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(46)

    def set_animation_enabled(self, enabled):
        if enabled:
            if not self.timer.isActive():
                self.timer.start(46)
        else:
            self.timer.stop()
        self.update()

    def set_season(self, season):
        self.season = season
        self.phase = 0
        self.update()

    def tick(self):
        self.phase = (self.phase + 1) % 720
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        t = self.phase / 75.0
        colors = {
            "春日": ((246, 183, 128), (150, 211, 177), (62, 76, 61)),
            "盛夏": ((255, 194, 83), (245, 142, 76), (91, 60, 25)),
            "秋意": ((220, 132, 83), (184, 101, 98), (86, 53, 42)),
            "冬藏": ((133, 176, 224), (185, 168, 220), (49, 63, 86)),
        }[self.season]
        clip = QPainterPath()
        clip.addRoundedRect(0, 0, w, h, 16, 16)
        p.setClipPath(clip)
        p.fillPath(clip, QColor(255, 255, 255, 178))
        p.setPen(Qt.NoPen)
        for i, (color, offset) in enumerate(((colors[0], 0), (colors[1], 2.2))):
            cx = w * (0.25 + i * 0.48) + math.sin(t * (0.58 + i * 0.12) + offset) * 20
            cy = h * (0.45 + i * 0.12) + math.cos(t * 0.62 + offset) * 8
            radius = 62 - i * 8
            gradient = QRadialGradient(QPointF(cx, cy), radius)
            gradient.setColorAt(0, QColor(*color, 125))
            gradient.setColorAt(1, QColor(*color, 0))
            p.setBrush(QBrush(gradient))
            p.drawEllipse(QPointF(cx, cy), radius, radius * 0.62)
        p.setClipping(False)
        p.setPen(QColor(*colors[2]))
        font = p.font()
        font.setPointSize(11)
        font.setBold(True)
        p.setFont(font)
        p.drawText(16, 0, w - 32, h, Qt.AlignVCenter | Qt.AlignLeft, self.season)
        font.setPointSize(8)
        font.setBold(False)
        p.setFont(font)
        p.setPen(QColor(*colors[2], 150))
        p.drawText(65, 1, w - 77, h, Qt.AlignVCenter | Qt.AlignRight, THEMES[self.season][4])
        p.end()
