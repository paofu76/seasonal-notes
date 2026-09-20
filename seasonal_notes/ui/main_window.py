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
    QImage,
    QKeySequence,
    QShortcut,
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
    QMenu,
    QComboBox,
)


from seasonal_notes.storage import (
    ATTACHMENTS_DIR,
    BACKUP_DIR,
    cleanup_attachments,
    create_daily_backup,
    ensure_storage,
    export_archive,
    import_archive,
    load_notes,
    load_settings,
    save_notes,
    save_settings,
)
from seasonal_notes.themes import THEMES
from .animations import SeasonalOverlay, SeasonMood
from .editor import NoteEditor
from .note_item import NoteListItem
from .note_calendar import NoteCalendar
from .table_preview import TablePreview


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        ensure_storage()
        create_daily_backup()
        self.preferences = load_settings()
        self.setWindowTitle("季节笔记")
        window_size = self.preferences.get("window_size", [1240, 780])
        if not isinstance(window_size, list) or len(window_size) != 2:
            window_size = [1240, 780]
        self.resize(max(960, int(window_size[0])), max(640, int(window_size[1])))
        self.setMinimumSize(960, 640)
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.notes = self.load()
        self.current = None
        self.theme = self.preferences.get("theme", "春日")
        if self.theme not in THEMES:
            self.theme = "春日"
        self.selected_date = ""
        self.favorite_only = False
        self.archive_only = False
        self.trash_only = False
        self.draft_date = date.today().isoformat()
        self.draft_folder = "随手记"
        self.draft_tags = []
        self.draft_archived = False
        self.loading_editor = False
        self.build()
        split_sizes = self.preferences.get("split_sizes")
        if isinstance(split_sizes, list) and len(split_sizes) == 2:
            self.split.setSizes([max(220, int(value)) for value in split_sizes])
        motion_enabled = bool(self.preferences.get("motion", True))
        self.motion.setChecked(motion_enabled)
        self.toggle_motion(motion_enabled)
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
        outer = QVBoxLayout(root)
        outer.setContentsMargins(16, 14, 16, 16)
        outer.setSpacing(12)

        def soft_shadow(widget, opacity=28):
            effect = QGraphicsDropShadowEffect(widget)
            effect.setBlurRadius(30)
            effect.setOffset(0, 7)
            effect.setColor(QColor(47, 38, 55, opacity))
            widget.setGraphicsEffect(effect)

        self.side = QWidget()
        self.side.setObjectName("topDock")
        self.side.setFixedHeight(72)
        sl = QHBoxLayout(self.side)
        sl.setContentsMargins(18, 11, 12, 11)
        sl.setSpacing(7)
        self.logo = QLabel("SEASON / 季节手记")
        self.logo.setObjectName("logo")
        self.logo.setFixedWidth(172)
        sl.addWidget(self.logo)
        self.all_btn = QPushButton("▤  0")
        self.all_btn.setObjectName("sideItem")
        self.all_btn.setToolTip("显示全部未归档笔记")
        self.all_btn.clicked.connect(self.clear_filters)
        sl.addWidget(self.all_btn)
        self.favorites_btn = QPushButton("★  收藏")
        self.favorites_btn.setObjectName("filterButton")
        self.favorites_btn.setToolTip("只看收藏笔记")
        self.favorites_btn.setCheckable(True)
        self.favorites_btn.toggled.connect(self.toggle_favorite_filter)
        sl.addWidget(self.favorites_btn)
        self.archive_btn = QPushButton("⌁  归档")
        self.archive_btn.setObjectName("filterButton")
        self.archive_btn.setToolTip("查看已归档笔记")
        self.archive_btn.setCheckable(True)
        self.archive_btn.toggled.connect(self.toggle_archive_filter)
        sl.addWidget(self.archive_btn)
        self.season_buttons = []
        season_labels = {
            "春日": "🌱 春",
            "盛夏": "🌊 夏",
            "秋意": "🍂 秋",
            "冬藏": "❄️ 冬",
        }
        for n in THEMES:
            b = QPushButton(season_labels[n])
            b.setObjectName("season")
            b.setCheckable(True)
            b.clicked.connect(lambda _, x=n: self.set_season(x))
            sl.addWidget(b)
            self.season_buttons.append((n, b))
        sl.addStretch()
        self.motion = QPushButton("◉  动态")
        self.motion.setObjectName("motionToggle")
        self.motion.setCheckable(True)
        self.motion.setChecked(True)
        self.motion.clicked.connect(self.toggle_motion)
        sl.addWidget(self.motion)
        self.more = QToolButton()
        self.more.setObjectName("moreButton")
        self.more.setText("•••")
        self.more.setPopupMode(QToolButton.InstantPopup)
        self.more_menu = QMenu(self.more)
        self.trash_action = self.more_menu.addAction("查看废纸篓")
        self.trash_action.setCheckable(True)
        self.trash_action.toggled.connect(self.toggle_trash_filter)
        self.more_menu.addSeparator()
        self.more_menu.addAction("导出完整备份…", self.export_data)
        self.more_menu.addAction("从备份恢复…", self.import_data)
        self.more_menu.addSeparator()
        self.more_menu.addAction("清理未使用附件", self.cleanup_unused_attachments)
        self.more.setMenu(self.more_menu)
        sl.addWidget(self.more)
        self.new = QPushButton("＋  记录今天")
        self.new.setObjectName("primary")
        self.new.clicked.connect(self.new_note)
        self.new.setFixedHeight(44)
        sl.addWidget(self.new)
        outer.addWidget(self.side)
        soft_shadow(self.side, 22)
        main = QWidget()
        main.setObjectName("main")
        ml = QVBoxLayout(main)
        ml.setContentsMargins(4, 2, 4, 2)
        ml.setSpacing(12)
        outer.addWidget(main, 1)
        head = QHBoxLayout()
        head.setSpacing(12)
        greeting_card = QWidget()
        greeting_card.setObjectName("greetingCard")
        greeting = QVBoxLayout(greeting_card)
        greeting.setContentsMargins(10, 6, 10, 7)
        greeting.setSpacing(1)
        self.day_stamp = QLabel(datetime.now().strftime("TODAY  ·  %m.%d"))
        self.day_stamp.setObjectName("dayStamp")
        greeting.addWidget(self.day_stamp)
        hour = datetime.now().hour
        hello = "早上好" if hour < 11 else "午后好" if hour < 18 else "晚上好"
        self.hello = QLabel(hello)
        self.hello.setObjectName("hello")
        greeting.addWidget(self.hello)
        sub = QLabel("让文字和此刻的风景，一起留在今天。")
        sub.setObjectName("sub")
        greeting.addWidget(sub)
        head.addWidget(greeting_card)
        self.quote = QLabel("今天的风景，值得被认真收藏。")
        self.quote.setObjectName("quote")
        self.quote.setMinimumWidth(250)
        self.quote.setAlignment(Qt.AlignCenter)
        head.addWidget(self.quote)
        head.addStretch()
        self.mood = SeasonMood()
        head.addWidget(self.mood)
        self.status = QLabel("●  已保存")
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
        self.search.setPlaceholderText("搜索标题、正文或日期…")
        self.search.returnPressed.connect(self.refresh)
        bar.addWidget(self.search, 1)
        self.date_button = QPushButton("选择日期  ▾")
        self.date_button.setObjectName("dateButton")
        self.date_button.setMinimumWidth(132)
        self.date_button.clicked.connect(self.choose_date)
        bar.addWidget(self.date_button)
        self.search_btn = QPushButton("搜索")
        self.search_btn.setObjectName("compactPrimary")
        self.search_btn.clicked.connect(self.refresh)
        bar.addWidget(self.search_btn)
        self.reset = QPushButton("重置")
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
        list_title = QLabel("最近记录")
        list_title.setObjectName("cardTitle")
        list_head.addWidget(list_title)
        list_head.addStretch()
        self.list_count = QLabel("0 篇")
        self.list_count.setObjectName("muted")
        list_head.addWidget(self.list_count)
        ll.addLayout(list_head)
        self.organizer_filter = QComboBox()
        self.organizer_filter.setObjectName("organizerFilter")
        self.organizer_filter.addItem("全部分类与标签", "")
        self.organizer_filter.currentIndexChanged.connect(lambda _: self.refresh())
        ll.addWidget(self.organizer_filter)
        self.list_stack = QStackedWidget()
        self.list_stack.setObjectName("listStack")
        self.list = QListWidget()
        self.list.setObjectName("noteList")
        self.list.setSpacing(4)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
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
        self.organize = QPushButton("🏷 分类")
        self.organize.setObjectName("quiet")
        self.organize.clicked.connect(self.organize_note)
        top.addWidget(self.organize)
        rl.addLayout(top)
        self.meta = QPushButton("选择一篇笔记，或开始新的记录")
        self.meta.setObjectName("meta")
        self.meta.setToolTip("修改这篇笔记的记录日期")
        self.meta.clicked.connect(self.choose_note_date)
        rl.addWidget(self.meta)
        tools = QHBoxLayout()
        tools.setSpacing(6)
        self.format_buttons = {}
        for text, tooltip, fn in [
            ("↶", "撤销（⌘Z）", lambda: self.editor.undo()),
            ("↷", "重做（⇧⌘Z）", lambda: self.editor.redo()),
        ]:
            button = QToolButton()
            button.setText(text)
            button.setToolTip(tooltip)
            button.clicked.connect(fn)
            tools.addWidget(button)
        for text, fn in [
            ("B", lambda: self.fmt("bold")),
            ("I", lambda: self.fmt("italic")),
            ("U", lambda: self.fmt("underline")),
            ("☑ 清单", self.checklist),
            ("▦ 表格", self.table),
            ("▧ 图片", self.image),
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
        self.restore_btn = QPushButton("恢复")
        self.restore_btn.setObjectName("quiet")
        self.restore_btn.clicked.connect(self.restore_note)
        self.restore_btn.hide()
        tools.addWidget(self.restore_btn)
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
        self.count_label = QLabel("0 字 · 1 行")
        self.count_label.setObjectName("muted")
        footer.addWidget(self.count_label)
        footer.addStretch()
        self.save = QPushButton("完成记录")
        self.save.setObjectName("primary")
        self.save.clicked.connect(self.save_note)
        self.save.setFixedWidth(116)
        footer.addWidget(self.save)
        rl.addLayout(footer)
        split.addWidget(right)
        soft_shadow(right)
        self.split = split
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
        self.editor.textChanged.connect(self.update_count)
        self.editor.currentCharFormatChanged.connect(self.sync_format_buttons)
        self.editor.imagePasted.connect(self.insert_clipboard_image)
        self.install_shortcuts()

    def install_shortcuts(self):
        self.shortcuts = []

        def add(sequence, callback):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)

        add("Meta+N", self.new_note)
        add("Meta+S", self.save_note)
        add("Meta+F", self.focus_search)
        add("Meta+Shift+F", lambda: self.favorites_btn.setChecked(not self.favorite_only))

    def focus_search(self):
        self.search.setFocus()
        self.search.selectAll()

    def toggle_motion(self, enabled):
        self.overlay.set_animation_enabled(enabled)
        self.mood.set_animation_enabled(enabled)
        self.motion.setText("◉  动态" if enabled else "○  静止")

    def toggle_favorite_filter(self, enabled):
        self.favorite_only = enabled
        self.refresh()

    def toggle_archive_filter(self, enabled):
        self.archive_only = enabled
        if enabled and self.trash_only:
            self.trash_action.setChecked(False)
        self.refresh()

    def toggle_trash_filter(self, enabled):
        self.trash_only = enabled
        if enabled and self.archive_only:
            self.archive_btn.setChecked(False)
        self.more.setText("废纸篓" if enabled else "•••")
        self.refresh()

    def notes_in_current_scope(self):
        """Return notes that belong to the active archive/trash/favorite scope."""
        notes = [
            note
            for note in self.notes
            if bool(note.get("deleted_at")) == self.trash_only
            and (self.trash_only or bool(note.get("archived", False)) == self.archive_only)
            and (not self.favorite_only or note.get("favorite", False))
        ]
        organizer = self.organizer_filter.currentData() if hasattr(self, "organizer_filter") else ""
        if organizer and organizer.startswith("folder:"):
            folder = organizer.split(":", 1)[1]
            notes = [note for note in notes if note.get("folder", "随手记") == folder]
        elif organizer and organizer.startswith("tag:"):
            tag = organizer.split(":", 1)[1]
            notes = [note for note in notes if tag in note.get("tags", [])]
        return notes

    def refresh_organizer_filter(self):
        current = self.organizer_filter.currentData()
        base = [
            note
            for note in self.notes
            if bool(note.get("deleted_at")) == self.trash_only
            and (self.trash_only or bool(note.get("archived", False)) == self.archive_only)
        ]
        folders = sorted({note.get("folder", "随手记") for note in base if note.get("folder")})
        tags = sorted({tag for note in base for tag in note.get("tags", []) if tag})
        self.organizer_filter.blockSignals(True)
        self.organizer_filter.clear()
        self.organizer_filter.addItem("全部分类与标签", "")
        for folder in folders:
            self.organizer_filter.addItem(f"分类 · {folder}", f"folder:{folder}")
        for tag in tags:
            self.organizer_filter.addItem(f"标签 · #{tag}", f"tag:{tag}")
        index = self.organizer_filter.findData(current)
        self.organizer_filter.setCurrentIndex(max(0, index))
        self.organizer_filter.blockSignals(False)

    def update_count(self):
        text = self.editor.toPlainText()
        characters = len("".join(text.split()))
        lines = max(1, text.count("\n") + 1)
        self.count_label.setText(f"{characters} 字 · {lines} 行")

    def update_meta(self, season=None):
        season = season or (self.current.get("season", self.theme) if self.current else self.theme)
        tags = "  ".join(f"#{tag}" for tag in self.draft_tags)
        parts = [f"📅  {self.draft_date}", season, self.draft_folder]
        if tags:
            parts.append(tags)
        if self.draft_archived:
            parts.append("已归档")
        self.meta.setText("  ·  ".join(parts))

    def style(self):
        bg, panel, accent, text, _ = THEMES[self.theme]
        panel_color = QColor(panel)
        selected = {"春日": "#ffead9", "盛夏": "#ffebc7", "秋意": "#f7dfd0", "冬藏": "#e2edf8"}[
            self.theme
        ]
        selected_color = QColor(selected)
        pr, pg, pb = panel_color.red(), panel_color.green(), panel_color.blue()
        xr, xg, xb = selected_color.red(), selected_color.green(), selected_color.blue()
        sidebar_glass = f"rgba({pr},{pg},{pb},214)"
        panel_glass = f"rgba({pr},{pg},{pb},226)"
        soft_glass = f"rgba({pr},{pg},{pb},166)"
        selected_glass = f"rgba({xr},{xg},{xb},224)"
        accent2 = QColor(accent).lighter(118).name()
        quiet_text = QColor(text).lighter(145).name()
        self.setStyleSheet(f"""
QMainWindow,#root{{background:{bg};}}
#main{{background:transparent;}}
QWidget{{font-family:"SF Pro Display","PingFang SC",Arial;color:{text};font-size:13px;}}
#topDock{{background:{sidebar_glass};border:0;border-radius:23px;}}
#logo{{font-size:16px;font-weight:850;letter-spacing:1.2px;}}
#greetingCard{{background:{soft_glass};border-radius:17px;}}
#dayStamp{{font-size:10px;font-weight:800;color:{accent};letter-spacing:2px;}}
#hello{{font-size:32px;font-weight:800;letter-spacing:-1px;}}
#sub{{font-size:12px;color:{quiet_text};}}
#status{{background:{selected_glass};color:{text};border-radius:14px;padding:7px 11px;font-size:11px;font-weight:700;}}
#quote{{background:{selected_glass};border-radius:16px;padding:9px 14px;color:{text};font-size:11px;font-weight:650;}}
#meta,#muted{{color:{quiet_text};}}
#meta{{background:transparent;text-align:left;padding:3px 2px;font-size:11px;}}
#section{{font-size:9px;font-weight:800;color:{quiet_text};margin:6px 2px;letter-spacing:2px;}}
QPushButton,QToolButton{{border:0;border-radius:12px;padding:8px 13px;background:{soft_glass};color:{text};font-weight:650;}}
QPushButton:hover,QToolButton:hover{{background:{selected_glass};}}
QToolButton:checked{{background:{accent};color:white;}}
#primary,#compactPrimary{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {accent},stop:1 {accent2});color:white;font-weight:800;}}
#primary:hover,#compactPrimary:hover{{background:{accent2};}}
#sideItem,#season,#filterButton{{background:rgba(255,255,255,65);padding:9px 11px;border-radius:13px;}}
#sideItem:hover,#season:hover,#filterButton:hover{{background:{selected_glass};}}
#season:checked,#filterButton:checked{{background:{accent};color:white;font-weight:800;}}
#motionToggle{{background:{soft_glass};color:{quiet_text};font-size:10px;padding:9px 11px;}}
#moreButton{{min-width:26px;padding:9px 8px;background:{soft_glass};}}
#searchCard{{background:{sidebar_glass};border:0;border-radius:20px;}}
#listCard{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {panel_glass},stop:1 {selected_glass});border:0;border-radius:26px;}}
#editorCard{{background:{panel_glass};border:0;border-radius:26px;}}
#search,#dateButton{{background:rgba(255,255,255,150);border:0;border-radius:12px;padding:9px 12px;selection-background-color:{accent};}}
#dateButton{{text-align:left;}}
#dateButton[activeDate="true"]{{background:{selected_glass};color:{accent};font-weight:800;}}
#search{{min-height:20px;}}
#organizerFilter{{background:rgba(255,255,255,105);border:0;border-radius:12px;padding:8px 11px;font-weight:650;}}
#organizerFilter::drop-down{{border:0;width:24px;}}
#quiet{{background:rgba(255,255,255,85);color:{accent};}}
#danger{{background:transparent;color:#bd5b58;}}
#cardTitle{{font-size:16px;font-weight:800;}}
#title{{font-size:27px;font-weight:800;border:0;background:transparent;padding:4px 2px;selection-background-color:{selected};}}
#noteList,#listStack{{background:transparent;border:0;outline:0;}}
#noteList::item{{padding:0;border:0;}}
#noteItem{{background:rgba(255,255,255,70);border-radius:15px;}}
#noteItem:hover{{background:rgba(255,255,255,145);}}
#noteItem[selected="true"]{{background:rgba(255,255,255,205);}}
#noteItemTitle{{font-size:14px;font-weight:750;}}
#notePreview{{font-size:12px;color:{quiet_text};}}
#noteItemMeta{{font-size:10px;color:{accent};font-weight:700;}}
#noteFavorite{{color:{accent};font-size:13px;}}
#emptyIcon{{font-size:30px;color:{accent};}}
#emptyTitle{{font-size:15px;font-weight:800;}}
#emptyHint{{font-size:12px;color:{quiet_text};}}
#editor{{background:rgba(255,255,255,112);border:0;border-radius:18px;padding:18px;font-size:15px;selection-background-color:{selected};}}
QSplitter::handle{{background:transparent;}}
QDialog#sheetDialog{{background:{panel};}}
QDialog QLineEdit{{background:{selected};border:0;border-radius:11px;padding:9px 11px;selection-background-color:{accent};}}
#dialogTitle{{font-size:21px;font-weight:800;}}
#dialogSub{{font-size:12px;color:{quiet_text};}}
#dialogCard{{background:{selected};border-radius:16px;}}
#selectedDate{{font-size:17px;font-weight:800;color:{accent};padding:8px;}}
QSpinBox{{background:{panel};border:0;border-radius:11px;padding:8px 10px;min-width:74px;}}
QCheckBox{{spacing:8px;}}
QCalendarWidget QWidget{{background:{panel};}}
QCalendarWidget QToolButton{{color:{text};padding:7px;}}
QCalendarWidget QAbstractItemView:enabled{{selection-background-color:{accent};selection-color:white;alternate-background-color:{panel};outline:0;}}
QCalendarWidget QTableView{{border:0;}}
#calendarNotes{{background:rgba(255,255,255,135);border:0;border-radius:11px;padding:5px;outline:0;}}
QMenu{{background:{panel};border:0;border-radius:10px;padding:7px;}}
QMenu::item{{padding:8px 24px 8px 12px;border-radius:7px;}}
QMenu::item:selected{{background:{selected};}}
   """)

    def apply_theme(self):
        self.style()
        self.overlay.set_season(self.theme)
        self.mood.set_season(self.theme)
        copy = {
            "春日": "樱花创作间\n让新想法和雨声一起发芽。",
            "盛夏": "海边冲浪屋\n把阳光、海风和心事都写下。",
            "秋意": "秋日艺术校园\n唱片转动，灵感也正好降落。",
            "冬藏": "城市放映夜\n窗外落雪，房间里仍有热爱。",
        }
        self.quote.setText(copy[self.theme])
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
        dialog.setFixedWidth(720)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(22, 22, 22, 18)
        layout.setSpacing(13)
        title = QLabel("笔记月历")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        hint = QLabel("带数字的日期已有记录；右侧会展示当天的笔记。")
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
        body = QHBoxLayout()
        body.setSpacing(12)
        calendar_notes = self.notes_in_current_scope()
        calendar = NoteCalendar(calendar_notes, THEMES[self.theme][2])
        calendar.setObjectName("dateCalendar")
        calendar.setGridVisible(False)
        calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calendar.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)
        calendar.setMinimumHeight(285)
        if self.selected_date:
            calendar.setSelectedDate(QDate.fromString(self.selected_date, "yyyy-MM-dd"))
        body.addWidget(calendar, 1)

        day_panel = QWidget()
        day_panel.setObjectName("dialogCard")
        day_panel.setMinimumWidth(230)
        day_layout = QVBoxLayout(day_panel)
        day_layout.setContentsMargins(12, 12, 12, 12)
        selected = QLabel()
        selected.setObjectName("selectedDate")
        selected.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        day_layout.addWidget(selected)
        day_list = QListWidget()
        day_list.setObjectName("calendarNotes")
        day_layout.addWidget(day_list, 1)
        body.addWidget(day_panel)
        layout.addLayout(body)

        def show_selected():
            day = calendar.selectedDate().toString("yyyy-MM-dd")
            selected.setText(calendar.selectedDate().toString("MM 月 dd 日"))
            day_list.clear()
            matching = [note for note in calendar_notes if note.get("date") == day]
            for note in matching:
                marker = "★ " if note.get("favorite") else ""
                day_list.addItem(marker + (note.get("title") or "无标题笔记"))
            if not matching:
                day_list.addItem("这一天还没有记录")

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
        day_list.itemDoubleClicked.connect(lambda _: apply_selected())
        clear.clicked.connect(clear_selected)
        cancel.clicked.connect(dialog.reject)
        dialog.exec()

    def choose_note_date(self):
        dialog = QDialog(self)
        dialog.setObjectName("sheetDialog")
        dialog.setWindowTitle("修改笔记日期")
        dialog.setModal(True)
        dialog.setFixedWidth(420)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(22, 22, 22, 18)
        layout.setSpacing(12)

        title = QLabel("这篇笔记属于哪一天？")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        hint = QLabel("适合补记旅行、日记或过去某一天的灵感。")
        hint.setObjectName("dialogSub")
        layout.addWidget(hint)

        calendar = QCalendarWidget()
        calendar.setGridVisible(False)
        calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calendar.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)
        initial = QDate.fromString(self.draft_date, "yyyy-MM-dd")
        calendar.setSelectedDate(initial if initial.isValid() else QDate.currentDate())
        layout.addWidget(calendar)

        actions = QHBoxLayout()
        today = QPushButton("今天")
        cancel = QPushButton("取消")
        apply_button = QPushButton("使用这个日期")
        apply_button.setObjectName("compactPrimary")
        actions.addWidget(today)
        actions.addStretch()
        actions.addWidget(cancel)
        actions.addWidget(apply_button)
        layout.addLayout(actions)

        today.clicked.connect(lambda: calendar.setSelectedDate(QDate.currentDate()))
        cancel.clicked.connect(dialog.reject)
        apply_button.clicked.connect(dialog.accept)
        calendar.activated.connect(lambda _: dialog.accept())
        if dialog.exec() != QDialog.Accepted:
            return

        self.draft_date = calendar.selectedDate().toString("yyyy-MM-dd")
        self.update_meta()
        if self.current:
            self.current["date"] = self.draft_date
            self.persist()
            self.refresh(self.current["id"])
        self.status.setText("●  日期已更新")

    def organize_note(self):
        dialog = QDialog(self)
        dialog.setObjectName("sheetDialog")
        dialog.setWindowTitle("分类与标签")
        dialog.setModal(True)
        dialog.setFixedWidth(430)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(22, 22, 22, 18)
        layout.setSpacing(12)
        title = QLabel("整理这篇笔记")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        hint = QLabel("分类适合长期整理，标签适合跨分类搜索。")
        hint.setObjectName("dialogSub")
        layout.addWidget(hint)

        folder_label = QLabel("分类")
        folder_label.setObjectName("section")
        layout.addWidget(folder_label)
        folder = QLineEdit(self.draft_folder)
        folder.setPlaceholderText("例如：随手记、旅行、工作")
        layout.addWidget(folder)

        tags_label = QLabel("标签")
        tags_label.setObjectName("section")
        layout.addWidget(tags_label)
        tags = QLineEdit("，".join(self.draft_tags))
        tags.setPlaceholderText("用逗号分隔，例如：灵感，咖啡，周末")
        layout.addWidget(tags)
        archived = QCheckBox("归档这篇笔记")
        archived.setChecked(self.draft_archived)
        layout.addWidget(archived)

        actions = QHBoxLayout()
        cancel = QPushButton("取消")
        save = QPushButton("保存分类")
        save.setObjectName("compactPrimary")
        actions.addStretch()
        actions.addWidget(cancel)
        actions.addWidget(save)
        layout.addLayout(actions)
        cancel.clicked.connect(dialog.reject)
        save.clicked.connect(dialog.accept)
        if dialog.exec() != QDialog.Accepted:
            return

        self.draft_folder = folder.text().strip() or "随手记"
        normalized = tags.text().replace("，", ",")
        self.draft_tags = list(dict.fromkeys(tag.strip().lstrip("#") for tag in normalized.split(",") if tag.strip()))[:10]
        self.draft_archived = archived.isChecked()
        self.update_meta()
        if self.current:
            self.current.update(
                folder=self.draft_folder,
                tags=self.draft_tags,
                archived=self.draft_archived,
            )
            self.persist()
            self.refresh(self.current["id"])
        self.status.setText("●  分类已更新")

    def export_data(self):
        default_name = os.path.expanduser(
            f"~/Desktop/季节笔记备份-{date.today().isoformat()}.snotes"
        )
        path, _ = QFileDialog.getSaveFileName(
            self, "导出完整备份", default_name, "季节笔记备份 (*.snotes)"
        )
        if not path:
            return
        if not path.endswith(".snotes"):
            path += ".snotes"
        try:
            export_archive(path, self.notes)
        except OSError as error:
            QMessageBox.warning(self, "导出失败", str(error))
            return
        QMessageBox.information(self, "导出完成", "笔记和图片已经保存为一个完整备份。")

    def import_data(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "从备份恢复", str(BACKUP_DIR), "季节笔记备份 (*.snotes)"
        )
        if not path:
            return
        answer = QMessageBox.question(
            self,
            "恢复备份",
            "恢复后将以备份内容替换当前笔记。当前数据会先自动备份，是否继续？",
        )
        if answer != QMessageBox.Yes:
            return
        try:
            create_daily_backup(self.notes, force=True)
            self.notes = import_archive(path)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "恢复失败", str(error))
            return
        self.current = None
        self.clear_filters()
        self.status.setText("●  备份已恢复")

    def cleanup_unused_attachments(self):
        removed = cleanup_attachments(self.notes)
        QMessageBox.information(
            self,
            "附件整理完成",
            f"已清理 {len(removed)} 个未使用的图片文件。",
        )

    def update_date_button(self):
        self.date_button.setText(
            ("日期  " + self.selected_date if self.selected_date else "选择日期") + "  ▾"
        )
        self.date_button.setProperty("activeDate", bool(self.selected_date))
        self.date_button.style().unpolish(self.date_button)
        self.date_button.style().polish(self.date_button)

    def reset_filter_state(self):
        self.search.clear()
        self.selected_date = ""
        self.favorite_only = False
        self.archive_only = False
        self.trash_only = False
        for control in (self.favorites_btn, self.archive_btn, self.trash_action):
            control.blockSignals(True)
            control.setChecked(False)
            control.blockSignals(False)
        self.more.setText("•••")
        self.organizer_filter.blockSignals(True)
        self.organizer_filter.setCurrentIndex(0)
        self.organizer_filter.blockSignals(False)
        self.update_date_button()

    def clear_filters(self):
        self.reset_filter_state()
        self.refresh()

    def refresh(self, select_id=None, select_first=True):
        self.refresh_organizer_filter()
        q = self.search.text().strip().lower()
        ds = self.selected_date
        scoped_notes = self.notes_in_current_scope()
        items = [
            n
            for n in scoped_notes
            if (
                not q
                or q
                in (
                    n.get("title", "")
                    + n.get("body", "")
                    + n.get("date", "")
                    + n.get("folder", "")
                    + " ".join(n.get("tags", []))
                ).lower()
            )
            and (not ds or n.get("date", "") == ds)
        ]
        items.sort(
            key=lambda note: (note.get("date", ""), note.get("updated_at", "")),
            reverse=True,
        )
        self.list.blockSignals(True)
        self.list.clear()
        for n in items:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 82))
            item.setData(Qt.UserRole, n.get("id"))
            self.list.addItem(item)
            self.list.setItemWidget(item, NoteListItem(n))
        self.list.blockSignals(False)
        self.visible = items
        active_count = sum(
            not note.get("deleted_at") and not note.get("archived", False) for note in self.notes
        )
        self.all_btn.setText(f"▤  {active_count}")
        archived_count = sum(
            bool(note.get("archived", False)) and not note.get("deleted_at") for note in self.notes
        )
        trash_count = sum(bool(note.get("deleted_at")) for note in self.notes)
        self.archive_btn.setText(f"⌁  归档 {archived_count}" if archived_count else "⌁  归档")
        self.trash_action.setText(f"查看废纸篓（{trash_count}）" if trash_count else "查看废纸篓")
        self.list_count.setText(f"{len(items)} 篇")
        self.list_stack.setCurrentWidget(self.list if items else self.list_empty)
        if not items:
            filtering = bool(
                q
                or ds
                or self.favorite_only
                or self.archive_only
                or self.trash_only
                or self.organizer_filter.currentData()
            )
            if self.trash_only and not q and not ds and not self.organizer_filter.currentData():
                self.empty_title.setText("废纸篓是空的")
            else:
                self.empty_title.setText("没有找到匹配的笔记" if filtering else "今天还没有笔记")
            self.empty_hint.setText(
                "移到废纸篓的笔记会保留在这里，可随时恢复。"
                if self.trash_only and not q and not ds
                else "调整搜索、日期、分类或收藏条件再试试。"
                if filtering
                else "写下第一句话，季节就有了形状。"
            )
        if items and select_first:
            wanted = select_id or (self.current.get("id") if self.current else None)
            row = next((i for i, n in enumerate(items) if n.get("id") == wanted), 0)
            self.list.setCurrentRow(row)

    def pick(self, row):
        if row < 0 or row >= len(getattr(self, "visible", [])):
            return
        target_id = self.visible[row].get("id")
        if self.autosave_timer.isActive() and not self.loading_editor:
            self.save_note(True, refresh_list=False)
        self.autosave_timer.stop()
        self.loading_editor = True
        n = next(
            (note for note in self.notes if note.get("id") == target_id),
            self.visible[row],
        )
        self.current = n
        self.draft_date = n.get("date", date.today().isoformat())
        self.draft_folder = n.get("folder", "随手记")
        self.draft_tags = list(n.get("tags", []))
        self.draft_archived = bool(n.get("archived", False))
        for index in range(self.list.count()):
            widget = self.list.itemWidget(self.list.item(index))
            if widget:
                widget.set_selected(index == row)
        self.title.setText(n.get("title", ""))
        if n.get("body_html"):
            self.editor.setHtml(n["body_html"])
        else:
            self.editor.setPlainText(n.get("body", ""))
        self.update_meta(n.get("season", "春日"))
        self.favorite.setText("★ 已收藏" if n.get("favorite") else "☆ 收藏")
        self.restore_btn.setVisible(self.trash_only)
        self.delete_btn.setText("彻底删除" if self.trash_only else "移到废纸篓")
        self.loading_editor = False
        self.sync_format_buttons(self.editor.currentCharFormat())

    def new_note(self):
        if self.autosave_timer.isActive() and not self.loading_editor:
            self.save_note(True)
        self.autosave_timer.stop()
        self.loading_editor = True
        self.current = None
        self.reset_filter_state()
        self.list.blockSignals(True)
        self.list.clearSelection()
        self.list.setCurrentRow(-1)
        self.list.blockSignals(False)
        self.draft_date = date.today().isoformat()
        self.draft_folder = "随手记"
        self.draft_tags = []
        self.draft_archived = False
        self.title.clear()
        self.editor.clear()
        self.update_meta(self.theme)
        self.favorite.setText("☆ 收藏")
        self.restore_btn.hide()
        self.delete_btn.setText("移到废纸篓")
        self.loading_editor = False
        self.refresh(select_first=False)
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

    def save_note(self, silent=False, refresh_list=True):
        t = self.title.text().strip() or "无标题"
        b = self.editor.toPlainText()
        html = self.editor.toHtml()
        now = datetime.now().isoformat(timespec="seconds")
        n = self.current or {
            "id": str(uuid.uuid4()),
            "date": self.draft_date,
            "favorite": False,
            "created_at": now,
        }
        n.update(
            title=t,
            body=b,
            body_html=html,
            season=self.theme,
            date=self.draft_date,
            folder=self.draft_folder,
            tags=self.draft_tags,
            archived=self.draft_archived,
            updated_at=now,
        )
        if not self.current:
            self.notes.insert(0, n)
        self.current = n
        self.persist()
        cleanup_attachments(self.notes)
        self.status.setText("●  已自动保存" if silent else "●  内容已保存")
        if refresh_list:
            self.refresh(n["id"])

    def delete_note(self):
        if not self.current:
            return
        if self.trash_only:
            answer = QMessageBox.question(
                self,
                "彻底删除笔记",
                "彻底删除后无法恢复，确定继续吗？",
            )
            if answer != QMessageBox.Yes:
                return
            self.notes = [n for n in self.notes if n["id"] != self.current["id"]]
            cleanup_attachments(self.notes)
        else:
            answer = QMessageBox.question(
                self,
                "移到废纸篓",
                "这篇笔记会保留在废纸篓中，可随时恢复。",
            )
            if answer != QMessageBox.Yes:
                return
            self.current["deleted_at"] = datetime.now().isoformat(timespec="seconds")
        self.autosave_timer.stop()
        self.current = None
        self.persist()
        self.new_note()

    def restore_note(self):
        if not self.current or not self.current.get("deleted_at"):
            return
        restored_id = self.current.get("id")
        restored_archived = bool(self.current.get("archived", False))
        self.current.pop("deleted_at", None)
        self.current["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self.persist()
        self.current = None
        self.search.clear()
        self.selected_date = ""
        self.favorite_only = False
        self.archive_only = restored_archived
        self.trash_only = False
        for control, checked in (
            (self.favorites_btn, False),
            (self.archive_btn, restored_archived),
            (self.trash_action, False),
        ):
            control.blockSignals(True)
            control.setChecked(checked)
            control.blockSignals(False)
        self.organizer_filter.blockSignals(True)
        self.organizer_filter.setCurrentIndex(0)
        self.organizer_filter.blockSignals(False)
        self.update_date_button()
        self.more.setText("•••")
        self.refresh(restored_id)
        self.status.setText("●  笔记已恢复")

    def toggle_favorite(self):
        if not self.current:
            self.save_note()
        if self.current:
            self.current["favorite"] = not self.current.get("favorite", False)
            self.favorite.setText("★ 已收藏" if self.current["favorite"] else "☆ 收藏")
            self.persist()
            self.refresh(self.current["id"])

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
            self.insert_stored_image(stored)

    def insert_clipboard_image(self, image: QImage):
        os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
        stored = os.path.join(ATTACHMENTS_DIR, str(uuid.uuid4()) + ".png")
        if not image.save(stored, "PNG"):
            QMessageBox.warning(self, "图片粘贴失败", "无法保存剪贴板中的图片。")
            return
        self.insert_stored_image(stored)

    def insert_stored_image(self, stored):
        fmt = QTextImageFormat()
        fmt.setName(str(stored))
        fmt.setWidth(min(560, max(260, self.editor.viewport().width() - 46)))
        self.editor.textCursor().insertImage(fmt)
        self.editor.setFocus()
        self.status.setText("●  图片已插入")

    def closeEvent(self, event):
        self.autosave_timer.stop()
        if not self.loading_editor and (
            self.current or self.title.text().strip() or self.editor.toPlainText().strip()
        ):
            self.save_note(True, refresh_list=False)
        save_settings(
            {
                "theme": self.theme,
                "motion": self.motion.isChecked(),
                "window_size": [self.width(), self.height()],
                "split_sizes": self.split.sizes(),
            }
        )
        event.accept()

    def changeEvent(self, event):
        super().changeEvent(event)
        if hasattr(self, "overlay") and event.type() == QEvent.ActivationChange:
            active = self.isActiveWindow() and self.motion.isChecked()
            self.overlay.set_animation_enabled(active)
            self.mood.set_animation_enabled(active)
