import os
import json
import subprocess
import re
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QKeySequence, QShortcut, QFont, QColor
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QWidget,
    QMessageBox,
    QApplication,
)
from PyQt6.Qsci import QsciScintilla

from app.utils.config import ConfigManager


# =============================================================================
# 1. Floating Dialog Overlays (GoToLineDialog & FindReplaceDialog)
# =============================================================================

class GoToLineDialog(QDialog):
    """
    Floating Go To Line Dialog (Ctrl + G).
    Foydalanuvchi belgilagan qatorga tezkor o'tish oynasi.
    """

    def __init__(self, current_line: int, total_lines: int, parent=None):
        super().__init__(parent)
        self.total_lines = total_lines
        self.target_line = None

        self.setWindowTitle("Qatorga O'tish")
        self.setFixedSize(360, 140)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        self._build_ui(current_line, total_lines)

    def _build_ui(self, current_line: int, total_lines: int):
        self.setStyleSheet("""
            QDialog {
                background-color: #1f1f1f;
                border: 1px solid #007acc;
                border-radius: 8px;
            }
            QLabel {
                color: #cccccc;
                font-size: 13px;
            }
            QLineEdit {
                background-color: #252526;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 8px 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        info_label = QLabel(f"Qator raqami (1 - {total_lines}, joriy: {current_line}):")
        layout.addWidget(info_label)

        self.line_input = QLineEdit()
        self.line_input.setPlaceholderText("Masalan: 42")
        self.line_input.setText(str(current_line))
        self.line_input.selectAll()
        layout.addWidget(self.line_input)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.ok_btn = QPushButton("O'tish")
        self.ok_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.ok_btn)

        self.cancel_btn = QPushButton("Bekor Qilish")
        self.cancel_btn.setStyleSheet("background-color: #3c3c3c;")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        self.line_input.returnPressed.connect(self._on_confirm)

    def _on_confirm(self):
        text = self.line_input.text().strip()
        if text.isdigit():
            val = int(text)
            if 1 <= val <= self.total_lines:
                self.target_line = val
                self.accept()
                return
        QMessageBox.warning(self, "Xatolik", f"Iltimos 1 va {self.total_lines} oralig'ida to'g'ri qator raqami kiriting!")


class FindReplaceDialog(QDialog):
    """
    Floating Find & Replace Dialog (Ctrl + F / Ctrl + H).
    Matnlarni tezkor qidirish va almashtirish dialogi.
    """

    def __init__(self, editor: QsciScintilla, show_replace: bool = False, parent=None):
        super().__init__(parent)
        self.editor = editor

        self.setWindowTitle("Almashtirish" if show_replace else "Qidirish")
        self.setFixedSize(450, 180 if show_replace else 130)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        self._build_ui(show_replace)

    def _build_ui(self, show_replace: bool):
        self.setStyleSheet("""
            QDialog {
                background-color: #1f1f1f;
                border: 1px solid #007acc;
                border-radius: 8px;
            }
            QLineEdit {
                background-color: #252526;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # 1. Qidiruv qatori
        find_layout = QHBoxLayout()
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Qidiriladigan matn...")
        if self.editor and self.editor.hasSelectedText():
            self.find_input.setText(self.editor.selectedText())
        find_layout.addWidget(self.find_input, 1)

        self.find_btn = QPushButton("Keyingisi")
        self.find_btn.clicked.connect(self._find_next)
        find_layout.addWidget(self.find_btn)
        layout.addLayout(find_layout)

        # 2. Almashtirish qatori
        if show_replace:
            replace_layout = QHBoxLayout()
            self.replace_input = QLineEdit()
            self.replace_input.setPlaceholderText("Yangi matn...")
            replace_layout.addWidget(self.replace_input, 1)

            self.replace_btn = QPushButton("Almashtirish")
            self.replace_btn.clicked.connect(self._replace_one)
            replace_layout.addWidget(self.replace_btn)

            self.replace_all_btn = QPushButton("Barchasi")
            self.replace_all_btn.clicked.connect(self._replace_all)
            replace_layout.addWidget(self.replace_all_btn)
            layout.addLayout(replace_layout)

        # Yopish tugmasi
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("Yopish (Esc)")
        close_btn.setStyleSheet("background-color: #3c3c3c;")
        close_btn.clicked.connect(self.reject)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

        self.find_input.returnPressed.connect(self._find_next)

    def _find_next(self):
        text = self.find_input.text()
        if not text or not self.editor:
            return
        found = self.editor.findFirst(text, False, False, False, True, True)
        if not found:
            # Fayl boshidan qayta izlash
            self.editor.setCursorPosition(0, 0)
            self.editor.findFirst(text, False, False, False, True, True)

    def _replace_one(self):
        if not self.editor:
            return
        find_text = self.find_input.text()
        replace_text = getattr(self, "replace_input", QLineEdit()).text()
        if self.editor.hasSelectedText() and self.editor.selectedText() == find_text:
            self.editor.replace(replace_text)
        self._find_next()

    def _replace_all(self):
        if not self.editor:
            return
        find_text = self.find_input.text()
        replace_text = getattr(self, "replace_input", QLineEdit()).text()
        if not find_text:
            return

        self.editor.setCursorPosition(0, 0)
        count = 0
        while self.editor.findFirst(find_text, False, False, False, True, True):
            self.editor.replace(replace_text)
            count += 1
        QMessageBox.information(self, "Natija", f"{count} ta almashtirish bajarildi.")


# =============================================================================
# 2. PersistenceMixin (AppData/Local/ScodeEditor Sessiyani Saqlash & Tiklash)
# =============================================================================

class PersistenceMixin:
    """
    Sessiyani AppData/Roaming/ScodeEditor/session.json va AppData/Local/ScodeEditor/session.json papkasida saqlash hamda tiklash mixini.
    """

    def save_session_state(self):
        """
        Joriy ochiq fayllar, tablar, kursor va skroll o'rinlari hamda oyna holatini session.json ga saqlash.
        """
        try:
            from app.core.session_manager import SessionManager
            main_win = self.window() if hasattr(self, 'window') else None
            sm = SessionManager(main_window=main_win)
            sm.save_session(editor_view=self)
        except Exception as e:
            print(f"Sessiyani saqlashda xatolik: {e}")

    def restore_session_state(self):
        """
        AppData/Roaming/ScodeEditor/session.json dan oxirgi ochiq tablar va kursor o'rinlarini tiklash.
        """
        try:
            from app.core.session_manager import SessionManager
            main_win = self.window() if hasattr(self, 'window') else None
            sm = SessionManager(main_window=main_win)
            sm.restore_session(editor_view=self)
        except Exception as e:
            print(f"Sessiyani tiklashda xatolik: {e}")



# =============================================================================
# 3. SplitViewMixin (Multi-Tab va Split View Ctrl + \\)
# =============================================================================

class SplitViewMixin:
    r"""
    Multi-Tab va Split View (Ctrl + \) yonma-yon redaktor oynalarini boshqarish mixini.
    """

    def _ensure_split_widget(self):
        splitter = getattr(self, 'editor_splitter', None) or getattr(self, 'top_hsplitter', None)
        
        is_valid = False
        if hasattr(self, 'right_tab_widget') and self.right_tab_widget is not None:
            try:
                _ = self.right_tab_widget.count()
                is_valid = True
            except (RuntimeError, AttributeError):
                is_valid = False

        if not is_valid:
            parent_widget = self if isinstance(self, QWidget) else None
            from app.ui.editor_tabs import EditorTabWidget
            new_tab_widget = EditorTabWidget(is_secondary=True, parent=parent_widget)
            new_tab_widget.setMinimumWidth(150)
            new_tab_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            if hasattr(self, 'tab_widget') and self.tab_widget:
                new_tab_widget.setStyleSheet(self.tab_widget.styleSheet())
            new_tab_widget.tabCloseRequested.connect(self._close_split_tab)
            new_tab_widget.split_tab_requested.connect(self._handle_split_tab)
            new_tab_widget.close_split_requested.connect(self._handle_close_split)
            if hasattr(self, '_on_right_tab_changed'):
                new_tab_widget.currentChanged.connect(self._on_right_tab_changed)

            self.right_tab_widget = new_tab_widget
            if splitter:
                splitter.setChildrenCollapsible(False)
                splitter.addWidget(self.right_tab_widget)

        self.right_tab_widget.show()
        self.right_tab_widget.setVisible(True)
        self.right_tab_widget.raise_()

        self._refresh_split_layout()

    def _handle_split_mode(self, mode: str):
        splitter = getattr(self, 'editor_splitter', None) or getattr(self, 'top_hsplitter', None)
        if mode == "vertical":
            if splitter:
                splitter.setOrientation(Qt.Orientation.Horizontal)
        else:
            if splitter:
                splitter.setOrientation(Qt.Orientation.Vertical)
        self.cmd_toggle_split()

    def _handle_split_tab(self, tab_index: int, direction: str):
        target_tabs = getattr(self, 'active_tab_widget', None) or getattr(self, 'tab_widget', None)
        if not target_tabs or tab_index < 0 or tab_index >= target_tabs.count():
            return

        w = target_tabs.widget(tab_index)
        ed = self._extract_editor(w) if hasattr(self, '_extract_editor') else None
        file_path = getattr(ed, 'file_path', None) if ed else getattr(self, 'current_file_path', None)

        if direction in ("right", "vertical"):
            if hasattr(self, 'editor_splitter') and self.editor_splitter:
                self.editor_splitter.setOrientation(Qt.Orientation.Horizontal)
        else:
            if hasattr(self, 'editor_splitter') and self.editor_splitter:
                self.editor_splitter.setOrientation(Qt.Orientation.Vertical)

        if file_path and os.path.exists(file_path):
            self.open_file(file_path, in_split=True)

    def _handle_close_split(self):
        if hasattr(self, 'right_tab_widget') and self.right_tab_widget:
            self.right_tab_widget.hide()
            self.right_tab_widget.setVisible(False)
            if hasattr(self, 'tab_widget'):
                self.active_tab_widget = self.tab_widget

    def _refresh_split_layout(self):
        splitter = getattr(self, 'editor_splitter', None) or getattr(self, 'top_hsplitter', None)
        if not splitter or not hasattr(self, 'right_tab_widget') or not self.right_tab_widget:
            return

        if self.right_tab_widget.isVisible():
            left_tab = getattr(self, 'tab_widget', None)
            idx0 = splitter.indexOf(left_tab) if left_tab else 0
            idx1 = splitter.indexOf(self.right_tab_widget)

            if idx0 >= 0:
                splitter.setStretchFactor(idx0, 1)
            if idx1 >= 0:
                splitter.setStretchFactor(idx1, 1)

            total = splitter.width()
            if total <= 100 and hasattr(self, 'width'):
                total = max(200, self.width() - 220)
            if total <= 100:
                total = 1000

            half = total // 2
            splitter.setSizes([half, half])
            splitter.refresh()
            splitter.update()

    def _close_split_tab(self, idx: int):
        if hasattr(self, 'right_tab_widget') and self.right_tab_widget:
            if hasattr(self, '_close_tab_in_widget'):
                self._close_tab_in_widget(self.right_tab_widget, idx)
            else:
                self.right_tab_widget.removeTab(idx)
            if self.right_tab_widget.count() == 0:
                self.right_tab_widget.hide()
                self.right_tab_widget.setVisible(False)
                if hasattr(self, 'tab_widget'):
                    self.active_tab_widget = self.tab_widget

    def cmd_toggle_split(self):
        r"""
        Ctrl + \ bosilganda joriy oynani 2 ta yonma-yon redaktor oynasiga bo'lish.
        """
        if hasattr(self, 'right_tab_widget') and self.right_tab_widget and self.right_tab_widget.isVisible() and self.right_tab_widget.count() > 0:
            self.right_tab_widget.hide()
            self.right_tab_widget.setVisible(False)
            if hasattr(self, 'tab_widget'):
                self.active_tab_widget = self.tab_widget
            return

        self._ensure_split_widget()

        ed_info = getattr(self, 'get_current_editor', lambda: (None, None))()
        editor = ed_info[0] if isinstance(ed_info, tuple) else ed_info
        file_path = getattr(self, 'current_file_path', None)
        if not file_path and isinstance(ed_info, tuple) and len(ed_info) > 1:
            file_path = ed_info[1]
        if not file_path and editor:
            file_path = getattr(editor, 'file_path', None)

        if file_path and os.path.exists(file_path):
            if hasattr(self, 'open_file'):
                self.open_file(file_path, in_split=True)
            else:
                self._open_file_in_split_tab(file_path)
        else:
            if self.right_tab_widget.count() == 0:
                self.right_tab_widget.hide()
                self.right_tab_widget.setVisible(False)

    def toggle_split_view(self):
        """Alias for cmd_toggle_split"""
        self.cmd_toggle_split()

    def cmd_open_file_in_split(self, file_path: str):
        """Faylni Split View (o'ng tomondagi ikkinchi redaktor oynasi) da ochish"""
        if not file_path or not os.path.exists(file_path):
            return

        self._ensure_split_widget()
        if hasattr(self, 'open_file'):
            self.open_file(file_path, in_split=True)
        else:
            self._open_file_in_split_tab(file_path)

        if hasattr(self, 'right_tab_widget') and self.right_tab_widget:
            self.right_tab_widget.show()
            self.right_tab_widget.setVisible(True)
            self.right_tab_widget.raise_()
            self.active_tab_widget = self.right_tab_widget
        self._refresh_split_layout()

    def open_file_in_split_view(self, file_path: str):
        """Alias for cmd_open_file_in_split"""
        self.cmd_open_file_in_split(file_path)

    def _open_file_in_split_tab(self, file_path: str):
        self._ensure_split_widget()
        if hasattr(self, 'open_file'):
            self.open_file(file_path, in_split=True)
            return

        if not hasattr(self, 'right_tab_widget') or not self.right_tab_widget:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                content = handle.read()

            from app.ui.editor_scintilla import ScodeScintillaEditor

            cfg = getattr(self, 'config', None) or ConfigManager()
            settings = cfg.get_settings()

            parent_widget = self.right_tab_widget
            editor = ScodeScintillaEditor(parent=parent_widget)
            editor.file_path = file_path

            try:
                from app.ui.editor_view import apply_lexer_for_file
                apply_lexer_for_file(editor, file_path)
            except Exception:
                pass

            editor.apply_settings(
                font_family=settings.get("font_family", "Consolas"),
                font_size=settings.get("font_size", 11),
                tab_size=settings.get("tab_size", 4),
            )
            editor.setText(content)
            editor.setModified(False)

            from app.ui.editor_view import EditorTabContainer
            container = EditorTabContainer(editor, show_minimap=settings.get("show_minimap", True), parent=parent_widget)
            idx = self.right_tab_widget.addTab(container, os.path.basename(file_path))
            self.right_tab_widget.setTabToolTip(idx, file_path)
            self.right_tab_widget.setCurrentIndex(idx)
            self.right_tab_widget.show()
            self.right_tab_widget.setVisible(True)
            self.right_tab_widget.raise_()
            self.active_tab_widget = self.right_tab_widget
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Split view tabda fayl ochishda xatolik: {e}")


# =============================================================================
# 4. FloatingOverlaysMixin (Ctrl+P, Ctrl+Shift+P, Ctrl+G, Ctrl+F/H)
# =============================================================================

class FloatingOverlaysMixin:
    """
    Floating dialog overlays (Quick Open, Command Palette, Go to Line, Find & Replace).
    SearchPanel is the primary find/replace panel.
    """

    def cmd_quick_open(self):
        """Ctrl + P: Tezkor Fayl Qidiruv Modalini ochish"""
        path = getattr(self, 'project_path', None)
        if not path or not os.path.exists(path):
            curr_file = getattr(self, 'current_file_path', None)
            if curr_file and os.path.exists(curr_file):
                path = os.path.dirname(curr_file)
            else:
                path = os.getcwd()

        if not path or not os.path.exists(path):
            return

        from app.ui.quick_open import QuickOpenDialog
        dialog = QuickOpenDialog(self if isinstance(self, QWidget) else None, path)
        if hasattr(self, 'geometry'):
            geo = self.geometry()
            x = geo.x() + (geo.width() - dialog.width()) // 2
            y = geo.y() + (geo.height() - dialog.height()) // 2
            dialog.move(max(0, x), max(0, y))

        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_file_path:
            if hasattr(self, 'open_file'):
                self.open_file(dialog.selected_file_path)

    def open_quick_open_dialog(self):
        """Alias for cmd_quick_open"""
        self.cmd_quick_open()

    def cmd_goto_line(self):
        """Ctrl + G: Floating Go to Line Dialog"""
        ed_info = getattr(self, 'get_current_editor', lambda: (None, None))()
        editor = ed_info[0] if isinstance(ed_info, tuple) else ed_info
        if not editor or not hasattr(editor, 'lines'):
            return

        current_line, _ = editor.getCursorPosition()
        total_lines = editor.lines()

        dialog = GoToLineDialog(current_line + 1, total_lines, parent=self if isinstance(self, QWidget) else None)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.target_line:
            editor.setCursorPosition(dialog.target_line - 1, 0)
            editor.setFocus()

    def show_goto_line_dialog(self):
        """Alias for cmd_goto_line"""
        self.cmd_goto_line()

    def cmd_find_in_file(self):
        """Ctrl + F: SearchPanel (Primary Find Panel)"""
        ed_info = getattr(self, 'get_current_editor', lambda: (None, None))()
        editor = ed_info[0] if isinstance(ed_info, tuple) else ed_info
        sel = editor.selectedText() if editor and editor.hasSelectedText() else ""
        if hasattr(self, 'search_panel') and self.search_panel:
            self.search_panel.show_find(sel)
        elif editor:
            dialog = FindReplaceDialog(editor, show_replace=False, parent=self if isinstance(self, QWidget) else None)
            dialog.exec()

    def show_find_dialog(self):
        """Alias for cmd_find_in_file"""
        self.cmd_find_in_file()

    def cmd_replace_in_file(self):
        """Ctrl + H: SearchPanel (Primary Replace Panel)"""
        ed_info = getattr(self, 'get_current_editor', lambda: (None, None))()
        editor = ed_info[0] if isinstance(ed_info, tuple) else ed_info
        sel = editor.selectedText() if editor and editor.hasSelectedText() else ""
        if hasattr(self, 'search_panel') and self.search_panel:
            self.search_panel.show_replace(sel)
        elif editor:
            dialog = FindReplaceDialog(editor, show_replace=True, parent=self if isinstance(self, QWidget) else None)
            dialog.exec()

    def show_replace_dialog(self):
        """Alias for cmd_replace_in_file"""
        self.cmd_replace_in_file()


# =============================================================================
# 5. EditorCommandsMixin (19 VS Code Shortcuts & High-performance Editing)
# =============================================================================

class EditorCommandsMixin:
    """
    19 ta VS Code qisqartmalari va QScintilla bilan yuqori unumdor tahrirlash mixini.
    """

    def _get_active_editor(self) -> QsciScintilla:
        if hasattr(self, 'get_current_editor'):
            res = self.get_current_editor()
            ed = res[0] if isinstance(res, tuple) else res
            if ed and isinstance(ed, QsciScintilla):
                return ed
        return None

    def _get_comment_tags(self, ed) -> tuple[str, str, str]:
        """Returns (line_prefix, block_open, block_close) based on file extension."""
        file_path = getattr(ed, 'file_path', '') or ''
        ext = os.path.splitext(file_path)[1].lower()

        if ext in ['.html', '.htm', '.xml', '.svg']:
            return ('<!--', '<!--', '-->')
        elif ext in ['.css', '.scss', '.less']:
            return ('/*', '/*', '*/')
        elif ext in ['.py', '.sh', '.bash', '.yaml', '.yml']:
            return ('#', '"""', '"""')
        else:
            return ('//', '/*', '*/')

    # 1. Ctrl + D: Multi-cursor / So'zni tanlash
    def cmd_select_next_occurrence(self):
        ed = self._get_active_editor()
        if not ed:
            return
        if not ed.hasSelectedText():
            line, col = ed.getCursorPosition()
            line_text = ed.text(line)
            match = re.search(r'\b\w+\b', line_text[col:]) or re.search(r'\b\w+\b', line_text[:col])
            if match:
                ed.SendScintilla(QsciScintilla.SCI_WORDSELECT)
        else:
            sel_text = ed.selectedText()
            ed.findFirst(sel_text, False, False, False, True, True)

    def select_next_occurrence(self):
        self.cmd_select_next_occurrence()

    # 2. Ctrl + Enter: Pastdan yangi qator ochish
    def cmd_insert_line_below(self):
        ed = self._get_active_editor()
        if not ed:
            return
        line, _ = ed.getCursorPosition()
        line_text = ed.text(line).rstrip('\r\n')
        indent_match = re.match(r'^(\s*)', line_text)
        indent = indent_match.group(1) if indent_match else ''

        ed.setCursorPosition(line, len(line_text))
        ed.insert('\n' + indent)
        ed.setCursorPosition(line + 1, len(indent))

    def insert_line_below(self):
        self.cmd_insert_line_below()

    # 3. Ctrl + Shift + Enter: Yuqoridan yangi qator ochish
    def cmd_insert_line_above(self):
        ed = self._get_active_editor()
        if not ed:
            return
        line, _ = ed.getCursorPosition()
        line_text = ed.text(line).rstrip('\r\n')
        indent_match = re.match(r'^(\s*)', line_text)
        indent = indent_match.group(1) if indent_match else ''

        ed.setCursorPosition(line, 0)
        ed.insert(indent + '\n')
        ed.setCursorPosition(line, len(indent))

    def insert_line_above(self):
        self.cmd_insert_line_above()

    # 4. Ctrl + Shift + K: Qatorni o'chirish
    def cmd_delete_current_line(self):
        ed = self._get_active_editor()
        if ed:
            ed.SendScintilla(QsciScintilla.SCI_LINEDELETE)

    def delete_current_line(self):
        self.cmd_delete_current_line()

    # 5. Alt + Up: Qatorni yuqoriga surish
    def cmd_move_line_up(self):
        ed = self._get_active_editor()
        if ed:
            ed.SendScintilla(QsciScintilla.SCI_MOVESELECTEDLINESUP)

    def move_line_up(self):
        self.cmd_move_line_up()

    # 6. Alt + Down: Qatorni pastga surish
    def cmd_move_line_down(self):
        ed = self._get_active_editor()
        if ed:
            ed.SendScintilla(QsciScintilla.SCI_MOVESELECTEDLINESDOWN)

    def move_line_down(self):
        self.cmd_move_line_down()

    # 7. Shift + Alt + Down: Qatorni pastga nusxalash
    def cmd_duplicate_line_down(self):
        ed = self._get_active_editor()
        if ed:
            ed.SendScintilla(QsciScintilla.SCI_SELECTIONDUPLICATE)

    def duplicate_line_down(self):
        self.cmd_duplicate_line_down()

    # 8. Shift + Alt + Up: Qatorni yuqoriga nusxalash
    def cmd_duplicate_line_up(self):
        ed = self._get_active_editor()
        if ed:
            ed.SendScintilla(QsciScintilla.SCI_SELECTIONDUPLICATE)
            ed.SendScintilla(QsciScintilla.SCI_MOVESELECTEDLINESUP)

    def duplicate_line_up(self):
        self.cmd_duplicate_line_up()

    # 9. Ctrl + /: Line Comment (Qatorli Izoh)
    def cmd_toggle_line_comment(self):
        ed = self._get_active_editor()
        if not ed:
            return
        line, col = ed.getCursorPosition()
        line_text = ed.text(line)
        stripped = line_text.strip()

        prefix, _, _ = self._get_comment_tags(ed)

        if prefix == '<!--':
            if stripped.startswith('<!--') and stripped.endswith('-->'):
                new_text = line_text.replace('<!--', '', 1).replace('-->', '', 1).rstrip('\r\n') + '\n'
            else:
                indent_match = re.match(r'^(\s*)', line_text)
                indent = indent_match.group(1) if indent_match else ''
                new_text = indent + '<!-- ' + line_text[len(indent):].rstrip('\r\n') + ' -->\n'
        else:
            if stripped.startswith(prefix):
                pos = line_text.find(prefix)
                space_after = 1 if len(line_text) > pos + len(prefix) and line_text[pos + len(prefix)] == ' ' else 0
                new_text = line_text[:pos] + line_text[pos + len(prefix) + space_after:]
            else:
                indent_match = re.match(r'^(\s*)', line_text)
                indent = indent_match.group(1) if indent_match else ''
                new_text = indent + prefix + ' ' + line_text[len(indent):]

        ed.setSelection(line, 0, line, len(line_text))
        ed.replaceSelectedText(new_text)
        ed.setCursorPosition(line, min(col, len(new_text)))

    def toggle_line_comment(self):
        self.cmd_toggle_line_comment()

    # 10. Shift + Alt + A: Block Comment (Blokli Izoh)
    def cmd_toggle_block_comment(self):
        ed = self._get_active_editor()
        if not ed:
            return
        _, open_tag, close_tag = self._get_comment_tags(ed)

        if ed.hasSelectedText():
            text = ed.selectedText()
            if text.startswith(open_tag) and text.endswith(close_tag):
                ed.replaceSelectedText(text[len(open_tag):-len(close_tag)].strip())
            else:
                ed.replaceSelectedText(f"{open_tag} {text} {close_tag}")
        else:
            line, col = ed.getCursorPosition()
            line_text = ed.text(line)
            ed.setSelection(line, 0, line, len(line_text))
            text = ed.selectedText()
            if text.strip().startswith(open_tag) and text.strip().endswith(close_tag):
                new_text = text.replace(open_tag, '').replace(close_tag, '').strip() + '\n'
            else:
                indent_match = re.match(r'^(\s*)', text)
                indent = indent_match.group(1) if indent_match else ''
                new_text = f"{indent}{open_tag} {text.strip()} {close_tag}\n"
            ed.replaceSelectedText(new_text)

    def toggle_block_comment(self):
        self.cmd_toggle_block_comment()

    # 11. Ctrl + Shift + \: Go to Matching Bracket (Juft qavsga o'tish)
    def cmd_goto_matching_bracket(self):
        ed = self._get_active_editor()
        if not ed:
            return
        line, col = ed.getCursorPosition()
        pos = ed.positionFromLineIndex(line, col)

        match_pos = ed.SendScintilla(QsciScintilla.SCI_BRACEMATCH, pos)
        if match_pos >= 0:
            ed.SendScintilla(QsciScintilla.SCI_GOTOPOS, match_pos)

    def goto_matching_bracket(self):
        self.cmd_goto_matching_bracket()

    # 12. Ctrl + Shift + T: Tashqi terminalni ochish (subprocess)
    def cmd_open_external_terminal(self):
        path = getattr(self, 'project_path', None) or os.getcwd()
        try:
            if sys.platform == 'win32':
                subprocess.Popen(['cmd.exe', '/k', f'cd /d "{path}"'])
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', '-a', 'Terminal', path])
            else:
                subprocess.Popen(['x-terminal-emulator'], cwd=path)
        except Exception as e:
            print(f"Tashqi terminal ochishda xatolik: {e}")

    def open_external_terminal(self):
        self.cmd_open_external_terminal()

    # 13. Ctrl + B: Sidebar'ni yashirish/ko'rsatish
    def cmd_toggle_sidebar(self):
        sidebar = getattr(self, 'file_tree', None) or getattr(self, 'tree_view', None) or getattr(self, 'left_panel', None)
        if sidebar:
            sidebar.setVisible(not sidebar.isVisible())

    def toggle_sidebar(self):
        self.cmd_toggle_sidebar()

    # 14. Ctrl + W: Joriy tabni yopish
    def cmd_close_tab(self):
        target = getattr(self, 'active_tab_widget', None) or getattr(self, 'tab_widget', None)
        if target and target.count() > 0:
            idx = target.currentIndex()
            if hasattr(self, '_close_tab_in_widget'):
                self._close_tab_in_widget(target, idx)
            elif hasattr(self, '_close_tab') and target == getattr(self, 'tab_widget', None):
                self._close_tab(idx)
            else:
                target.removeTab(idx)

    def close_current_tab(self):
        self.cmd_close_tab()

    # 15. Ctrl + Tab: Keyingi tabga o'tish
    def cmd_next_tab(self):
        target = getattr(self, 'active_tab_widget', None) or getattr(self, 'tab_widget', None)
        if target and target.count() > 1:
            idx = (target.currentIndex() + 1) % target.count()
            target.setCurrentIndex(idx)

    def next_tab(self):
        self.cmd_next_tab()

    # 16. Ctrl + Shift + Tab: Oldingi tabga o'tish
    def cmd_prev_tab(self):
        target = getattr(self, 'active_tab_widget', None) or getattr(self, 'tab_widget', None)
        if target and target.count() > 1:
            idx = (target.currentIndex() - 1) % target.count()
            target.setCurrentIndex(idx)

    def prev_tab(self):
        self.cmd_prev_tab()
