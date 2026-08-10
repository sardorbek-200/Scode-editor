from PyQt6.QtWidgets import QWidget, QPlainTextEdit
from PyQt6.QtGui import QColor, QPainter, QTextFormat
from PyQt6.QtCore import Qt, QRect, QSize


class LineNumberArea(QWidget):
    """Qator raqamlarini chizish uchun yordamchi vidjet."""

    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    """
    Qator raqamlari (Line Numbers) va joriy qator ajratib ko'rsatish funksiyasiga ega
    kod redaktori vidjeti.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self):
        digits = 1
        max_blocks = max(1, self.blockCount())
        while max_blocks >= 10:
            max_blocks //= 10
            digits += 1

        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _=0):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QPlainTextEdit.ExtraSelection()
            line_color = QColor("#282828")  # Dark theme da joriy qator foni
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        # Qator raqamlari joylashgan joy foni: #1e1e1e
        painter.fillRect(event.rect(), QColor("#1e1e1e"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        current_line_number = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                if block_number == current_line_number:
                    painter.setPen(QColor("#ffffff"))  # Faol qator raqami oq rangda
                else:
                    painter.setPen(QColor("#858585"))  # Qolgan qator raqamlari: #858585

                painter.setFont(self.font())
                painter.drawText(
                    0, top, self.line_number_area.width() - 8, self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number
                )

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
