import json, os, uuid, sys
from datetime import date
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QAction, QFont, QTextCursor, QTextImageFormat
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QLabel, QPushButton, QLineEdit, QTextEdit, QSplitter, QFileDialog, QMessageBox,
    QDateEdit, QToolButton, QInputDialog)

ROOT=os.path.dirname(os.path.abspath(__file__)); DATA=os.path.join(ROOT,'notes.json')
THEMES={
 '春日':('#dfeee2','#f9fcf8','#2f7f4f','#183d27','🌱'),
 '盛夏':('#fff0cb','#fffdf7','#c76d10','#56370f','☀'),
 '秋意':('#f3dfd2','#fffaf7','#a44d2d','#54291d','🍂'),
 '冬藏':('#dcecf5','#fbfdff','#3977a6','#203f57','❄')}

class App(QMainWindow):
 def __init__(self):
  super().__init__(); self.setWindowTitle('季节笔记'); self.resize(1240,780); self.notes=self.load(); self.current=None; self.theme='春日'; self.build(); self.apply_theme(); self.refresh()
 def load(self):
  	try:
  		with open(DATA,encoding='utf8') as f:return json.load(f)
  	except Exception:return []
 def persist(self):
  	with open(DATA,'w',encoding='utf8') as f: json.dump(self.notes,f,ensure_ascii=False,indent=2)
 def build(self):
  	root=QWidget(); self.setCentralWidget(root); outer=QHBoxLayout(root); outer.setContentsMargins(0,0,0,0)
  	self.side=QWidget(); self.side.setFixedWidth(245); sl=QVBoxLayout(self.side); sl.setContentsMargins(24,28,24,24); sl.setSpacing(8)
  	self.logo=QLabel('✽  季节笔记\n    SEASON NOTES'); self.logo.setObjectName('logo'); sl.addWidget(self.logo)
  	self.new=QPushButton('＋  新建笔记'); self.new.clicked.connect(self.new_note); sl.addWidget(self.new); sl.addSpacing(24)
  	self.all_label=QLabel('笔记空间'); self.all_label.setObjectName('section'); sl.addWidget(self.all_label); self.all_btn=QPushButton('▤  所有笔记     0'); self.all_btn.setObjectName('sideItem'); self.all_btn.clicked.connect(self.clear_filters); sl.addWidget(self.all_btn); sl.addSpacing(22)
  	sec=QLabel('季节主题'); sec.setObjectName('section'); sl.addWidget(sec); self.season_buttons=[]
  	for n in THEMES:
  		b=QPushButton(f'{THEMES[n][4]}  {n}'); b.setObjectName('season'); b.clicked.connect(lambda _,x=n:self.set_season(x)); sl.addWidget(b); self.season_buttons.append((n,b))
  	sl.addStretch(); self.quote=QLabel('“把日子写下来，\n时间就有了形状。”'); self.quote.setObjectName('quote'); sl.addWidget(self.quote)
  	outer.addWidget(self.side)
  	main=QWidget(); ml=QVBoxLayout(main); ml.setContentsMargins(32,26,32,28); ml.setSpacing(12); outer.addWidget(main)
  	head=QHBoxLayout(); h=QLabel('你好，Lena'); h.setObjectName('hello'); head.addWidget(h); head.addStretch(); self.status=QLabel('● 已自动保存'); self.status.setObjectName('status'); head.addWidget(self.status); ml.addLayout(head)
  	sub=QLabel('记录微小的变化，也记录此刻的自己。'); sub.setObjectName('sub'); ml.addWidget(sub)
  	bar=QHBoxLayout(); self.search=QLineEdit(); self.search.setPlaceholderText('搜索标题、内容'); self.search.returnPressed.connect(self.refresh); bar.addWidget(self.search,1); self.date=QDateEdit(calendarPopup=True); self.date.setDisplayFormat('yyyy-MM-dd'); self.date.setMinimumDate(QDate(2000,1,1)); self.date.setSpecialValueText('选择日期'); self.date.setDate(QDate(2000,1,1)); self.date.dateChanged.connect(self.refresh); bar.addWidget(self.date); self.search_btn=QPushButton('搜索'); self.search_btn.clicked.connect(self.refresh); bar.addWidget(self.search_btn); self.reset=QPushButton('重置'); self.reset.clicked.connect(self.clear_filters); bar.addWidget(self.reset); ml.addLayout(bar)
  	split=QSplitter(Qt.Horizontal); split.setChildrenCollapsible(False); ml.addWidget(split,1)
  	left=QWidget(); ll=QVBoxLayout(left); ll.setContentsMargins(0,0,12,0); self.list=QListWidget(); self.list.currentRowChanged.connect(self.pick); ll.addWidget(self.list); split.addWidget(left)
  	right=QWidget(); rl=QVBoxLayout(right); rl.setContentsMargins(12,0,0,0)
  	top=QHBoxLayout(); self.title=QLineEdit(); self.title.setPlaceholderText('无标题'); self.title.setObjectName('title'); top.addWidget(self.title,1); self.favorite=QPushButton('☆ 收藏'); self.favorite.clicked.connect(self.toggle_favorite); top.addWidget(self.favorite); rl.addLayout(top)
  	self.meta=QLabel(''); self.meta.setObjectName('meta'); rl.addWidget(self.meta)
  	tools=QHBoxLayout()
  	for text,fn in [('B',lambda:self.fmt('bold')),('I',lambda:self.fmt('italic')),('U',lambda:self.fmt('underline')),('☷ 清单',self.checklist),('▦ 表格',self.table),('▧ 图片',self.image)]:
  		b=QToolButton(); b.setText(text); b.clicked.connect(fn); tools.addWidget(b)
  	tools.addStretch(); self.delete_btn=QPushButton('删除'); self.delete_btn.clicked.connect(self.delete_note); tools.addWidget(self.delete_btn); rl.addLayout(tools)
  	self.editor=QTextEdit(); self.editor.setPlaceholderText('从这里开始记录……\n\n文本长度不受限制，图片可以插入正文。'); rl.addWidget(self.editor,1); self.save=QPushButton('保存笔记'); self.save.clicked.connect(self.save_note); rl.addWidget(self.save,0,Qt.AlignRight); split.addWidget(right); split.setSizes([280,700])
 def style(self):
  	bg,panel,accent,text,_=THEMES[self.theme]; self.setStyleSheet(f'''QMainWindow{{background:{bg};}} QWidget{{font-family:Arial;color:{text};}} #logo{{font-size:20px;font-weight:700;margin-bottom:18px;}} #hello{{font-size:30px;font-weight:700;}} #sub,#meta,#status,#quote{{color:{accent};}} #section{{font-size:12px;font-weight:700;margin-top:8px;}} QPushButton,QToolButton{{border:0;border-radius:7px;padding:9px 14px;background:{panel};color:{text};}} QPushButton:hover,QToolButton:hover{{background:{accent};color:white;}} #sideItem{{text-align:left;background:transparent;color:{accent};font-size:13px;}} #season{{text-align:left;background:{panel};margin:2px 0;}} #new{{background:{accent};color:white;font-weight:700;padding:12px;}} QLineEdit,QTextEdit,QListWidget,QDateEdit{{background:{panel};border:1px solid {bg};border-radius:8px;padding:9px;color:{text};}} #title{{font-size:22px;font-weight:700;border:0;background:transparent;padding:4px;}} QListWidget::item{{padding:14px 8px;border-bottom:1px solid {bg};}} QListWidget::item:selected{{background:{accent};color:white;border-radius:7px;}} QSplitter::handle{{background:{bg};width:8px;}}''')
 def apply_theme(self): self.style(); bg,panel,accent,text,_=THEMES[self.theme]; self.new.setObjectName('new'); self.new.setStyleSheet(f'background:{accent};color:white;font-weight:700;padding:12px;border-radius:7px;'); self.save.setStyleSheet(f'background:{accent};color:white;font-weight:700;padding:10px 18px;border-radius:7px;'); self.refresh()
 def set_season(self,n): self.theme=n; self.apply_theme();
 def clear_filters(self): self.search.clear(); self.date.setDate(QDate(2000,1,1)); self.refresh()
 def refresh(self):
  	q=self.search.text().strip().lower(); ds=self.date.date().toString('yyyy-MM-dd') if self.date.date()!=QDate(2000,1,1) else ''
  	items=[n for n in self.notes if (not q or q in (n.get('title','')+n.get('body','')+n.get('date','')).lower()) and (not ds or n.get('date','')==ds)]; self.list.blockSignals(True); self.list.clear()
  	for n in items:self.list.addItem(f"{n.get('title') or '无标题'}\n{n.get('date','')}  ·  {n.get('season','春日')}")
  	self.list.blockSignals(False); self.visible=items; self.all_btn.setText(f'▤  所有笔记     {len(self.notes)}')
  	if items:self.list.setCurrentRow(0)
 def pick(self,row):
  	if row<0 or row>=len(getattr(self,'visible',[])):return
  	n=self.visible[row]; self.current=n; self.title.setText(n.get('title','')); self.editor.setPlainText(n.get('body','')); self.meta.setText(f"{n.get('date','')}  ·  {n.get('season','春日')}"); self.favorite.setText('★ 已收藏' if n.get('favorite') else '☆ 收藏')
 def new_note(self): self.current=None; self.title.clear(); self.editor.clear(); self.meta.setText(date.today().isoformat()+f'  ·  {self.theme}'); self.favorite.setText('☆ 收藏'); self.editor.setFocus()
 def save_note(self):
  	t=self.title.text().strip() or '无标题'; b=self.editor.toPlainText(); n=self.current or {'id':str(uuid.uuid4()),'date':date.today().isoformat(),'favorite':False}; n.update(title=t,body=b,season=self.theme)
  	if not self.current:self.notes.insert(0,n)
  	self.current=n; self.persist(); self.status.setText('● 已自动保存'); self.refresh()
 def delete_note(self):
  	if not self.current:return
  	if QMessageBox.question(self,'删除笔记','确定删除当前笔记吗？')==QMessageBox.Yes:self.notes=[n for n in self.notes if n['id']!=self.current['id']]; self.current=None; self.persist(); self.new_note(); self.refresh()
 def toggle_favorite(self):
  	if self.current:self.current['favorite']=not self.current.get('favorite',False); self.favorite.setText('★ 已收藏' if self.current['favorite'] else '☆ 收藏'); self.persist()
 def fmt(self,kind):
  	cur=self.editor.textCursor(); fmt=cur.charFormat(); fmt.setFontWeight(QFont.Bold if kind=='bold' else fmt.fontWeight());
  	if kind=='italic':fmt.setFontItalic(not fmt.fontItalic())
  	if kind=='underline':fmt.setFontUnderline(not fmt.fontUnderline())
  	self.editor.mergeCurrentCharFormat(fmt)
 def checklist(self):self.editor.textCursor().insertText('☐ ')
 def table(self):
  	r,ok=QInputDialog.getInt(self,'插入表格','行数：',3,1,20); 
  	if ok:
  		c,ok=QInputDialog.getInt(self,'插入表格','列数：',2,1,10)
  		if ok:self.editor.textCursor().insertText('\n'+'\t'.join('列'+str(i+1) for i in range(c))+'\n'+'\n'.join('\t'.join(' ' for _ in range(c)) for _ in range(r))+'\n')
 def image(self):
  	path,_=QFileDialog.getOpenFileName(self,'插入图片','', 'Images (*.png *.jpg *.jpeg *.gif)');
  	if path:
  		fmt=QTextImageFormat(); fmt.setName(path); fmt.setWidth(420); self.editor.textCursor().insertImage(fmt)

if __name__=='__main__':
 app=QApplication(sys.argv); w=App(); w.show(); sys.exit(app.exec())
