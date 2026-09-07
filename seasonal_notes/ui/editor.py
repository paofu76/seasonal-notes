import json, os, uuid, sys, shutil
from datetime import date
from PySide6.QtCore import Qt, QDate, QSize, QTimer, QPointF, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (QAction, QFont, QTextCursor, QTextImageFormat, QPainter, QColor,
    QBrush, QPainterPath, QRadialGradient, QLinearGradient, QTextTableFormat, QTextLength,
    QTextCharFormat)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QLabel, QPushButton, QLineEdit, QTextEdit, QSplitter, QFileDialog, QMessageBox,
    QToolButton, QInputDialog, QGraphicsDropShadowEffect, QDialog, QCalendarWidget, QSpinBox,
    QCheckBox, QGridLayout)


class NoteEditor(QTextEdit):
 """支持点击勾选的富文本编辑器。"""
 def mousePressEvent(self,event):
  cursor=self.cursorForPosition(event.position().toPoint()); text=cursor.block().text()
  if event.position().x()<62 and (text.startswith('☐') or text.startswith('☑')):
   cursor.setPosition(cursor.block().position()); cursor.movePosition(QTextCursor.NextCharacter,QTextCursor.KeepAnchor)
   cursor.insertText('☑' if text.startswith('☐') else '☐'); self.setTextCursor(cursor); return
  super().mousePressEvent(event)

