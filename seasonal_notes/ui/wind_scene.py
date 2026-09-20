"""Local image deformation: branches and cloth move while architecture stays still."""

import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QColor, QPainter, QPainterPath, QPixmap, QPolygonF, QTransform,
)
from PySide6.QtWidgets import QWidget

from seasonal_notes.themes import THEMES


class SeasonalOverlay(QWidget):
    INTERVAL = 33
    SCENE_NAMES = {
        "春日": "樱花创作间 · 雨后日出",
        "盛夏": "海边冲浪屋 · 风过白纱",
        "秋意": "艺术校园 · 唱片与落叶",
        "冬藏": "城市放映夜 · 雪落窗前",
    }

    SCENE_FILES = {
        "春日": "spring-studio.png",
        "盛夏": "summer-surf.png",
        "秋意": "autumn-campus.png",
        "冬藏": "winter-loft.png",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.season = "春日"
        self.phase = 0
        self.scenes = {}
        assets = Path(__file__).resolve().parent.parent / "assets"
        for season, filename in self.SCENE_FILES.items():
            scene = QPixmap(str(assets / filename))
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

    @staticmethod
    def _fade(value):
        value = max(0.0, min(1.0, value))
        return value * value * (3 - 2 * value)

    def displacement(self, u, v, t):
        """Return normalized displacement; zero at canvas edges and fixed structures."""
        edge = self._fade(u / .06) * self._fade((1-u) / .06)
        edge *= self._fade(v / .04) * self._fade((1-v) / .05)
        gust = .70 + .30 * math.sin(t * .47 + .8)
        wind = math.sin(t * 1.35 - u * 3.5 + v * 2) * gust
        flutter = math.sin(t * 2.7 + u * 11 - v * 7)
        canopy = self._fade((.49-v) / .25) * self._fade((.86-u) / .40)
        dx = canopy * (.009 * wind + .0025 * flutter)
        dy = canopy * .006 * math.sin(t * 1.1 - u * 5)
        if self.season == "盛夏":
            # The curtain is anchored along its top; folds travel down its length.
            cloth = self._fade((u-.73) / .14) * self._fade(v / .24)
            dx += cloth * (.024 * math.sin(t * 1.3 - v * 5) * gust
                           + .005 * math.sin(t * 2.1 - v * 12))
            dy += cloth * .006 * math.cos(t * 1.3 - v * 5)
            water = self._fade((v-.41)/.05) * self._fade((.78-v)/.12)
            water *= self._fade((u-.12)/.10) * self._fade((.72-u)/.10)
            dx += water * .0028 * math.sin(v * 88 - t * 2.2)
            dy += water * .0015 * math.cos(u * 25 + t * 1.8)
        elif self.season == "春日":
            water = self._fade((v-.55)/.10) * self._fade((.91-v)/.08)
            water *= self._fade((u-.42)/.14)
            dx += water * .0025 * math.sin(v * 74 - t * 1.8)
            curtain = self._fade((u-.68)/.12) * self._fade((.59-v)/.22)
            dx += curtain * .010 * math.sin(t * 1.15-v * 7)
        elif self.season == "秋意":
            dx *= 1.55
            dy *= 1.25
        else:
            dx *= .65
            dy *= .65
            curtain = self._fade((u-.70)/.12) * self._fade((.68-v)/.20)
            dx += curtain * (.015 * math.sin(t*.92-v*6)
                             + .003 * math.sin(t*2.0-v*13))
            dy += curtain * .0035 * math.cos(t*.92-v*6)
        return dx * edge, dy * edge

    def _draw_scene(self, p, scene, t):
        w, h = self.width(), self.height()
        # Fixed camera preserves the landscape. Mesh nodes share their edges.
        scale = max(w / scene.width(), h / scene.height())
        dw, dh = scene.width()*scale, scene.height()*scale
        ox, oy = (w-dw)/2, (h-dh)/2
        cols, rows = 24, 18
        points = []
        for row in range(rows+1):
            line = []
            for col in range(cols+1):
                u, v = col/cols, row/rows
                dx, dy = self.displacement(u, v, t)
                line.append(QPointF(ox+(u+dx)*dw, oy+(v+dy)*dh))
            points.append(line)
        unit = QPolygonF([QPointF(0, 0), QPointF(1, 0), QPointF(1, 1), QPointF(0, 1)])
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        # Fill first so subpixel rasterization cannot expose a clear seam.
        p.drawPixmap(QRectF(ox, oy, dw, dh), scene, QRectF(scene.rect()))
        for row in range(rows):
            for col in range(cols):
                quad = QPolygonF([points[row][col], points[row][col+1],
                                 points[row+1][col+1], points[row+1][col]])
                transform = QTransform.quadToQuad(unit, quad)
                p.setWorldTransform(transform)
                p.drawPixmap(QRectF(0, 0, 1, 1), scene,
                             QRectF(col*scene.width()/cols, row*scene.height()/rows,
                                    scene.width()/cols, scene.height()/rows))
        p.resetTransform()

    def _draw_weather(self, p, t):
        if self.season == "盛夏":
            return
        w, h = self.width(), self.height()
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        winter = self.season == "冬藏"
        count = 48 if winter else 17
        for i in range(count):
            depth = .45 + (i % 5) * .18
            duration = (17 if winter else 14) / depth
            progress = (t/duration + i*.61803398875) % 1
            x = ((i*.381966 + progress*.37 + .035*math.sin(t*.8+i)) % 1) * w
            y = -24 + progress*(h+48)
            size = (2.4 if winter else 6.0) * depth
            fade = min(1., progress*12, (1-progress)*12)
            p.save()
            p.translate(x, y)
            p.rotate(t*(19 if winter else 48)+i*71)
            if winter:
                p.setBrush(QColor(240, 247, 255, int(150*fade)))
                p.drawEllipse(QPointF(), size, size)
            else:
                p.scale(.30+.70*abs(math.cos(t*1.7+i)), 1)
                leaf = QPainterPath()
                leaf.moveTo(0, -size)
                leaf.cubicTo(size*1.1, -size*.65, size*.9, size*.55, 0, size)
                leaf.cubicTo(-size*.8, size*.45, -size*.9, -size*.5, 0, -size)
                color = (244, 178+i%3*12, 192) if self.season == "春日" else (192+i%4*14, 98+i%3*19, 36)
                p.setBrush(QColor(*color, int(205*fade)))
                p.drawPath(leaf)
            p.restore()

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
