import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QCheckBox,
    QDialog,
    QLineEdit,
    QMenu,
    QPushButton,
)

from seasonal_notes import storage
from seasonal_notes.ui.main_window import App


class UiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.storage_patch = patch.multiple(
            storage,
            APP_DATA_DIR=root,
            ATTACHMENTS_DIR=root / "attachments",
            DATA=root / "notes.json",
            SETTINGS=root / "settings.json",
            BACKUP_DIR=root / "backups",
            LEGACY_DATA=root / "missing-legacy.json",
        )
        self.storage_patch.start()
        self.window = App()

    def tearDown(self):
        self.window.loading_editor = True
        self.window.close()
        self.window.deleteLater()
        self.storage_patch.stop()
        self.temporary.cleanup()

    def test_note_edit_save_and_filters(self):
        self.window.new_note()
        self.window.title.setText("今天的灵感")
        self.window.editor.setPlainText("海风和唱片")
        self.window.save_note()

        self.assertEqual(len(self.window.notes), 1)
        self.assertEqual(storage.load_notes()[0]["title"], "今天的灵感")

        self.window.search.setText("唱片")
        self.window.refresh()
        self.assertEqual(len(self.window.visible), 1)
        self.window.search.setText("不存在的内容")
        self.window.refresh()
        self.assertEqual(len(self.window.visible), 0)

        self.window.search.clear()
        self.window.selected_date = "2000-01-01"
        self.window.refresh()
        self.assertEqual(len(self.window.visible), 0)
        self.window.selected_date = self.window.notes[0]["date"]
        self.window.refresh()
        self.assertEqual(len(self.window.visible), 1)

        self.window.toggle_favorite()
        self.window.favorites_btn.setChecked(True)
        self.assertEqual(len(self.window.visible), 1)
        self.assertTrue(self.window.visible[0]["favorite"])

        def organize_note():
            for dialog in QApplication.topLevelWidgets():
                if isinstance(dialog, QDialog) and dialog.windowTitle() == "分类与标签":
                    fields = dialog.findChildren(QLineEdit)
                    fields[0].setText("旅行")
                    fields[1].setText("海边，周末")
                    dialog.findChild(QCheckBox).setChecked(True)
                    for button in dialog.findChildren(QPushButton):
                        if button.text() == "保存分类":
                            button.click()
                            return

        QTimer.singleShot(20, organize_note)
        self.window.organize_note()
        self.assertEqual(self.window.current["folder"], "旅行")
        self.assertEqual(self.window.current["tags"], ["海边", "周末"])
        self.assertTrue(self.window.current["archived"])
        self.window.archive_btn.setChecked(True)
        self.assertEqual(len(self.window.visible), 1)

    def test_checklist_table_and_date_picker(self):
        self.window.editor.clear()
        self.window.checklist()
        self.assertTrue(self.window.editor.toPlainText().startswith("☐"))

        def insert_default_table():
            for dialog in QApplication.topLevelWidgets():
                if isinstance(dialog, QDialog) and dialog.windowTitle() == "插入表格":
                    for button in dialog.findChildren(QPushButton):
                        if button.text() == "插入表格":
                            button.click()
                            return

        QTimer.singleShot(20, insert_default_table)
        self.window.table()
        table = self.window.editor.textCursor().currentTable()
        self.assertIsNotNone(table)
        self.assertEqual((table.rows(), table.columns()), (4, 3))
        menu = QMenu()
        self.window.editor._add_table_actions(menu, self.window.editor.textCursor(), table)
        table_menu = menu.actions()[-1].menu()
        next(action for action in table_menu.actions() if action.text() == "在下方添加一行").trigger()
        self.assertEqual(table.rows(), 5)

        chosen = QDate(2026, 8, 18)

        def choose_day():
            for dialog in QApplication.topLevelWidgets():
                if isinstance(dialog, QDialog) and dialog.windowTitle() == "按日期查找笔记":
                    dialog.findChild(QCalendarWidget).setSelectedDate(chosen)
                    for button in dialog.findChildren(QPushButton):
                        if button.text() == "查看这一天":
                            button.click()
                            return

        QTimer.singleShot(20, choose_day)
        self.window.choose_date()
        self.assertEqual(self.window.selected_date, "2026-08-18")

        note_day = QDate(2026, 8, 9)

        def choose_note_day():
            for dialog in QApplication.topLevelWidgets():
                if isinstance(dialog, QDialog) and dialog.windowTitle() == "修改笔记日期":
                    dialog.findChild(QCalendarWidget).setSelectedDate(note_day)
                    for button in dialog.findChildren(QPushButton):
                        if button.text() == "使用这个日期":
                            button.click()
                            return

        QTimer.singleShot(20, choose_note_day)
        self.window.choose_note_date()
        self.assertEqual(self.window.draft_date, "2026-08-09")

        self.window.clear_filters()
        self.assertEqual(self.window.selected_date, "")
        self.assertEqual(self.window.search.text(), "")
        self.assertFalse(self.window.favorite_only)
        self.assertIn("字", self.window.count_label.text())


if __name__ == "__main__":
    unittest.main()
