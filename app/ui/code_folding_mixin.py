import re
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QColor, QPainter, QPolygon, QFont, QTextCursor
from PyQt6.QtWidgets import QWidget, QPlainTextEdit, QTextEdit


class CodeFoldingMixin:
    """
    Scode Editor uchun Universal Code Folding (kod bloklarini yig'ish/ochish) Mixin klassi.
    
    Qo'llab-quvvatlanadigan redaktorlar:
    1. QsciScintilla (Nativ QScintilla fold margin API)
    2. QTextEdit / QPlainTextEdit (Custom block visibility & margin indicators)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.folded_lines = set()  # QPlainTextEdit/QTextEdit yig'ilgan qatorlar indekslari
        self._init_code_folding()

    def _is_scintilla(self) -> bool:
        """QsciScintilla ekanligini aniqlash"""
        return hasattr(self, 'getCursorPosition') and hasattr(self, 'setFolding')

    def _init_code_folding(self):
        """Folding funksiyasini boshlang'ich sozlash"""
        if self._is_scintilla():
            self._setup_scintilla_folding()
        else:
            self._setup_qtextedit_folding()

    def _setup_scintilla_folding(self):
        """QsciScintilla uchun nativ folding marginni sozlash"""
        try:
            from PyQt6.Qsci import QsciScintilla
            # PlainFoldStyle orqali zamonaviy, nozik fold paneli
            self.setFolding(QsciScintilla.FoldStyle.PlainFoldStyle)
            self.setMarginType(2, QsciScintilla.MarginType.SymbolMargin)
            self.setMarginWidth(2, 14)
            self.setMarginSensitivity(2, True)

            dark_bg = QColor("#1e1e1e")
            if hasattr(self, '_set_margin_color'):
                self._set_margin_color(2, dark_bg, QColor("#656e7b"))
            else:
                try:
                    self.setMarginBackgroundColor(2, dark_bg)
                    self.setMarginForegroundColor(2, QColor("#656e7b"))
                except Exception:
                    pass
            self.setFoldMarginColors(dark_bg, dark_bg)

            # Scintilla ichki fold marker ranglarini biriktirish
            self.SendScintilla(QsciScintilla.SCI_SETFOLDMARGINCOLOUR, True, dark_bg.rgb())
            self.SendScintilla(QsciScintilla.SCI_SETFOLDMARGINBACKCOLOUR, True, dark_bg.rgb())
        except Exception:
            pass

    def _setup_qtextedit_folding(self):
        """QTextEdit / QPlainTextEdit uchun margin hodisalarini ulash"""
        if hasattr(self, 'line_number_area') and self.line_number_area:
            original_mouse_press = self.line_number_area.mousePressEvent
            
            def margin_mouse_press(event):
                # Sichqonchaning chap tugmasi bosilganda folding simvoliga tegishini tekshirish
                if event.button() == Qt.MouseButton.LeftButton:
                    y = event.pos().y()
                    block = self.firstVisibleBlock() if hasattr(self, 'firstVisibleBlock') else None
                    if block:
                        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
                        bottom = top + round(self.blockBoundingRect(block).height())
                        
                        while block.isValid():
                            if top <= y <= bottom:
                                line_num = block.blockNumber()
                                fold_end = self.get_fold_end_line(line_num)
                                if fold_end > line_num:
                                    self.toggle_fold(line_num)
                                    return
                                break
                            block = block.next()
                            top = bottom
                            bottom = top + round(self.blockBoundingRect(block).height())
                
                if original_mouse_press:
                    original_mouse_press(event)

            self.line_number_area.mousePressEvent = margin_mouse_press

    def toggle_fold(self, line_num: int = -1):
        """
        Berilgan qatordagi yoki joriy kursor turgan qatordagi kod blokini yig'ish/ochish.
        """
        if self._is_scintilla():
            if line_num < 0:
                line_num, _ = self.getCursorPosition()
            self.toggleFold(line_num)
        else:
            if line_num < 0:
                line_num = self.textCursor().blockNumber()

            fold_end = self.get_fold_end_line(line_num)
            if fold_end > line_num:
                is_folded = line_num in self.folded_lines
                self._set_block_range_visible(line_num, fold_end, visible=is_folded)
                if is_folded:
                    self.folded_lines.remove(line_num)
                else:
                    self.folded_lines.add(line_num)
                
                self.viewport().update()
                if hasattr(self, 'update_line_number_area'):
                    self.update_line_number_area(self.viewport().rect(), 0)

    def fold_all(self):
        """Barcha yig'ilishi mumkin bo'lgan bloklarni yig'ib qo'yish (Collapse All)"""
        if self._is_scintilla():
            self.foldAll(True)
        else:
            doc = self.document()
            for b_num in range(doc.blockCount()):
                fold_end = self.get_fold_end_line(b_num)
                if fold_end > b_num and b_num not in self.folded_lines:
                    self._set_block_range_visible(b_num, fold_end, visible=False)
                    self.folded_lines.add(b_num)
            self.viewport().update()
            if hasattr(self, 'update_line_number_area'):
                self.update_line_number_area(self.viewport().rect(), 0)

    def unfold_all(self):
        """Barcha yig'ilgan kod bloklarini qayta ochish (Expand All)"""
        if self._is_scintilla():
            self.foldAll(False)
        else:
            doc = self.document()
            for b_num in range(doc.blockCount()):
                block = doc.findBlockByNumber(b_num)
                if not block.isVisible():
                    block.setVisible(True)
            self.folded_lines.clear()
            self.viewport().update()
            if hasattr(self, 'update_line_number_area'):
                self.update_line_number_area(self.viewport().rect(), 0)

    def get_fold_end_line(self, start_line: int) -> int:
        """
        Berilgan qator uchun blok tugash qatorini hisoblash (Python, JS, CSS, HTML).
        """
        if self._is_scintilla():
            return -1

        doc = self.document()
        total_blocks = doc.blockCount()
        if start_line >= total_blocks - 1:
            return start_line

        start_block = doc.findBlockByNumber(start_line)
        start_text = start_block.text()
        lang = getattr(self, 'language', 'python').lower()

        # 1. Python Syntax Folding (Indentation va ':' bo'yicha)
        if 'python' in lang:
            stripped = start_text.strip()
            if stripped.endswith(':') or re.match(r'^(def|class|if|elif|else|for|while|try|except|finally|with)\b', stripped):
                start_indent = len(start_text) - len(start_text.lstrip())
                end_line = start_line

                for i in range(start_line + 1, total_blocks):
                    block = doc.findBlockByNumber(i)
                    text = block.text()
                    if not text.strip():
                        continue  # Bo'sh qatorlarni o'tkazib yuborish
                    
                    indent = len(text) - len(text.lstrip())
                    if indent > start_indent:
                        end_line = i
                    else:
                        break
                return end_line

        # 2. JavaScript / CSS Syntax Folding ({ ... } bo'yicha)
        elif any(l in lang for l in ('javascript', 'js', 'css')):
            if '{' in start_text and start_text.count('{') > start_text.count('}'):
                brace_count = 0
                for i in range(start_line, total_blocks):
                    text = doc.findBlockByNumber(i).text()
                    brace_count += text.count('{') - text.count('}')
                    if brace_count <= 0:
                        return i
                return total_blocks - 1

        # 3. HTML Syntax Folding (<tag> ... </tag> bo'yicha)
        elif 'html' in lang or 'xml' in lang:
            tag_match = re.search(r'<([a-zA-Z0-9]+)(?:\s+[^/>]*)?>', start_text)
            if tag_match:
                tag_name = tag_match.group(1).lower()
                void_tags = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
                if tag_name not in void_tags and f'</{tag_name}>' not in start_text:
                    depth = 0
                    for i in range(start_line, total_blocks):
                        text = doc.findBlockByNumber(i).text()
                        if f'<{tag_name}' in text:
                            depth += text.count(f'<{tag_name}')
                        if f'</{tag_name}>' in text:
                            depth -= text.count(f'</{tag_name}>')
                        if depth <= 0:
                            return i
                    return total_blocks - 1

        return start_line

    def _set_block_range_visible(self, start_line: int, end_line: int, visible: bool):
        """Qatorlar oralig'ini yashirish yoki ko'rsatish"""
        doc = self.document()
        for i in range(start_line + 1, end_line + 1):
            block = doc.findBlockByNumber(i)
            if block.isValid():
                block.setVisible(visible)

    def draw_folding_indicators(self, painter: QPainter, block, top: int, height: int):
        """
        QTextEdit / QPlainTextEdit margin qismida yig'ish strelkalarini (- / + yoki ▼ / ►) chizish.
        """
        line_num = block.blockNumber()
        fold_end = self.get_fold_end_line(line_num)

        if fold_end > line_num:
            is_folded = line_num in self.folded_lines
            painter.setPen(QColor("#858585"))
            painter.setFont(QFont("Consolas", 9))

            # Strelka indikatorini chizish (▼ ochiq, ► yig'ilgan)
            indicator = "►" if is_folded else "▼"
            margin_x = 4  # Margindagi ikonkalar o'rni
            painter.drawText(margin_x, top, 12, height, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, indicator)


# --- NAMOUNAVIY ISHLATILISHI ---
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from app.ui.smart_editor_mixin import SmartEditorMixin, ScodeTextEdit

    class FoldingEditor(CodeFoldingMixin, ScodeTextEdit):
        def __init__(self, parent=None, language="python"):
            super().__init__(parent=parent, language=language)

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Scode Editor - Code Folding Test")
    window.resize(800, 600)

    editor = FoldingEditor(language="python")
    editor.setPlainText(
        "class Test:\n"
        "    def demo():\n"
        "        if True:\n"
        "            print('Hello World')\n"
        "        print('Done')\n"
    )
    window.setCentralWidget(editor)
    window.show()
    sys.exit(app.exec())
