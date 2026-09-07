import math

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush, QPainterPath, QRadialGradient, QLinearGradient
from PySide6.QtWidgets import QWidget


from seasonal_notes.themes import THEMES


class SeasonalOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.season = "春日"
        self.phase = 0
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(42)

    def set_animation_enabled(self, enabled):
        if enabled:
            if not self.timer.isActive():
                self.timer.start(42)
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
        if self.width() < 10:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        t = self.phase / 90.0
        p.setPen(Qt.NoPen)

        def glow(cx, cy, radius, color, alpha):
            gradient = QRadialGradient(QPointF(cx, cy), radius)
            gradient.setColorAt(0, QColor(*color, alpha))
            gradient.setColorAt(0.55, QColor(*color, max(2, alpha // 3)))
            gradient.setColorAt(1, QColor(*color, 0))
            p.setBrush(QBrush(gradient))
            p.drawEllipse(QPointF(cx, cy), radius, radius * 0.78)

        def organic_blob(cx, cy, sx, sy, color, alpha, seed):
            pulse = 1 + math.sin(t * 0.62 + seed) * 0.045
            sx *= pulse
            sy *= pulse
            path = QPainterPath()
            path.moveTo(cx - sx, cy + sy * 0.05)
            path.cubicTo(
                cx - sx * 0.92,
                cy - sy * 0.72,
                cx - sx * 0.28,
                cy - sy * 1.05,
                cx + sx * 0.22,
                cy - sy * 0.88,
            )
            path.cubicTo(
                cx + sx * 0.92,
                cy - sy * 0.72,
                cx + sx * 1.05,
                cy - sy * 0.08,
                cx + sx * 0.82,
                cy + sy * 0.42,
            )
            path.cubicTo(
                cx + sx * 0.48,
                cy + sy * 0.98,
                cx - sx * 0.40,
                cy + sy * 1.02,
                cx - sx,
                cy + sy * 0.05,
            )
            path.closeSubpath()
            gradient = QLinearGradient(cx - sx, cy - sy, cx + sx, cy + sy)
            gradient.setColorAt(0, QColor(*color, alpha))
            gradient.setColorAt(1, QColor(*color, max(3, alpha // 5)))
            p.setBrush(QBrush(gradient))
            p.drawPath(path)

        def soft_ribbon(y, width, color, alpha, phase):
            lift = math.sin(t * 0.72 + phase) * 16
            path = QPainterPath()
            path.moveTo(w * 0.18, y)
            path.cubicTo(
                w * 0.40, y - width + lift, w * 0.64, y + width - lift, w, y - width * 0.28
            )
            path.lineTo(w, y + width * 0.42)
            path.cubicTo(
                w * 0.72,
                y + width + lift,
                w * 0.42,
                y - width * 0.22 - lift,
                w * 0.18,
                y + width * 0.55,
            )
            path.closeSubpath()
            gradient = QLinearGradient(w * 0.18, y, w, y)
            gradient.setColorAt(0, QColor(*color, 0))
            gradient.setColorAt(0.48, QColor(*color, alpha))
            gradient.setColorAt(1, QColor(*color, 0))
            p.setBrush(QBrush(gradient))
            p.drawPath(path)

        if self.season == "春日":
            # 水彩般的湿润色块：缓慢相互靠近、分离，像清晨空气正在舒展。
            glow(w * 0.72 + math.sin(t * 0.42) * 42, h * 0.13, w * 0.46, (255, 218, 124), 45)
            organic_blob(
                w * 0.32 + math.sin(t * 0.48) * 24,
                h * 0.80,
                w * 0.27,
                h * 0.20,
                (151, 211, 174),
                32,
                0,
            )
            organic_blob(
                w * 0.88 + math.cos(t * 0.38) * 20,
                h * 0.55,
                w * 0.18,
                h * 0.28,
                (247, 174, 151),
                25,
                2,
            )
            soft_ribbon(h * 0.31, 42, (134, 204, 180), 20, 0)
            # 三层细雨，近景更清晰，远景更慢，形成空间纵深。
            for layer, (count, speed, alpha, size) in enumerate(
                [(14, 0.34, 18, 2.0), (10, 0.58, 28, 2.8), (7, 0.88, 38, 3.6)]
            ):
                for i in range(count):
                    x = ((i * 137 + layer * 83) % 997) / 997 * w
                    y = ((i * 211 + self.phase * speed * 7 + layer * 139) % 1009) / 1009 * h
                    drop = QPainterPath()
                    drop.moveTo(x, y - size * 1.5)
                    drop.cubicTo(x + size, y, x + size * 0.8, y + size, x, y + size * 1.35)
                    drop.cubicTo(x - size * 0.8, y + size, x - size, y, x, y - size * 1.5)
                    p.setBrush(QColor(99, 157, 143, alpha))
                    p.drawPath(drop)
        elif self.season == "盛夏":
            # 日照不是圆形太阳，而是大面积暖光呼吸与空气折射。
            glow(w * 0.78 + math.sin(t * 0.30) * 35, h * 0.04, w * 0.56, (255, 186, 72), 70)
            glow(w * 0.42, h * 0.95, w * 0.48, (255, 226, 121), 44)
            soft_ribbon(h * 0.26, 46, (255, 164, 82), 28, 1)
            soft_ribbon(h * 0.68, 58, (119, 196, 171), 19, 3)
            # 浮动光斑模拟树荫下被微风推动的日光。
            for i in range(12):
                x = ((i * 191) % 1013) / 1013 * w + math.sin(t * 0.42 + i) * 24
                y = ((i * 127) % 809) / 809 * h + math.cos(t * 0.38 + i) * 14
                radius = 5 + (i % 4) * 3
                p.setBrush(QColor(255, 194, 88, 15 + (i % 3) * 7))
                p.drawEllipse(QPointF(x, y), radius * 1.7, radius)
        elif self.season == "秋意":
            # 琥珀色透明薄片错层漂移，保留秋日层次但不画具象叶片。
            glow(w * 0.82, h * 0.16, w * 0.44, (233, 155, 91), 48)
            for i, (cx, cy, sx, sy, color) in enumerate(
                [
                    (0.30, 0.82, 0.20, 0.13, (210, 125, 78)),
                    (0.72, 0.72, 0.24, 0.16, (176, 102, 92)),
                    (0.90, 0.34, 0.13, 0.20, (226, 169, 103)),
                ]
            ):
                organic_blob(
                    w * cx + math.sin(t * 0.35 + i) * 30,
                    h * cy + math.cos(t * 0.28 + i) * 18,
                    w * sx,
                    h * sy,
                    color,
                    24 + i * 3,
                    i,
                )
            soft_ribbon(h * 0.40, 52, (183, 107, 81), 18, 2)
            # 少量枫叶剪影，不遮挡内容，只在背景边缘缓慢旋转。
            for i in range(9):
                x = ((i * 173 + self.phase * (0.34 + i % 3 * 0.09) * 5) % 1103) / 1103 * w
                y = ((i * 257 + self.phase * (0.42 + i % 2 * 0.12) * 4) % 1019) / 1019 * h
                size = 4.5 + (i % 3) * 1.8
                p.save()
                p.translate(x, y)
                p.rotate(self.phase * 0.22 + i * 37)
                leaf = QPainterPath()
                leaf.moveTo(0, -size * 1.8)
                leaf.lineTo(size * 0.45, -size * 0.55)
                leaf.lineTo(size * 1.5, -size * 0.7)
                leaf.lineTo(size * 0.75, size * 0.15)
                leaf.lineTo(size * 1.05, size * 1.0)
                leaf.lineTo(0, size * 0.45)
                leaf.lineTo(-size * 1.05, size * 1.0)
                leaf.lineTo(-size * 0.75, size * 0.15)
                leaf.lineTo(-size * 1.5, -size * 0.7)
                leaf.lineTo(-size * 0.45, -size * 0.55)
                leaf.closeSubpath()
                p.setBrush(QColor(183, 103 + i % 3 * 16, 74, 20 + i % 3 * 7))
                p.drawPath(leaf)
                p.restore()
        else:
            # 冬季采用透亮的极光薄幕和冰蓝漫反射，安静但不冰冷。
            glow(w * 0.76, h * 0.10, w * 0.48, (174, 213, 242), 55)
            glow(w * 0.35, h * 0.92, w * 0.42, (196, 181, 231), 35)
            soft_ribbon(h * 0.24, 58, (145, 191, 228), 24, 0)
            soft_ribbon(h * 0.60, 72, (185, 169, 220), 18, 2)
            organic_blob(
                w * 0.92 + math.sin(t * 0.30) * 16,
                h * 0.70,
                w * 0.13,
                h * 0.28,
                (226, 241, 250),
                32,
                4,
            )
            for i in range(24):
                x = ((i * 149 + math.sin(t * 0.32 + i) * 44) % 1009) / 1009 * w
                y = ((i * 227 + self.phase * (0.24 + i % 4 * 0.06) * 5) % 1031) / 1031 * h
                radius = 1.7 + (i % 4) * 0.65
                p.setBrush(QColor(111, 157, 201, 24 + (i % 4) * 8))
                p.drawEllipse(QRectF(x - radius, y - radius, radius * 2, radius * 2))
        p.end()


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
