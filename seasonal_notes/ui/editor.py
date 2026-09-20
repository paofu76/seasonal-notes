from PySide6.QtCore import Signal
from PySide6.QtGui import QImage, QTextCursor
from PySide6.QtWidgets import QMenu, QTextEdit


class NoteEditor(QTextEdit):
    """支持点击勾选的富文本编辑器。"""

    imagePasted = Signal(QImage)

    def insertFromMimeData(self, source):
        if source.hasImage():
            image = QImage(source.imageData())
            if not image.isNull():
                self.imagePasted.emit(image)
                return
        super().insertFromMimeData(source)

    def contextMenuEvent(self, event):
        cursor = self.cursorForPosition(event.position().toPoint())
        menu = self.createStandardContextMenu()
        table = cursor.currentTable()
        if table is not None:
            self._add_table_actions(menu, cursor, table)

        image_cursor = self._image_cursor(cursor)
        if image_cursor is not None:
            self._add_image_actions(menu, image_cursor)
        menu.exec(event.globalPos())
        menu.deleteLater()

    def _add_table_actions(self, menu, cursor, table):
        menu.addSeparator()
        table_menu = QMenu("表格", menu)
        menu.addMenu(table_menu)
        cell = table.cellAt(cursor)
        row, column = cell.row(), cell.column()
        table_menu.addAction("在上方添加一行", lambda: table.insertRows(row, 1))
        table_menu.addAction("在下方添加一行", lambda: table.insertRows(row + cell.rowSpan(), 1))
        table_menu.addAction("在左侧添加一列", lambda: table.insertColumns(column, 1))
        table_menu.addAction(
            "在右侧添加一列", lambda: table.insertColumns(column + cell.columnSpan(), 1)
        )
        table_menu.addSeparator()
        remove_row = table_menu.addAction("删除当前行", lambda: table.removeRows(row, 1))
        remove_row.setEnabled(table.rows() > 1)
        remove_column = table_menu.addAction("删除当前列", lambda: table.removeColumns(column, 1))
        remove_column.setEnabled(table.columns() > 1)

        first_row, row_count, first_column, column_count = cursor.selectedTableCells()
        merge = table_menu.addAction(
            "合并所选单元格",
            lambda: table.mergeCells(first_row, first_column, row_count, column_count),
        )
        merge.setEnabled(first_row >= 0 and (row_count > 1 or column_count > 1))
        split = table_menu.addAction(
            "拆分当前单元格",
            lambda: table.splitCell(row, column, cell.rowSpan(), cell.columnSpan()),
        )
        split.setEnabled(cell.rowSpan() > 1 or cell.columnSpan() > 1)

    def _image_cursor(self, cursor):
        for move_back in (False, True):
            candidate = QTextCursor(cursor)
            if move_back and not candidate.movePosition(QTextCursor.PreviousCharacter):
                continue
            candidate.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
            if candidate.charFormat().isImageFormat():
                return candidate
        return None

    def _add_image_actions(self, menu, cursor):
        menu.addSeparator()
        image_menu = QMenu("图片", menu)
        menu.addMenu(image_menu)
        for label, ratio in (("小尺寸 50%", .50), ("中尺寸 75%", .75), ("适应编辑区", 1.0)):
            image_menu.addAction(label, lambda _, value=ratio: self._resize_image(cursor, value))
        image_menu.addSeparator()
        image_menu.addAction("删除图片", cursor.removeSelectedText)

    def _resize_image(self, cursor, ratio):
        image_format = cursor.charFormat().toImageFormat()
        target_width = max(180, int((self.viewport().width() - 48) * ratio))
        image_format.setWidth(target_width)
        cursor.setCharFormat(image_format)
        self.setTextCursor(cursor)

    def mousePressEvent(self, event):
        cursor = self.cursorForPosition(event.position().toPoint())
        text = cursor.block().text()
        if event.position().x() < 62 and (text.startswith("☐") or text.startswith("☑")):
            cursor.setPosition(cursor.block().position())
            cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
            cursor.insertText("☑" if text.startswith("☐") else "☐")
            self.setTextCursor(cursor)
            return
        super().mousePressEvent(event)
