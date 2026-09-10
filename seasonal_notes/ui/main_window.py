import os
import shutil
import uuid
from datetime import date, datetime
from PySide6.QtCore import Qt, QDate, QTimer, QPropertyAnimation, QEasingCurve, QEvent, QSize
from PySide6.QtGui import (
    QFont,
    QTextImageFormat,
    QColor,
    QBrush,
    QTextTableFormat,
    QTextLength,
    QTextCharFormat,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QToolButton,
    QGraphicsDropShadowEffect,
    QDialog,
    QCalendarWidget,
    QSpinBox,
    QCheckBox,
    QListWidgetItem,
    QStackedWidget,
)


from seasonal_notes.storage import ensure_storage, load_notes, save_notes, ATTACHMENTS_DIR
from seasonal_notes.themes import THEMES
from .animations import SeasonalOverlay, SeasonMood
from .editor import NoteEditor
from .note_item import NoteListItem
from .table_preview import TablePreview


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        ensure_storage()
        self.setWindowTitle("季节笔记")
        self.resize(1240, 780)
        self.setMinimumSize(960, 640)
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.notes = self.load()
        self.current = None
        self.theme = "春日"
        self.selected_date = ""
        self.loading_editor = False
        self.build()
        self.apply_theme()
        self.refresh()

    def load(self):
        return load_notes()

    def persist(self):
        save_notes(self.notes)

    def build(self):
        root = QWidget()
        root.setObjectName("root")
        self.root = root
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        def soft_shadow(widget, opacity=28):
            effect = QGraphicsDropShadowEffect(widget)
            effect.setBlurRadius(30)
            effect.setOffset(0, 7)
            effect.setColor(QColor(47, 38, 55, opacity))
            widget.setGraphicsEffect(effect)

        self.side = QWidget()
        self.side.setObjectName("sidebar")
        self.side.setFixedWidth(228)
        sl = QVBoxLayout(self.side)
        sl.setContentsMargins(22, 26, 22, 24)
        sl.setSpacing(7)
        self.logo = QLabel("✦  季节笔记\n     SEASON NOTES")
        self.logo.setObjectName("logo")
        sl.addWidget(self.logo)
        sl.addSpacing(18)
        self.new = QPushButton("＋  新建笔记")
        self.new.setObjectName("primary")
        self.new.clicked.connect(self.new_note)
        self.new.setFixedHeight(44)
        sl.addWidget(self.new)
        sl.addSpacing(20)
        self.all_label = QLabel("笔记空间")
        self.all_label.setObjectName("section")
        sl.addWidget(self.all_label)
        self.all_btn = QPushButton("所有笔记")
        self.all_btn.setObjectName("sideItem")
        self.all_btn.clicked.connect(self.clear_filters)
        sl.addWidget(self.all_btn)
        sl.addSpacing(18)
        sec = QLabel("季节氛围")
        sec.setObjectName("section")
        sl.addWidget(sec)
        self.season_buttons = []
        for n in THEMES:
            b = QPushButton(n)
            b.setObjectName("season")
            b.setCheckable(True)
            b.clicked.connect(lambda _, x=n: self.set_season(x))
            sl.addWidget(b)
            self.season_buttons.append((n, b))
        sl.addStretch()
        self.motion = QPushButton("动态氛围  开")
        self.motion.setObjectName("motionToggle")
        self.motion.setCheckable(True)
        self.motion.setChecked(True)
        self.motion.clicked.connect(self.toggle_motion)
        sl.addWidget(self.motion)
        self.quote = QLabel("去记录，也去感受。\n今天会有新的好事发生。")
        self.quote.setObjectName("quote")
        sl.addWidget(self.quote)
        outer.addWidget(self.side)
        main = QWidget()
        main.setObjectName("main")
        ml = QVBoxLayout(main)
        ml.setContentsMargins(28, 23, 28, 26)
        ml.setSpacing(14)
        outer.addWidget(main, 1)
        head = QHBoxLayout()
        head.setSpacing(12)
        greeting = QVBoxLayout()
        greeting.setSpacing(2)
        hour = datetime.now().hour
        hello = "早上好" if hour < 11 else "午后好" if hour < 18 else "晚上好"
        self.hello = QLabel(hello)
        self.hello.setObjectName("hello")
        greeting.addWidget(self.hello)
        sub = QLabel("把今天的小小闪光，安静地收藏起来。")
        sub.setObjectName("sub")
        greeting.addWidget(sub)
        head.addLayout(greeting)
        head.addStretch()
        self.mood = SeasonMood()
        head.addWidget(self.mood)
        self.status = QLabel("●  内容已保存")
        self.status.setObjectName("status")
        head.addWidget(self.status)
        ml.addLayout(head)
        search_card = QWidget()
        search_card.setObjectName("searchCard")
        bar = QHBoxLayout(search_card)
        bar.setContentsMargins(10, 8, 10, 8)
        bar.setSpacing(8)
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText("搜索笔记内容…")
        self.search.returnPressed.connect(self.refresh)
        bar.addWidget(self.search, 1)
        self.date_button = QPushButton("选择日期  ▾")
        self.date_button.setObjectName("dateButton")
        self.date_button.setMinimumWidth(132)
        self.date_button.clicked.connect(self.choose_date)
        bar.addWidget(self.date_button)
        self.search_btn = QPushButton("查找")
        self.search_btn.setObjectName("compactPrimary")
        self.search_btn.clicked.connect(self.refresh)
        bar.addWidget(self.search_btn)
        self.reset = QPushButton("清空")
        self.reset.setObjectName("quiet")
        self.reset.clicked.connect(self.clear_filters)
        bar.addWidget(self.reset)
        ml.addWidget(search_card)
        soft_shadow(search_card, 18)
        split = QSplitter(Qt.Horizontal)
        split.setObjectName("contentSplit")
        split.setChildrenCollapsible(False)
        ml.addWidget(split, 1)
        left = QWidget()
        left.setObjectName("listCard")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(14, 15, 14, 14)
        ll.setSpacing(10)
        list_head = QHBoxLayout()
        list_title = QLabel("最近笔记")
        list_title.setObjectName("cardTitle")
        list_head.addWidget(list_title)
        list_head.addStretch()
        self.list_count = QLabel("0 篇")
        self.list_count.setObjectName("muted")
        list_head.addWidget(self.list_count)
        ll.addLayout(list_head)
        self.list_stack = QStackedWidget()
        self.list_stack.setObjectName("listStack")
        self.list = QListWidget()
        self.list.setObjectName("noteList")
        self.list.setSpacing(4)
        self.list.currentRowChanged.connect(self.pick)
        self.list_stack.addWidget(self.list)
        self.list_empty = QWidget()
        empty_layout = QVBoxLayout(self.list_empty)
        empty_layout.setContentsMargins(20, 30, 20, 30)
        empty_layout.addStretch()
        empty_icon = QLabel("✦")
        empty_icon.setObjectName("emptyIcon")
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_icon)
        self.empty_title = QLabel("今天还没有笔记")
        self.empty_title.setObjectName("emptyTitle")
        self.empty_title.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.empty_title)
        self.empty_hint = QLabel("写下第一句话，季节就有了形状。")
        self.empty_hint.setObjectName("emptyHint")
        self.empty_hint.setAlignment(Qt.AlignCenter)
        self.empty_hint.setWordWrap(True)
        empty_layout.addWidget(self.empty_hint)
        empty_layout.addStretch()
        self.list_stack.addWidget(self.list_empty)
        ll.addWidget(self.list_stack)
        split.addWidget(left)
        soft_shadow(left)
        right = QWidget()
        right.setObjectName("editorCard")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(22, 18, 22, 18)
        rl.setSpacing(9)
        top = QHBoxLayout()
        self.title = QLineEdit()
        self.title.setPlaceholderText("无标题笔记")
        self.title.setObjectName("title")
        top.addWidget(self.title, 1)
        self.favorite = QPushButton("☆ 收藏")
        self.favorite.setObjectName("quiet")
        self.favorite.clicked.connect(self.toggle_favorite)
        top.addWidget(self.favorite)
        rl.addLayout(top)
        self.meta = QLabel("选择一篇笔记，或开始新的记录")
        self.meta.setObjectName("meta")
        rl.addWidget(self.meta)
        tools = QHBoxLayout()
        tools.setSpacing(6)
        self.format_buttons = {}
        for text, fn in [
            ("B", lambda: self.fmt("bold")),
            ("I", lambda: self.fmt("italic")),
            ("U", lambda: self.fmt("underline")),
            ("清单", self.checklist),
            ("表格", self.table),
            ("图片", self.image),
        ]:
            b = QToolButton()
            b.setText(text)
            b.clicked.connect(fn)
            if text in ("B", "I", "U"):
                b.setCheckable(True)
                b.setShortcut({"B": "Meta+B", "I": "Meta+I", "U": "Meta+U"}[text])
                self.format_buttons[text] = b
            tools.addWidget(b)
        tools.addStretch()
        self.delete_btn = QPushButton("删除")
        self.delete_btn.setObjectName("danger")
        self.delete_btn.clicked.connect(self.delete_note)
        tools.addWidget(self.delete_btn)
        rl.addLayout(tools)
        self.editor = NoteEditor()
        self.editor.setObjectName("editor")
        self.editor.setPlaceholderText(
            "从这里开始记录…\n\n文字没有长度限制，也可以插入可勾选清单、网格表格和图片。"
        )
        rl.addWidget(self.editor, 1)
        footer = QHBoxLayout()
        footer.addStretch()
        self.save = QPushButton("保存这一刻")
        self.save.setObjectName("primary")
        self.save.clicked.connect(self.save_note)
        self.save.setFixedWidth(128)
        footer.addWidget(self.save)
        rl.addLayout(footer)
        split.addWidget(right)
        soft_shadow(right)
        split.setSizes([300, 700])
        split.setHandleWidth(14)
        self.overlay = SeasonalOverlay(root)
        self.overlay.lower()
        self.root.resizeEvent = lambda e: (
            self.overlay.resize(self.root.size()),
            QWidget.resizeEvent(self.root, e),
        )
        self.overlay.resize(root.size())
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.setInterval(900)
        self.autosave_timer.timeout.connect(self.auto_save)
        self.title.textChanged.connect(self.schedule_autosave)
        self.editor.textChanged.connect(self.schedule_autosave)
        self.editor.currentCharFormatChanged.connect(self.sync_format_buttons)

    def toggle_motion(self, enabled):
        self.overlay.set_animation_enabled(enabled)
        self.mood.set_animation_enabled(enabled)
        self.motion.setText("动态氛围  开" if enabled else "动态氛围  关")

    def style(self):
        bg, panel, accent, text, _ = THEMES[self.theme]
        panel_color = QColor(panel)
        sidebar_color = QColor(bg).lighter(103)
        panel_rgba = f"rgba({panel_color.red()},{panel_color.green()},{panel_color.blue()},239)"
        sr, sg, sb = sidebar_color.red(), sidebar_color.green(), sidebar_color.blue()
        sidebar_rgba = (f"qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                        f"stop:0 rgba({sr},{sg},{sb},240),"
                        f"stop:0.60 rgba({sr},{sg},{sb},226),"
                        f"stop:0.79 rgba({sr},{sg},{sb},45),"
                        f"stop:1 rgba({sr},{sg},{sb},210))")
        selected = {"春日": "#ffead9", "盛夏": "#ffebc7", "秋意": "#f7dfd0", "冬藏": "#e2edf8"}[
            self.theme
        ]
        accent2 = QColor(accent).lighter(118).name()
        self.setStyleSheet(f"""
   QMainWindow,#root{{background:{bg};}} #main{{background:transparent;}} QWidget{{font-family:"SF Pro Display","PingFang SC",Arial;color:{text};font-size:13px;}}
#sidebar{{background:{sidebar_rgba};border-right:1px solid {QColor(bg).darker(104).name()};}}
	 #logo{{font-size:18px;font-weight:700;line-height:1.2;letter-spacing:1px;}} #hello{{font-size:28px;font-weight:700;}} #sub,#meta,#status,#quote,#muted{{color:{accent};}} #sub{{font-size:12px;}} #quote{{font-size:12px;line-height:1.6;}}
   #hello,#sub,#status{{background:rgba(255,250,241,220);border-radius:8px;padding:4px 10px;}}
   #quote{{background:rgba(255,250,241,225);border-radius:8px;padding:7px;color:{text};}}
   #section{{font-size:11px;font-weight:700;color:{QColor(text).lighter(145).name()};margin:5px 0;letter-spacing:1px;}}
	 QPushButton,QToolButton{{border:0;border-radius:10px;padding:8px 13px;background:{QColor(panel).darker(101).name()};color:{text};font-weight:600;}}
  	 QPushButton:hover,QToolButton:hover{{background:{selected};}} QToolButton:checked{{background:{accent};color:white;}} #primary,#compactPrimary{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {accent},stop:1 {accent2});color:white;}} #primary:hover,#compactPrimary:hover{{background:{accent2};}}
  	 #sideItem,#season{{text-align:left;background:transparent;padding:10px 12px;}} #sideItem:hover,#season:hover{{background:{selected};}}
  	 #season:checked{{background:{panel};color:{accent};font-weight:700;border:1px solid {selected};}}
	 #searchCard,#listCard,#editorCard{{background:{panel_rgba};border:1px solid {QColor(bg).darker(104).name()};border-radius:18px;}}
  	 #search,#dateButton{{background:{QColor(bg).lighter(106).name()};border:0;border-radius:8px;padding:9px 11px;selection-background-color:{accent};}} #dateButton{{text-align:left;}}
   #dateButton[activeDate="true"]{{background:{selected};color:{accent};font-weight:700;}}
   #search{{min-height:20px;}} #quiet{{background:transparent;color:{accent};}} #danger{{background:transparent;color:#a75b54;}}
  	 #cardTitle{{font-size:15px;font-weight:700;}} #title{{font-size:25px;font-weight:700;border:0;background:transparent;padding:3px 0;}}
   #noteList,#listStack{{background:transparent;border:0;outline:0;}} #noteList::item{{padding:0;border:0;}} #noteItem{{background:transparent;border-radius:12px;}} #noteItem:hover{{background:{bg};}} #noteItem[selected="true"]{{background:{selected};}} #noteItemTitle{{font-size:14px;font-weight:700;}} #notePreview{{font-size:12px;color:{QColor(text).lighter(138).name()};}} #noteItemMeta{{font-size:11px;color:{accent};}} #noteFavorite{{color:{accent};font-size:13px;}} #emptyIcon{{font-size:28px;color:{accent};}} #emptyTitle{{font-size:15px;font-weight:700;}} #emptyHint{{font-size:12px;color:{QColor(text).lighter(145).name()};}} #motionToggle{{text-align:left;background:transparent;color:{QColor(text).lighter(135).name()};font-size:11px;padding:8px 10px;}}
   #editor{{background:transparent;border:0;border-top:1px solid {bg};padding:16px 3px;font-size:15px;selection-background-color:{selected};}}
   QSplitter::handle{{background:transparent;}} QDialog#sheetDialog{{background:{panel};}} #dialogTitle{{font-size:21px;font-weight:700;}} #dialogSub{{font-size:12px;color:{accent};}} #dialogCard{{background:{bg};border-radius:14px;}} #selectedDate{{font-size:17px;font-weight:700;color:{accent};padding:8px;}}
   QSpinBox{{background:{panel};border:1px solid {selected};border-radius:9px;padding:7px 10px;min-width:74px;}} QCheckBox{{spacing:8px;}}
   QCalendarWidget QWidget{{background:{panel};}} QCalendarWidget QToolButton{{color:{text};padding:7px;}} QCalendarWidget QAbstractItemView:enabled{{selection-background-color:{accent};selection-color:white;alternate-background-color:{panel};outline:0;}} QCalendarWidget QTableView{{border:0;}}
   """)

    def apply_theme(self):
        self.style()
        self.overlay.set_season(self.theme)
        self.mood.set_season(self.theme)
        self.quote.setText(self.overlay.SCENE_NAMES[self.theme] + "\n让风景陪你，慢慢写。")
        self.mood.setToolTip(self.overlay.SCENE_NAMES[self.theme])
        for name, button in self.season_buttons:
            button.setChecked(name == self.theme)
        self.refresh()

    def set_season(self, n):
        self.theme = n
        self.overlay.set_season(n)
        self.apply_theme()
        self.animate_theme()

    def animate_theme(self):
        from PySide6.QtWidgets import QGraphicsOpacityEffect

        effect = QGraphicsOpacityEffect(self.overlay)
        self.overlay.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(480)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        self._theme_anim = anim

    def choose_date(self):
        dialog = QDialog(self)
        dialog.setObjectName("sheetDialog")
        dialog.setWindowTitle("按日期查找笔记")
        dialog.setModal(True)
        dialog.setFixedWidth(440)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(22, 22, 22, 18)
        layout.setSpacing(13)
        title = QLabel("选择记录日期")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        hint = QLabel("快速回到某一天，看看当时写下了什么。")
        hint.setObjectName("dialogSub")
        layout.addWidget(hint)
        quick = QHBoxLayout()
        quick.setSpacing(8)
        today = QPushButton("今天")
        yesterday = QPushButton("昨天")
        quick.addWidget(today)
        quick.addWidget(yesterday)
        quick.addStretch()
        layout.addLayout(quick)
        calendar = QCalendarWidget()
        calendar.setObjectName("dateCalendar")
        calendar.setGridVisible(False)
        calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calendar.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)
        calendar.setMinimumHeight(285)
        if self.selected_date:
            calendar.setSelectedDate(QDate.fromString(self.selected_date, "yyyy-MM-dd"))
        layout.addWidget(calendar)
        selected = QLabel()
        selected.setObjectName("selectedDate")
        selected.setAlignment(Qt.AlignCenter)
        layout.addWidget(selected)

        def show_selected():
            selected.setText(calendar.selectedDate().toString("yyyy 年 MM 月 dd 日"))

        def choose_quick(value):
            calendar.setSelectedDate(value)
            show_selected()

        today.clicked.connect(lambda: choose_quick(QDate.currentDate()))
        yesterday.clicked.connect(lambda: choose_quick(QDate.currentDate().addDays(-1)))
        calendar.selectionChanged.connect(show_selected)
        show_selected()
        actions = QHBoxLayout()
        clear = QPushButton("清除筛选")
        clear.setObjectName("quiet")
        cancel = QPushButton("取消")
        choose = QPushButton("查看这一天")
        choose.setObjectName("compactPrimary")
        choose.setMinimumWidth(108)
        actions.addWidget(clear)
        actions.addStretch()
        actions.addWidget(cancel)
        actions.addWidget(choose)
        layout.addLayout(actions)

        def apply_selected():
            self.selected_date = calendar.selectedDate().toString("yyyy-MM-dd")
            self.update_date_button()
            dialog.accept()
            self.refresh()

        def clear_selected():
            self.selected_date = ""
            self.update_date_button()
            dialog.accept()
            self.refresh()

        choose.clicked.connect(apply_selected)
        calendar.activated.connect(lambda _: apply_selected())
        clear.clicked.connect(clear_selected)
        cancel.clicked.connect(dialog.reject)
        dialog.exec()

    def update_date_button(self):
        self.date_button.setText(
            ("日期  " + self.selected_date if self.selected_date else "选择日期") + "  ▾"
        )
        self.date_button.setProperty("activeDate", bool(self.selected_date))
        self.date_button.style().unpolish(self.date_button)
        self.date_button.style().polish(self.date_button)

    def clear_filters(self):
        self.search.clear()
        self.selected_date = ""
        self.update_date_button()
        self.refresh()

    def refresh(self, select_id=None):
        q = self.search.text().strip().lower()
        ds = self.selected_date
        items = [
            n
            for n in self.notes
            if (not q or q in (n.get("title", "") + n.get("body", "") + n.get("date", "")).lower())
            and (not ds or n.get("date", "") == ds)
        ]
        self.list.blockSignals(True)
        self.list.clear()
        for n in items:
            item = QListWidgetItem()
            item.setSizeHint(QSize(240, 82))
            item.setData(Qt.UserRole, n.get("id"))
            self.list.addItem(item)
            self.list.setItemWidget(item, NoteListItem(n))
        self.list.blockSignals(False)
        self.visible = items
        self.all_btn.setText(f"所有笔记   {len(self.notes)}")
        self.list_count.setText(f"{len(items)} 篇")
        self.list_stack.setCurrentWidget(self.list if items else self.list_empty)
        if not items:
            filtering = bool(q or ds)
            self.empty_title.setText("没有找到匹配的笔记" if filtering else "今天还没有笔记")
            self.empty_hint.setText(
                "换个关键词或清空日期再试试。" if filtering else "写下第一句话，季节就有了形状。"
            )
        if items:
            wanted = select_id or (self.current.get("id") if self.current else None)
            row = next((i for i, n in enumerate(items) if n.get("id") == wanted), 0)
            self.list.setCurrentRow(row)

    def pick(self, row):
        if row < 0 or row >= len(getattr(self, "visible", [])):
            return
        self.autosave_timer.stop()
        self.loading_editor = True
        n = self.visible[row]
        self.current = n
        for index in range(self.list.count()):
            widget = self.list.itemWidget(self.list.item(index))
            if widget:
                widget.set_selected(index == row)
        self.title.setText(n.get("title", ""))
        if n.get("body_html"):
            self.editor.setHtml(n["body_html"])
        else:
            self.editor.setPlainText(n.get("body", ""))
        self.meta.setText(f"{n.get('date', '')}  ·  {n.get('season', '春日')}")
        self.favorite.setText("★ 已收藏" if n.get("favorite") else "☆ 收藏")
        self.loading_editor = False
        self.sync_format_buttons(self.editor.currentCharFormat())

    def new_note(self):
        self.autosave_timer.stop()
        self.loading_editor = True
        self.current = None
        self.title.clear()
        self.editor.clear()
        self.meta.setText(date.today().isoformat() + f"  ·  {self.theme}")
        self.favorite.setText("☆ 收藏")
        self.loading_editor = False
        self.editor.setFocus()

    def schedule_autosave(self):
        if self.loading_editor:
            return
        self.status.setText("●  正在编辑…")
        self.autosave_timer.start()

    def auto_save(self):
        if self.loading_editor:
            return
        if self.current or self.title.text().strip() or self.editor.toPlainText().strip():
            self.save_note(True)

    def save_note(self, silent=False):
        t = self.title.text().strip() or "无标题"
        b = self.editor.toPlainText()
        html = self.editor.toHtml()
        n = self.current or {
            "id": str(uuid.uuid4()),
            "date": date.today().isoformat(),
            "favorite": False,
        }
        n.update(title=t, body=b, body_html=html, season=self.theme)
        if not self.current:
            self.notes.insert(0, n)
        self.current = n
        self.persist()
        self.status.setText("●  已自动保存" if silent else "●  内容已保存")
        self.refresh(n["id"])

    def delete_note(self):
        if not self.current:
            return
        if QMessageBox.question(self, "删除笔记", "确定删除当前笔记吗？") == QMessageBox.Yes:
            self.notes = [n for n in self.notes if n["id"] != self.current["id"]]
            self.current = None
            self.persist()
            self.new_note()
            self.refresh()

    def toggle_favorite(self):
        if not self.current:
            self.save_note()
        if self.current:
            self.current["favorite"] = not self.current.get("favorite", False)
            self.favorite.setText("★ 已收藏" if self.current["favorite"] else "☆ 收藏")
            self.persist()

    def fmt(self, kind):
        cur = self.editor.textCursor()
        fmt = cur.charFormat()
        if kind == "bold":
            fmt.setFontWeight(QFont.Normal if fmt.fontWeight() >= QFont.Bold else QFont.Bold)
        if kind == "italic":
            fmt.setFontItalic(not fmt.fontItalic())
        if kind == "underline":
            fmt.setFontUnderline(not fmt.fontUnderline())
        self.editor.mergeCurrentCharFormat(fmt)
        self.sync_format_buttons(fmt)
        self.editor.setFocus()

    def sync_format_buttons(self, fmt):
        states = {
            "B": fmt.fontWeight() >= QFont.Bold,
            "I": fmt.fontItalic(),
            "U": fmt.fontUnderline(),
        }
        for name, button in self.format_buttons.items():
            button.blockSignals(True)
            button.setChecked(states[name])
            button.blockSignals(False)

    def checklist(self):
        cursor = self.editor.textCursor()
        if cursor.block().text():
            cursor.insertBlock()
        checkbox_format = QTextCharFormat()
        checkbox_format.setFontPointSize(16)
        checkbox_format.setForeground(QColor(THEMES[self.theme][2]))
        cursor.insertText("☐", checkbox_format)
        text_format = QTextCharFormat()
        text_format.setFontPointSize(14)
        cursor.insertText("  请输入待办事项", text_format)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def table(self):
        dialog = QDialog(self)
        dialog.setObjectName("sheetDialog")
        dialog.setWindowTitle("插入表格")
        dialog.setModal(True)
        dialog.setFixedWidth(460)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(22, 22, 22, 18)
        layout.setSpacing(13)
        title = QLabel("创建一个表格")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        subtitle = QLabel("先选择结构，插入后可直接输入，按 Tab 快速切换单元格。")
        subtitle.setObjectName("dialogSub")
        layout.addWidget(subtitle)
        preset_label = QLabel("常用尺寸")
        preset_label.setObjectName("section")
        layout.addWidget(preset_label)
        presets = QHBoxLayout()
        presets.setSpacing(8)
        rows = QSpinBox()
        rows.setObjectName("tableRows")
        rows.setRange(1, 20)
        rows.setValue(3)
        rows.setSuffix(" 行")
        columns = QSpinBox()
        columns.setObjectName("tableColumns")
        columns.setRange(1, 10)
        columns.setValue(3)
        columns.setSuffix(" 列")
        for label, r, c in [("2 × 2", 2, 2), ("3 × 3", 3, 3), ("4 × 3", 4, 3), ("5 × 4", 5, 4)]:
            button = QPushButton(label)
            button.setObjectName("preset")
            button.clicked.connect(lambda _, rv=r, cv=c: (rows.setValue(rv), columns.setValue(cv)))
            presets.addWidget(button)
        layout.addLayout(presets)
        settings = QWidget()
        settings.setObjectName("dialogCard")
        settings_layout = QHBoxLayout(settings)
        settings_layout.setContentsMargins(14, 12, 14, 12)
        settings_layout.setSpacing(12)
        settings_layout.addWidget(QLabel("数据行"))
        settings_layout.addWidget(rows)
        settings_layout.addSpacing(8)
        settings_layout.addWidget(QLabel("列数"))
        settings_layout.addWidget(columns)
        settings_layout.addStretch()
        header = QCheckBox("包含表头")
        header.setObjectName("tableHeader")
        header.setChecked(True)
        settings_layout.addWidget(header)
        layout.addWidget(settings)
        preview = TablePreview()
        preview.setObjectName("tablePreview")
        layout.addWidget(preview)

        def update_preview():
            preview.configure(rows.value(), columns.value(), header.isChecked())

        rows.valueChanged.connect(lambda _: update_preview())
        columns.valueChanged.connect(lambda _: update_preview())
        header.toggled.connect(lambda _: update_preview())
        update_preview()
        actions = QHBoxLayout()
        cancel = QPushButton("取消")
        insert = QPushButton("插入表格")
        insert.setObjectName("compactPrimary")
        insert.setMinimumWidth(108)
        actions.addStretch()
        actions.addWidget(cancel)
        actions.addWidget(insert)
        layout.addLayout(actions)
        cancel.clicked.connect(dialog.reject)
        insert.clicked.connect(dialog.accept)
        if dialog.exec() != QDialog.Accepted:
            return
        r, c, has_header = rows.value(), columns.value(), header.isChecked()
        cursor = self.editor.textCursor()
        if cursor.block().text():
            cursor.insertBlock()
        table_format = QTextTableFormat()
        table_format.setBorder(1.15)
        table_format.setBorderBrush(QBrush(QColor(THEMES[self.theme][2]).lighter(145)))
        table_format.setCellPadding(9)
        table_format.setCellSpacing(0)
        table_format.setWidth(QTextLength(QTextLength.PercentageLength, 100))
        if hasattr(table_format, "setBorderCollapse"):
            table_format.setBorderCollapse(True)
        total_rows = r + (1 if has_header else 0)
        table = cursor.insertTable(total_rows, c, table_format)
        header_color = QColor(THEMES[self.theme][2]).lighter(185)
        for row in range(total_rows):
            for column in range(c):
                cell = table.cellAt(row, column)
                cell_format = cell.format()
                cell_format.setBackground(
                    header_color
                    if has_header and row == 0
                    else QColor("#fffaf4" if row % 2 else "#fff5eb")
                )
                cell.setFormat(cell_format)
                if has_header and row == 0:
                    header_cursor = cell.firstCursorPosition()
                    char_format = QTextCharFormat()
                    char_format.setFontWeight(QFont.Bold)
                    header_cursor.setCharFormat(char_format)
                    header_cursor.insertText(f"列 {column + 1}")
        target = table.cellAt(1 if has_header else 0, 0).firstCursorPosition()
        self.editor.setTextCursor(target)
        self.editor.setFocus()
        self.status.setText(f"●  已插入 {r} × {c} 表格")

    def image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "插入图片", "", "Images (*.png *.jpg *.jpeg *.gif)"
        )
        if path:
            os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
            extension = os.path.splitext(path)[1].lower() or ".png"
            stored = os.path.join(ATTACHMENTS_DIR, str(uuid.uuid4()) + extension)
            try:
                shutil.copy2(path, stored)
            except OSError as error:
                QMessageBox.warning(self, "图片插入失败", f"无法保存图片副本：\n{error}")
                return
            fmt = QTextImageFormat()
            fmt.setName(stored)
            fmt.setWidth(min(520, max(280, self.editor.viewport().width() - 40)))
            self.editor.textCursor().insertImage(fmt)
            self.editor.setFocus()

    def closeEvent(self, event):
        self.autosave_timer.stop()
        if not self.loading_editor and (
            self.current or self.title.text().strip() or self.editor.toPlainText().strip()
        ):
            self.save_note(True)
        event.accept()

    def changeEvent(self, event):
        super().changeEvent(event)
        if hasattr(self, "overlay") and event.type() == QEvent.ActivationChange:
            active = self.isActiveWindow() and self.motion.isChecked()
            self.overlay.set_animation_enabled(active)
            self.mood.set_animation_enabled(active)
