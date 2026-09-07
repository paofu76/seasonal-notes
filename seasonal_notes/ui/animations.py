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


from seasonal_notes.themes import THEMES

class SeasonalOverlay(QWidget):
 def __init__(self,parent=None):
  super().__init__(parent); self.season='春日'; self.phase=0; self.setAttribute(Qt.WA_TransparentForMouseEvents); self.setAttribute(Qt.WA_TranslucentBackground)
  self.timer=QTimer(self); self.timer.timeout.connect(self.tick); self.timer.start(42)
 def set_season(self,season): self.season=season; self.phase=0; self.update()
 def tick(self): self.phase=(self.phase+1)%720; self.update()
 def paintEvent(self,event):
  if self.width()<10:return
  import math
  p=QPainter(self); p.setRenderHint(QPainter.Antialiasing); w,h=self.width(),self.height(); t=self.phase/90.0; p.setPen(Qt.NoPen)

  def glow(cx,cy,radius,color,alpha):
   gradient=QRadialGradient(QPointF(cx,cy),radius); gradient.setColorAt(0,QColor(*color,alpha)); gradient.setColorAt(.55,QColor(*color,max(2,alpha//3))); gradient.setColorAt(1,QColor(*color,0)); p.setBrush(QBrush(gradient)); p.drawEllipse(QPointF(cx,cy),radius,radius*.78)

  def organic_blob(cx,cy,sx,sy,color,alpha,seed):
   pulse=1+math.sin(t*.62+seed)*.045; sx*=pulse; sy*=pulse
   path=QPainterPath(); path.moveTo(cx-sx,cy+sy*.05)
   path.cubicTo(cx-sx*.92,cy-sy*.72,cx-sx*.28,cy-sy*1.05,cx+sx*.22,cy-sy*.88)
   path.cubicTo(cx+sx*.92,cy-sy*.72,cx+sx*1.05,cy-sy*.08,cx+sx*.82,cy+sy*.42)
   path.cubicTo(cx+sx*.48,cy+sy*.98,cx-sx*.40,cy+sy*1.02,cx-sx,cy+sy*.05); path.closeSubpath()
   gradient=QLinearGradient(cx-sx,cy-sy,cx+sx,cy+sy); gradient.setColorAt(0,QColor(*color,alpha)); gradient.setColorAt(1,QColor(*color,max(3,alpha//5))); p.setBrush(QBrush(gradient)); p.drawPath(path)

  def soft_ribbon(y,width,color,alpha,phase):
   lift=math.sin(t*.72+phase)*16; path=QPainterPath(); path.moveTo(w*.18,y)
   path.cubicTo(w*.40,y-width+lift,w*.64,y+width-lift,w,y-width*.28)
   path.lineTo(w,y+width*.42); path.cubicTo(w*.72,y+width+lift,w*.42,y-width*.22-lift,w*.18,y+width*.55); path.closeSubpath()
   gradient=QLinearGradient(w*.18,y,w,y); gradient.setColorAt(0,QColor(*color,0)); gradient.setColorAt(.48,QColor(*color,alpha)); gradient.setColorAt(1,QColor(*color,0)); p.setBrush(QBrush(gradient)); p.drawPath(path)

  if self.season=='春日':
   # 水彩般的湿润色块：缓慢相互靠近、分离，像清晨空气正在舒展。
   glow(w*.72+math.sin(t*.42)*42,h*.13,w*.46,(255,218,124),45)
   organic_blob(w*.32+math.sin(t*.48)*24,h*.80,w*.27,h*.20,(151,211,174),32,0)
   organic_blob(w*.88+math.cos(t*.38)*20,h*.55,w*.18,h*.28,(247,174,151),25,2)
   soft_ribbon(h*.31,42,(134,204,180),20,0)
  elif self.season=='盛夏':
   # 日照不是圆形太阳，而是大面积暖光呼吸与空气折射。
   glow(w*.78+math.sin(t*.30)*35,h*.04,w*.56,(255,186,72),70)
   glow(w*.42,h*.95,w*.48,(255,226,121),44)
   soft_ribbon(h*.26,46,(255,164,82),28,1)
   soft_ribbon(h*.68,58,(119,196,171),19,3)
  elif self.season=='秋意':
   # 琥珀色透明薄片错层漂移，保留秋日层次但不画具象叶片。
   glow(w*.82,h*.16,w*.44,(233,155,91),48)
   for i,(cx,cy,sx,sy,color) in enumerate([
    (.30,.82,.20,.13,(210,125,78)),(.72,.72,.24,.16,(176,102,92)),(.90,.34,.13,.20,(226,169,103))]):
    organic_blob(w*cx+math.sin(t*.35+i)*30,h*cy+math.cos(t*.28+i)*18,w*sx,h*sy,color,24+i*3,i)
   soft_ribbon(h*.40,52,(183,107,81),18,2)
  else:
   # 冬季采用透亮的极光薄幕和冰蓝漫反射，安静但不冰冷。
   glow(w*.76,h*.10,w*.48,(174,213,242),55)
   glow(w*.35,h*.92,w*.42,(196,181,231),35)
   soft_ribbon(h*.24,58,(145,191,228),24,0)
   soft_ribbon(h*.60,72,(185,169,220),18,2)
   organic_blob(w*.92+math.sin(t*.30)*16,h*.70,w*.13,h*.28,(226,241,250),32,4)
  p.end()

class SeasonMood(QWidget):
 """标题区中的动态季节胶囊，提供清晰但不打扰编辑的动画焦点。"""
 def __init__(self,parent=None):
  super().__init__(parent); self.season='春日'; self.phase=0; self.setFixedSize(158,50); self.setAttribute(Qt.WA_TransparentForMouseEvents)
  self.timer=QTimer(self); self.timer.timeout.connect(self.tick); self.timer.start(46)
 def set_season(self,season): self.season=season; self.phase=0; self.update()
 def tick(self): self.phase=(self.phase+1)%720; self.update()
 def paintEvent(self,event):
  import math
  p=QPainter(self); p.setRenderHint(QPainter.Antialiasing); w,h=self.width(),self.height(); t=self.phase/75.0
  colors={
   '春日':((246,183,128),(150,211,177),(62,76,61)),
   '盛夏':((255,194,83),(245,142,76),(91,60,25)),
   '秋意':((220,132,83),(184,101,98),(86,53,42)),
   '冬藏':((133,176,224),(185,168,220),(49,63,86))}[self.season]
  clip=QPainterPath(); clip.addRoundedRect(0,0,w,h,16,16); p.setClipPath(clip); p.fillPath(clip,QColor(255,255,255,178)); p.setPen(Qt.NoPen)
  for i,(color,offset) in enumerate(((colors[0],0),(colors[1],2.2))):
   cx=w*(.25+i*.48)+math.sin(t*(.58+i*.12)+offset)*20; cy=h*(.45+i*.12)+math.cos(t*.62+offset)*8
   radius=62-i*8; gradient=QRadialGradient(QPointF(cx,cy),radius); gradient.setColorAt(0,QColor(*color,125)); gradient.setColorAt(1,QColor(*color,0)); p.setBrush(QBrush(gradient)); p.drawEllipse(QPointF(cx,cy),radius,radius*.62)
  p.setClipping(False); p.setPen(QColor(*colors[2])); font=p.font(); font.setPointSize(11); font.setBold(True); p.setFont(font); p.drawText(16,0,w-32,h,Qt.AlignVCenter|Qt.AlignLeft,self.season)
  font.setPointSize(8); font.setBold(False); p.setFont(font); p.setPen(QColor(*colors[2],150)); p.drawText(65,1,w-77,h,Qt.AlignVCenter|Qt.AlignRight,THEMES[self.season][4]); p.end()

