import re
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QKeyEvent
from PyQt6.QtWidgets import QTextEdit, QApplication, QMainWindow


class SmartEditorMixin:
    """
    Scode Editor uchun PyQt6 (QTextEdit, QPlainTextEdit, QsciScintilla) asosidagi SmartEditorMixin.
    
    Xususiyatlari:
    1. Auto-Bracket Matching & Skipping (Qavslar va tirnoqlarni avto-yopish hamda ustidan sakrash)
    2. Multi-Language Auto-Indentation (Python, JS, CSS, HTML uchun moslashuvchan Enter joy tashlash)
    3. Universal Prettier (Ctrl + Shift + I orqali kodni formatlash)
    """

    PAIRS = {
        '(': ')',
        '[': ']',
        '{': '}',
        '"': '"',
        "'": "'"
    }
    CLOSING_CHARS = {')', ']', '}', '"', "'"}

    def __init__(self, *args, **kwargs):
        lang = kwargs.pop('language', None)
        tab_sz = kwargs.pop('tab_size', 4)
        super().__init__(*args, **kwargs)

        self.language = lang if lang else getattr(self, 'language', 'python')
        self.tab_size = tab_sz

    def set_language(self, lang: str):
        """Muharrir ishlayotgan dasturlash tilini o'rnatish ('python', 'javascript', 'css', 'html')"""
        self.language = str(lang).lower() if lang else 'python'

    def _is_scintilla(self) -> bool:
        """Editor QsciScintilla ekanligini aniqlash"""
        return hasattr(self, 'getCursorPosition') and hasattr(self, 'insertAt')

    def _find_editor_view(self):
        """Finds the parent EditorView instance across widget hierarchy."""
        curr = self.parent() if hasattr(self, 'parent') else None
        while curr:
            if hasattr(curr, 'show_find_dialog') or hasattr(curr, 'search_panel'):
                return curr
            curr = curr.parent() if hasattr(curr, 'parent') else None

        try:
            win = self.window()
            if win:
                if hasattr(win, 'show_find_dialog') or hasattr(win, 'search_panel'):
                    return win
                if hasattr(win, 'editor_view') and hasattr(win.editor_view, 'show_find_dialog'):
                    return win.editor_view
                from PyQt6.QtWidgets import QWidget
                from app.ui.vscode_editor_mixins import EditorCommandsMixin
                for child in win.findChildren(QWidget):
                    if isinstance(child, EditorCommandsMixin):
                        return child
        except Exception:
            pass
        return None

    def keyPressEvent(self, event: QKeyEvent):
        """
        Klaviatura tugmasi bosilganda hodisalarni ushlab qolish va ishlov berish.
        """
        navigation_keys = {
            Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down,
            Qt.Key.Key_Home, Qt.Key.Key_End, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown,
            Qt.Key.Key_Backspace, Qt.Key.Key_Delete, Qt.Key.Key_Escape
        }
        if event.key() in navigation_keys and not (event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)):
            super().keyPressEvent(event)
            return

        key = event.key()
        mods = event.modifiers()
        ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)
        shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
        alt = bool(mods & Qt.KeyboardModifier.AltModifier)

        editor_view = self._find_editor_view()

        # 1. Ctrl + / -> Line Comment
        if ctrl and not shift and not alt and key in (Qt.Key.Key_Slash, Qt.Key.Key_Question):
            if editor_view and hasattr(editor_view, 'toggle_line_comment'):
                editor_view.toggle_line_comment()
                return
            elif hasattr(self, 'toggle_line_comment'):
                self.toggle_line_comment()
                return

        # 2. Shift + Alt + A -> Block Comment
        if not ctrl and shift and alt and key == Qt.Key.Key_A:
            if editor_view and hasattr(editor_view, 'toggle_block_comment'):
                editor_view.toggle_block_comment()
                return

        # 3. Shift + Alt + Down -> Duplicate Line Down
        if not ctrl and shift and alt and key == Qt.Key.Key_Down:
            if editor_view and hasattr(editor_view, 'duplicate_line_down'):
                editor_view.duplicate_line_down()
                return

        # 4. Shift + Alt + Up -> Duplicate Line Up
        if not ctrl and shift and alt and key == Qt.Key.Key_Up:
            if editor_view and hasattr(editor_view, 'duplicate_line_up'):
                editor_view.duplicate_line_up()
                return

        # 5. Alt + Up -> Move Line Up
        if not ctrl and not shift and alt and key == Qt.Key.Key_Up:
            if editor_view and hasattr(editor_view, 'move_line_up'):
                editor_view.move_line_up()
                return

        # 6. Alt + Down -> Move Line Down
        if not ctrl and not shift and alt and key == Qt.Key.Key_Down:
            if editor_view and hasattr(editor_view, 'move_line_down'):
                editor_view.move_line_down()
                return

        # 7. Ctrl + F -> Find
        if ctrl and not shift and not alt and key == Qt.Key.Key_F:
            if editor_view and hasattr(editor_view, 'show_find_dialog'):
                editor_view.show_find_dialog()
                return

        # 8. Ctrl + H -> Replace
        if ctrl and not shift and not alt and key == Qt.Key.Key_H:
            if editor_view and hasattr(editor_view, 'show_replace_dialog'):
                editor_view.show_replace_dialog()
                return

        # 9. Ctrl + P -> Quick Open
        if ctrl and not shift and not alt and key == Qt.Key.Key_P:
            if editor_view and hasattr(editor_view, 'open_quick_open_dialog'):
                editor_view.open_quick_open_dialog()
                return

        # 10. Ctrl + Shift + P -> Command Palette
        if ctrl and shift and not alt and key == Qt.Key.Key_P:
            if editor_view and hasattr(editor_view, 'open_command_palette'):
                editor_view.open_command_palette()
                return

        # 11. Ctrl + B -> Toggle Sidebar
        if ctrl and not shift and not alt and key == Qt.Key.Key_B:
            if editor_view and hasattr(editor_view, 'toggle_sidebar'):
                editor_view.toggle_sidebar()
                return

        # 12. Ctrl + Shift + T -> External Terminal
        if ctrl and shift and not alt and key == Qt.Key.Key_T:
            if editor_view and hasattr(editor_view, 'open_external_terminal'):
                editor_view.open_external_terminal()
                return

        # 13. Ctrl + \ -> Toggle Split View
        if ctrl and not shift and not alt and key in (Qt.Key.Key_Backslash, Qt.Key.Key_Bar):
            if editor_view and hasattr(editor_view, 'toggle_split_view'):
                editor_view.toggle_split_view()
                return

        # 14. Ctrl + Shift + K -> Delete Current Line
        if ctrl and shift and not alt and key == Qt.Key.Key_K:
            if editor_view and hasattr(editor_view, 'delete_current_line'):
                editor_view.delete_current_line()
                return

        # 15. Ctrl + D -> Select Next Occurrence
        if ctrl and not shift and not alt and key == Qt.Key.Key_D:
            if editor_view and hasattr(editor_view, 'select_next_occurrence'):
                editor_view.select_next_occurrence()
                return

        # 16. Ctrl + G -> Go to Line
        if ctrl and not shift and not alt and key == Qt.Key.Key_G:
            if editor_view and hasattr(editor_view, 'show_goto_line_dialog'):
                editor_view.show_goto_line_dialog()
                return

        # 17. Ctrl + W -> Close Current Tab
        if ctrl and not shift and not alt and key == Qt.Key.Key_W:
            if editor_view and hasattr(editor_view, 'close_current_tab'):
                editor_view.close_current_tab()
                return

        # 18. Ctrl + Shift + I -> Prettier (Kodni formatlash)
        if ctrl and shift and not alt and key == Qt.Key.Key_I:
            self.format_code()
            return

        # Scintilla redaktori uchun
        if self._is_scintilla():
            if self._handle_key_scintilla(event):
                return
        else:
            if self._handle_key_qtextedit(event):
                return

        super().keyPressEvent(event)

    # =========================================================================
    # QsciScintilla Engine Handler
    # =========================================================================
    def _handle_key_scintilla(self, event: QKeyEvent) -> bool:
        key = event.key()
        text = event.text()
        line, col = self.getCursorPosition()
        line_text = self.text(line)
        raw_line = line_text.rstrip('\r\n')

        next_char = raw_line[col] if col < len(raw_line) else ''
        prev_char = raw_line[col - 1] if col > 0 else ''
        has_sel = self.hasSelectedText()

        # --- Backspace bilan faqat haqiqiy juft qavslar orasida bo'lsa o'chirish ---
        if key == Qt.Key.Key_Backspace:
            if has_sel:
                return False
            if prev_char in self.PAIRS and self.PAIRS[prev_char] == next_char:
                self.setSelection(line, col - 1, line, col + 1)
                self.removeSelectedText()
                return True
            return False

        # Delete tugmasi har doim standart o'chirish mexanizmini ishlatadi
        if key == Qt.Key.Key_Delete:
            return False

        # --- 1. Auto-Bracket Matching & Skipping ---
        if text:
            # Sakrab o'tish (Skip over closing bracket/quote)
            if text in self.CLOSING_CHARS and next_char == text:
                if text in ('"', "'") and has_sel:
                    pass
                else:
                    self.setCursorPosition(line, col + 1)
                    return True

            # Juftini qo'shish (Auto-close pair)
            if text in self.PAIRS:
                closing_char = self.PAIRS[text]
                if has_sel:
                    sel = self.selectedText()
                    self.replaceSelectedText(f"{text}{sel}{closing_char}")
                else:
                    self.insert(f"{text}{closing_char}")
                    self.setCursorPosition(line, col + 1)
                return True

        # --- 2. Multi-Language Auto-Indentation (Enter) ---
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return self._handle_enter_scintilla(line, col, raw_line)

        return False

    def _handle_enter_scintilla(self, line: int, col: int, raw_line: str) -> bool:
        text_before = raw_line[:col]
        text_after = raw_line[col:]

        indent_match = re.match(r'^(\s*)', raw_line)
        base_indent = indent_match.group(1) if indent_match else ''

        indent_unit = ' ' * getattr(self, 'tab_size', 4)
        lang = getattr(self, 'language', 'python').lower()

        extra_indent = ''
        split_block = False

        if 'python' in lang:
            if text_before.rstrip().endswith(':'):
                extra_indent = indent_unit

        elif any(l in lang for l in ('javascript', 'js', 'css')):
            if text_before.rstrip().endswith('{'):
                extra_indent = indent_unit
                if text_after.lstrip().startswith('}'):
                    split_block = True

        elif 'html' in lang or 'xml' in lang:
            tag_match = re.search(r'<([a-zA-Z0-9]+)(?:\s+[^/>]*)?>$', text_before.strip())
            if tag_match:
                tag_name = tag_match.group(1).lower()
                void_tags = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
                if tag_name not in void_tags:
                    extra_indent = indent_unit
                    if text_after.lstrip().startswith(f'</{tag_name}>') or text_after.lstrip().startswith('</'):
                        split_block = True
        else:
            if text_before.rstrip().endswith('{') or text_before.rstrip().endswith(':'):
                extra_indent = indent_unit
                if text_before.rstrip().endswith('{') and text_after.lstrip().startswith('}'):
                    split_block = True

        if split_block:
            self.insert(f"\n{base_indent}{extra_indent}\n{base_indent}")
            self.setCursorPosition(line + 1, len(base_indent) + len(extra_indent))
            return True
        else:
            new_indent = base_indent + extra_indent
            self.insert(f"\n{new_indent}")
            self.setCursorPosition(line + 1, len(new_indent))
            return True

    # =========================================================================
    # QTextEdit / QPlainTextEdit Engine Handler
    # =========================================================================
    def _handle_key_qtextedit(self, event: QKeyEvent) -> bool:
        cursor = self.textCursor()
        text = event.text()
        key = event.key()

        doc = self.document()
        pos = cursor.position()
        block_text = cursor.block().text()
        col = cursor.positionInBlock()

        next_char = doc.characterAt(pos) if pos < doc.characterCount() else ''
        prev_char = doc.characterAt(pos - 1) if pos > 0 else ''

        # Backspace bilan juft qavslarni birga o'chirish
        if key == Qt.Key.Key_Backspace and not cursor.hasSelection():
            if prev_char in self.PAIRS and self.PAIRS[prev_char] == next_char:
                cursor.deleteChar()
                cursor.deletePreviousChar()
                return True

        # Auto-Bracket Matching & Skipping
        if text:
            if text in self.CLOSING_CHARS and next_char == text:
                if text in ('"', "'") and cursor.hasSelection():
                    pass
                else:
                    cursor.movePosition(QTextCursor.MoveOperation.Right)
                    self.setTextCursor(cursor)
                    return True

            if text in self.PAIRS:
                closing_char = self.PAIRS[text]
                if cursor.hasSelection():
                    selected_text = cursor.selectedText()
                    cursor.insertText(f"{text}{selected_text}{closing_char}")
                else:
                    cursor.insertText(f"{text}{closing_char}")
                    cursor.movePosition(QTextCursor.MoveOperation.Left)
                    self.setTextCursor(cursor)
                return True

        # Enter key auto-indentation
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return self._handle_enter_qtextedit(cursor, block_text, col)

        return False

    def _handle_enter_qtextedit(self, cursor: QTextCursor, line_text: str, col: int) -> bool:
        text_before = line_text[:col]
        text_after = line_text[col:]

        indent_match = re.match(r'^(\s*)', line_text)
        base_indent = indent_match.group(1) if indent_match else ''

        indent_unit = ' ' * getattr(self, 'tab_size', 4)
        lang = getattr(self, 'language', 'python').lower()

        extra_indent = ''
        split_block = False

        if 'python' in lang:
            if text_before.rstrip().endswith(':'):
                extra_indent = indent_unit

        elif any(l in lang for l in ('javascript', 'js', 'css')):
            if text_before.rstrip().endswith('{'):
                extra_indent = indent_unit
                if text_after.lstrip().startswith('}'):
                    split_block = True

        elif 'html' in lang or 'xml' in lang:
            tag_match = re.search(r'<([a-zA-Z0-9]+)(?:\s+[^/>]*)?>$', text_before.strip())
            if tag_match:
                tag_name = tag_match.group(1).lower()
                void_tags = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
                if tag_name not in void_tags:
                    extra_indent = indent_unit
                    if text_after.lstrip().startswith(f'</{tag_name}>') or text_after.lstrip().startswith('</'):
                        split_block = True
        else:
            if text_before.rstrip().endswith('{') or text_before.rstrip().endswith(':'):
                extra_indent = indent_unit
                if text_before.rstrip().endswith('{') and text_after.lstrip().startswith('}'):
                    split_block = True

        if split_block:
            cursor.insertText(f"\n{base_indent}{extra_indent}\n{base_indent}")
            cursor.movePosition(QTextCursor.MoveOperation.Up)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
            self.setTextCursor(cursor)
            return True
        else:
            new_indent = base_indent + extra_indent
            cursor.insertText(f"\n{new_indent}")
            self.setTextCursor(cursor)
            return True

    # =========================================================================
    # Universal Prettier Formatter
    # =========================================================================
    def format_code(self):
        """
        Universal Prettier: Ctrl + Shift + I bosilganda kodni chiroyli formatlash.
        """
        lang = getattr(self, 'language', 'python').lower()

        if self._is_scintilla():
            line, col = self.getCursorPosition()
            text = self.text()
        else:
            cursor = self.textCursor()
            saved_pos = cursor.position()
            text = self.toPlainText()

        lines = text.split('\n')
        cleaned_lines = [l.rstrip('\r').rstrip() for l in lines]

        if 'python' in lang:
            formatted_lines = self._format_python(cleaned_lines)
        elif any(l in lang for l in ('javascript', 'js', 'css')):
            formatted_lines = self._format_js_css(cleaned_lines)
        elif 'html' in lang or 'xml' in lang:
            formatted_lines = self._format_html(cleaned_lines)
        else:
            formatted_lines = cleaned_lines

        formatted_text = '\n'.join(formatted_lines)

        if formatted_text != text:
            if self._is_scintilla():
                self.setText(formatted_text)
                self.setCursorPosition(min(line, max(0, self.lines() - 1)), col)
            else:
                cursor.beginEditBlock()
                cursor.select(QTextCursor.SelectionType.Document)
                cursor.insertText(formatted_text)
                cursor.endEditBlock()
                cursor.setPosition(min(saved_pos, len(self.toPlainText())))
                self.setTextCursor(cursor)

    def _format_python(self, lines: list[str]) -> list[str]:
        """Python uchun ortiqcha bo'sh qatorlarni qisqartirish."""
        cleaned = []
        blank_count = 0
        for line in lines:
            if not line:
                blank_count += 1
                if blank_count <= 2:
                    cleaned.append("")
            else:
                blank_count = 0
                cleaned.append(line)
        return cleaned

    def _format_js_css(self, lines: list[str]) -> list[str]:
        """JavaScript va CSS uchun figurali qavslar ({}) bo'yicha indentatsiyani to'g'rilash."""
        formatted = []
        indent_level = 0
        indent_str = ' ' * getattr(self, 'tab_size', 4)

        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted.append('')
                continue

            leading_close = len(re.match(r'^\}*', stripped).group(0))
            current_indent = max(0, indent_level - leading_close)

            formatted.append(f"{indent_str * current_indent}{stripped}")

            open_b = stripped.count('{')
            close_b = stripped.count('}')
            indent_level = max(0, indent_level + (open_b - close_b))

        return formatted

    def _format_html(self, lines: list[str]) -> list[str]:
        """HTML / XML teglari bo'yicha darajalangan indentatsiyani shakllantirish."""
        formatted = []
        indent_level = 0
        indent_str = ' ' * getattr(self, 'tab_size', 4)
        void_tags = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted.append('')
                continue

            is_closing_start = re.match(r'^</[a-zA-Z0-9]+>', stripped)
            if is_closing_start:
                indent_level = max(0, indent_level - 1)

            formatted.append(f"{indent_str * indent_level}{stripped}")

            open_tags = re.findall(r'<([a-zA-Z0-9]+)(?:\s+[^/>]*)?>', stripped)
            close_tags = re.findall(r'</([a-zA-Z0-9]+)>', stripped)

            valid_open = [t.lower() for t in open_tags if t.lower() not in void_tags]

            if not is_closing_start:
                indent_level = max(0, indent_level + len(valid_open) - len(close_tags))

        return formatted


class ScodeTextEdit(SmartEditorMixin, QTextEdit):
    def __init__(self, parent=None, language='python', tab_size=4):
        super().__init__(parent=parent, language=language, tab_size=tab_size)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Scode Editor - Smart Editor Test")
    window.resize(800, 600)

    editor = ScodeTextEdit(language="python")
    editor.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 14px;")

    window.setCentralWidget(editor)
    window.show()
    sys.exit(app.exec())
