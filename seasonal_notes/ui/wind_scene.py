"""Subtle seasonal weather over photographic, gently moving wallpapers."""

import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap, QRadialGradient
from PySide6.QtWidgets import QWidget

from seasonal_notes.themes import THEMES


class SeasonalOverlay(QWidget):
    INTERVAL = 42
    SCENE_NAMES = {
        "春日": "樱花创作间 · 雨后日出",
        "盛夏": "海边冲浪屋 · 风过白纱",
        "秋意": "艺术校园 · 唱片与落叶",
        "冬藏": "城市放映夜 · 雪落窗前",
    }

    SCENE_FILES = {
        "春日": "spring-rain.png",
        "盛夏": "summer-breeze.png",
        "秋意": "autumn-leaves.png",
        "冬藏": "winter-snow.png",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.season = "春日"
        self.phase = 0
        self.scenes = {}
        assets = Path(__file__).resolve().parent.parent / "assets"
        for season, filename in self.SCENE_FILES.items():
            scene = QPixmap(str(assets / filename))
            if scene.isNull():
                legacy_name = {
                    "春日": "spring-studio.png",
                    "盛夏": "summer-surf.png",
                    "秋意": "autumn-campus.png",
                    "冬藏": "winter-loft.png",
                }[season]
                scene = QPixmap(str(assets / legacy_name))
            if not scene.isNull():
                self.scenes[season] = scene
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.tick)
        self.timer.start(self.INTERVAL)

    def set_season(self, season):
        self.season = season
        self.phase = 0
        self.update()

    def set_animation_enabled(self, enabled):
        if enabled and not self.timer.isActive():
            self.timer.start(self.INTERVAL)
        elif not enabled:
            self.timer.stop()
        self.update()

    def tick(self):
        self.phase += 1
        self.update()

    def _draw_scene(self, p, scene, t):
        w, h = self.width(), self.height()
        # A slow camera drift reads as breeze without bending buildings or furniture.
        scale = max(w / scene.width(), h / scene.height())
        zoom = 1.014 + .008 * (.5 + .5 * math.sin(t * .13))
        dw, dh = scene.width() * scale * zoom, scene.height() * scale * zoom
        drift_x = math.sin(t * .075) * w * .004
        drift_y = math.cos(t * .061) * h * .003
        ox, oy = (w - dw) / 2 + drift_x, (h - dh) / 2 + drift_y
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawPixmap(QRectF(ox, oy, dw, dh), scene, QRectF(scene.rect()))

    def _draw_weather(self, p, t):
        w, h = self.width(), self.height()
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        if self.season == "春日":
            # Fine, slanted rain with varied depth and speed; no uniform particle dots.
            for i in range(118):
                depth = .34 + (i % 11) * .058
                speed = .25 + depth * .27
                x = ((i * .618 + t * speed + .025 * math.sin(t * .7 + i)) % 1) * w
                y = ((i * .381 + t * (speed * 1.55)) % 1) * h
                length = 5 + depth * 15
                p.setPen(QColor(227, 239, 246, int(18 + depth * 52)))
                p.drawLine(QPointF(x, y), QPointF(x - length * .34, y + length))
        elif self.season == "盛夏":
            # Broad, defocused sun glints drift across the scene like moving foliage shade.
            for i in range(7):
                x = ((i * .227 + t * (.012 + i * .001)) % 1) * w
                y = (.13 + .72 * ((i * .371 + .08 * math.sin(t * .22 + i)) % 1)) * h
                radius = min(w, h) * (.12 + (i % 3) * .045)
                glow = QRadialGradient(QPointF(x, y), radius)
                glow.setColorAt(0, QColor(255, 246, 198, 22))
                glow.setColorAt(.42, QColor(255, 247, 215, 9))
                glow.setColorAt(1, QColor(255, 247, 215, 0))
                p.setBrush(glow)
                p.drawEllipse(QPointF(x, y), radius, radius * .62)
        elif self.season == "秋意":
            # A few layered, irregular maple leaves tumble slowly on a cross-breeze.
            for i in range(22):
                depth = .42 + (i % 6) * .105
                progress = (t * (.025 + depth * .021) + i * .173) % 1
                x = ((i * .397 + progress * .68 + .025 * math.sin(t * .42 + i)) % 1) * w
                y = -24 + progress * (h + 48)
                size = (5 + (i % 4) * 1.7) * depth
                alpha = int(54 + depth * 96)
                colors = ((185, 70, 31), (220, 116, 34), (167, 90, 38), (232, 157, 53))
                p.save()
                p.translate(x, y)
                p.rotate(24 * math.sin(t * (.35 + depth * .15) + i) + i * 37)
                leaf = QPainterPath()
                leaf.moveTo(0, size * 1.25)
                leaf.cubicTo(-size * .25, size * .78, -size * 1.1, size * .94,
                             -size * .78, size * .38)
                leaf.cubicTo(-size * 1.35, size * .14, -size * .82, -size * .25,
                             -size * .48, -size * .14)
                leaf.cubicTo(-size * .38, -size * .82, -size * .12, -size * .72,
                             0, -size * .46)
                leaf.cubicTo(size * .12, -size * .72, size * .38, -size * .82,
                             size * .48, -size * .14)
                leaf.cubicTo(size * .82, -size * .25, size * 1.35, size * .14,
                             size * .78, size * .38)
                leaf.cubicTo(size * 1.1, size * .94, size * .25, size * .78,
                             0, size * 1.25)
                p.setBrush(QColor(*colors[i % len(colors)], alpha))
                p.drawPath(leaf)
                p.restore()
        else:
            # Foreground flakes are larger and drift sideways; distant flakes stay soft.
            for i in range(72):
                depth = .2 + (i % 9) * .085
                progress = (t * (.035 + depth * .055) + i * .137) % 1
                x = ((i * .618 + progress * .22 + .025 * math.sin(t * .52 + i)) % 1) * w
                y = ((i * .381 + progress) % 1) * h
                radius = .7 + depth * 3.4
                alpha = int(44 + depth * 102)
                p.setBrush(QColor(244, 248, 255, alpha))
                p.drawEllipse(QPointF(x, y), radius * .82, radius * (1.05 + depth * .25))

    def paintEvent(self, event):
        if self.width() < 10 or self.height() < 10:
            return
        p = QPainter(self)
        scene = self.scenes.get(self.season)
        if scene is None:
            p.fillRect(self.rect(), QColor(THEMES[self.season][0]))
        else:
            t = self.phase * self.INTERVAL / 1000
            self._draw_scene(p, scene, t)
            self._draw_weather(p, t)
        p.end()
