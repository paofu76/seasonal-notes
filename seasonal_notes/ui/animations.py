import math
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush, QPainterPath, QRadialGradient, QLinearGradient, QPixmap
from PySide6.QtWidgets import QWidget


from seasonal_notes.themes import THEMES


class SeasonalOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.season = "春日"
        self.phase = 0
        atlas = QPixmap(str(Path(__file__).resolve().parent.parent / 'assets' / 'seasons-3d-atlas.png'))
        self.scenes = {}
        if not atlas.isNull():
            sw, sh = atlas.width() // 2, atlas.height() // 2
            for i, name in enumerate(('春日', '盛夏', '秋意', '冬藏')):
                self.scenes[name] = atlas.copy((i % 2) * sw, (i // 2) * sh, sw, sh)
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
        self.phase += 1
        self.update()

    def paintEvent(self, event):
        if self.width() < 10:
            return
        p = QPainter(self)
        scene = self.scenes.get(self.season)
        if scene is not None:
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            seconds = self.phase * 0.042
            zoom = 1.055 + 0.015 * math.sin(seconds * 0.065)
            scale = max(self.width() / scene.width(), self.height() / scene.height()) * zoom
            dw, dh = scene.width() * scale, scene.height() * scale
            x = (self.width() - dw) / 2 + math.sin(seconds * 0.09) * (dw - self.width()) * 0.28
            y = (self.height() - dh) / 2 + math.cos(seconds * 0.07) * (dh - self.height()) * 0.24
            p.drawPixmap(QRectF(x, y, dw, dh), scene, QRectF(scene.rect()))
            p.fillRect(self.rect(), QColor(255, 249, 239, 24))
            p.end()
            return
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        t = self.phase / 90.0
        p.setPen(Qt.NoPen)

        def ambient_wash(top, middle, bottom):
            """A quiet full-canvas wash keeps the scene visible behind translucent cards."""
            gradient = QLinearGradient(0, 0, w, h)
            gradient.setColorAt(0, QColor(*top))
            gradient.setColorAt(0.48, QColor(*middle))
            gradient.setColorAt(1, QColor(*bottom))
            p.fillRect(self.rect(), gradient)

        def horizon_glow(cx, cy, radius, color, alpha):
            gradient = QRadialGradient(QPointF(cx, cy), radius)
            gradient.setColorAt(0, QColor(*color, alpha))
            gradient.setColorAt(0.34, QColor(*color, int(alpha * 0.58)))
            gradient.setColorAt(0.76, QColor(*color, int(alpha * 0.16)))
            gradient.setColorAt(1, QColor(*color, 0))
            p.setBrush(QBrush(gradient))
            p.drawEllipse(QPointF(cx, cy), radius, radius)

        def depth_veil(anchor, amplitude, color, alpha, speed, offset, thickness):
            """Wide translucent planes create parallax without looking like particles."""
            drift = math.sin(t * speed + offset) * amplitude
            path = QPainterPath()
            path.moveTo(-w * 0.12, anchor + drift)
            path.cubicTo(
                w * 0.20,
                anchor - amplitude * 1.15 + drift,
                w * 0.48,
                anchor + amplitude * 0.90 - drift * 0.35,
                w * 0.72,
                anchor - amplitude * 0.30,
            )
            path.cubicTo(
                w * 0.90,
                anchor - amplitude + drift * 0.20,
                w * 1.05,
                anchor + amplitude * 0.45,
                w * 1.12,
                anchor + drift * 0.25,
            )
            path.lineTo(w * 1.12, anchor + thickness)
            path.cubicTo(
                w * 0.76,
                anchor + thickness * 0.62,
                w * 0.43,
                anchor + thickness * 1.18 + drift * 0.22,
                -w * 0.12,
                anchor + thickness * 0.68,
            )
            path.closeSubpath()
            gradient = QLinearGradient(0, anchor, w, anchor + thickness)
            gradient.setColorAt(0, QColor(*color, 0))
            gradient.setColorAt(0.22, QColor(*color, alpha // 2))
            gradient.setColorAt(0.58, QColor(*color, alpha))
            gradient.setColorAt(1, QColor(*color, 0))
            p.setBrush(QBrush(gradient))
            p.drawPath(path)

        def light_fall(x, width, color, alpha, lean=0.0):
            path = QPainterPath()
            path.moveTo(x, -h * 0.08)
            path.lineTo(x + width, -h * 0.08)
            path.lineTo(x + width * 0.32 + lean, h * 1.08)
            path.lineTo(x - width * 0.55 + lean, h * 1.08)
            path.closeSubpath()
            gradient = QLinearGradient(x, 0, x + lean, h)
            gradient.setColorAt(0, QColor(*color, alpha))
            gradient.setColorAt(0.52, QColor(*color, alpha // 3))
            gradient.setColorAt(1, QColor(*color, 0))
            p.setBrush(QBrush(gradient))
            p.drawPath(path)

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

        if self.season == "春日":
            ambient_wash((235, 249, 240, 44), (255, 247, 231, 22), (238, 246, 240, 34))
            horizon_glow(w * 0.76, h * 0.03, w * 0.54, (255, 211, 135), 48)
            horizon_glow(w * 0.03, h * 0.82, w * 0.38, (126, 197, 165), 34)
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
            depth_veil(h * 0.18, 46, (113, 187, 160), 30, 0.20, 0.4, h * 0.18)
            depth_veil(h * 0.62, 62, (245, 170, 149), 24, 0.13, 2.1, h * 0.24)
            light_fall(w * 0.62 + math.sin(t * 0.14) * 28, w * 0.18, (255, 236, 193), 38, w * 0.05)
        elif self.season == "盛夏":
            ambient_wash((255, 246, 214, 48), (248, 250, 224, 18), (226, 246, 235, 35))
            horizon_glow(w * 0.86, h * 0.02, w * 0.58, (255, 180, 67), 70)
            horizon_glow(w * 0.10, h * 0.92, w * 0.40, (89, 190, 163), 30)
            # 日照不是圆形太阳，而是大面积暖光呼吸与空气折射。
            glow(w * 0.78 + math.sin(t * 0.30) * 35, h * 0.04, w * 0.56, (255, 186, 72), 70)
            glow(w * 0.42, h * 0.95, w * 0.48, (255, 226, 121), 44)
            depth_veil(h * 0.20, 72, (255, 159, 71), 36, 0.22, 0.8, h * 0.20)
            depth_veil(h * 0.66, 88, (87, 183, 157), 28, 0.16, 2.8, h * 0.26)
            depth_veil(h * 0.43, 42, (255, 220, 122), 22, 0.28, 4.0, h * 0.13)
            light_fall(w * 0.74 + math.sin(t * 0.12) * 36, w * 0.24, (255, 214, 126), 52, -w * 0.08)
        elif self.season == "秋意":
            ambient_wash((255, 237, 220, 43), (249, 238, 224, 18), (241, 224, 215, 38))
            horizon_glow(w * 0.84, h * 0.08, w * 0.52, (232, 139, 78), 52)
            horizon_glow(w * 0.08, h * 0.92, w * 0.42, (175, 91, 83), 28)
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
            depth_veil(h * 0.22, 58, (219, 124, 76), 34, 0.17, 0.5, h * 0.20)
            depth_veil(h * 0.69, 76, (145, 79, 84), 28, 0.12, 2.6, h * 0.28)
            depth_veil(h * 0.48, 40, (232, 174, 105), 20, 0.23, 4.1, h * 0.13)
            light_fall(w * 0.80, w * 0.22, (246, 183, 121), 36, -w * 0.12)
        else:
            ambient_wash((230, 243, 253, 52), (241, 244, 252, 17), (232, 235, 249, 42))
            horizon_glow(w * 0.78, h * 0.02, w * 0.56, (125, 189, 233), 54)
            horizon_glow(w * 0.06, h * 0.90, w * 0.44, (175, 157, 219), 28)
            # 冬季采用透亮的极光薄幕和冰蓝漫反射，安静但不冰冷。
            glow(w * 0.76, h * 0.10, w * 0.48, (174, 213, 242), 55)
            glow(w * 0.35, h * 0.92, w * 0.42, (196, 181, 231), 35)
            depth_veil(h * 0.16, 72, (116, 180, 226), 36, 0.14, 0.2, h * 0.22)
            depth_veil(h * 0.52, 92, (170, 145, 211), 30, 0.10, 2.4, h * 0.30)
            depth_veil(h * 0.74, 54, (210, 232, 247), 24, 0.19, 4.5, h * 0.16)
            organic_blob(
                w * 0.92 + math.sin(t * 0.30) * 16,
                h * 0.70,
                w * 0.13,
                h * 0.28,
                (226, 241, 250),
                32,
                4,
            )
            light_fall(w * 0.18 + math.sin(t * 0.10) * 24, w * 0.20, (224, 241, 252), 40, w * 0.10)
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
