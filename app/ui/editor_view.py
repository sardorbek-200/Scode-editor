import os
import re
import sys
import shutil
import subprocess
import webbrowser

from PyQt6.Qsci import (
    QsciScintilla,
    QsciLexerPython,
    QsciLexerJavaScript,
    QsciLexerHTML,
    QsciLexerCSS,
    QsciLexerCPP,
    QsciLexerJSON,
    QsciLexerXML,
)
from PyQt6.QtCore import Qt, QDir, QTimer, QSize, QUrl, QModelIndex
from PyQt6.QtGui import QCursor, QKeySequence, QShortcut, QColor, QFont, QDesktopServices, QPainter, QPen

def apply_lexer_for_file(editor, filepath: str):
    """
    Fayl kengaytmasiga ko'ra QsciLexer obyektini biriktirish va GC dan saqlash uchun editor.current_lexer ga biriktirish
    """
    if not editor or not filepath:
        return

    ext = os.path.splitext(filepath)[1].lower().lstrip('.')
    font = QFont("Consolas", 11)

    lexer = None
    if ext in ['html', 'htm']:
        lexer = QsciLexerHTML(editor)
    elif ext in ['py', 'pyw']:
        lexer = QsciLexerPython(editor)
    elif ext in ['jsx', 'tsx']:
        from app.ui.editor_scintilla import JSXCustomLexer
        lexer = JSXCustomLexer(editor)
    elif ext in ['js', 'ts']:
        lexer = QsciLexerJavaScript(editor)
    elif ext == 'json':
        lexer = QsciLexerJSON(editor)
    elif ext in ['css', 'scss', 'less']:
        lexer = QsciLexerCSS(editor)
    elif ext in ['xml', 'svg']:
        lexer = QsciLexerXML(editor)
    elif ext in ['cpp', 'c', 'h', 'hpp', 'cs']:
        lexer = QsciLexerCPP(editor)

    if lexer:
        lexer.setFont(font)
        dark_bg = QColor("#1e1e1e")
        margin_fg = QColor("#858585")
        lexer.setDefaultPaper(dark_bg)
        lexer.setPaper(dark_bg)
        for style in range(128):
            lexer.setPaper(dark_bg, style)
        lexer.setPaper(dark_bg, QsciScintilla.STYLE_LINENUMBER)
        lexer.setColor(margin_fg, QsciScintilla.STYLE_LINENUMBER)

        editor.current_lexer = lexer
        editor.set_lexer_for_file(filepath)
    else:
        editor.current_lexer = None
        editor.setLexer(None)

    if hasattr(editor, "_enforce_dark_margins"):
        editor._enforce_dark_margins()
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTreeView,
    QVBoxLayout,
    QWidget,
    QMenu,
    QInputDialog,
    QDialog,
)

try:
    from PyQt6.QtWidgets import QFileSystemModel
except ImportError:
    from PyQt6.QtGui import QFileSystemModel

from app.utils.installer import PackageInstallerThread
from app.utils.icon_manager import IconManager
from app.utils.config import ConfigManager
from app.ui.editor_scintilla import ScodeScintillaEditor
from app.ui.smart_editor_mixin import SmartEditorMixin, ScodeTextEdit
from app.ui.smart_keybinding_palette_mixin import SmartKeyBindingAndPaletteMixin
from app.ui.vscode_editor_mixins import (
    PersistenceMixin,
    SplitViewMixin,
    FloatingOverlaysMixin,
    EditorCommandsMixin,
)
from app.ui.terminal_panel import TerminalPanel
from app.ui.search_panel import SearchPanel
from app.ui.quick_open import QuickOpenDialog
from app.ui.settings_dialog import SettingsDialog
from app.ui.tree_icon_provider import ScodeTreeIconProvider, ScodeFileSystemModel
from app.ui.custom_file_explorer import CustomFileExplorer
from app.ui.breadcrumbs_bar import BreadcrumbsBar
from app.core.backup_manager import AutoSaveBackupManager
from app.ui.editor_tabs import EditorTabWidget, EditorTabsManager




class MinimapViewportOverlay(QWidget):
    """Minimap ichidagi hozirgi ko'rinish maydonini ko'rsatadigan yarim shaffof overlay."""

    def __init__(self, minimap: QsciScintilla):
        super().__init__(minimap)
        self.minimap = minimap
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.raise_()

    def paintEvent(self, event):
        if not self.minimap or not self.minimap.isVisible():
            return

        total_lines = max(1, self.minimap.lines())
        scroll_bar = self.minimap.verticalScrollBar()
        scroll_max = max(1, scroll_bar.maximum() if scroll_bar is not None else 1)
        visible_lines = max(1, int((self.minimap.height() / max(1, self.minimap.fontMetrics().height()))))
        visible_lines = min(visible_lines, total_lines)
        if total_lines <= visible_lines:
            return

        visible_ratio = max(0.08, min(1.0, visible_lines / total_lines))
        current_top = max(0, min(int((scroll_bar.value() if scroll_bar is not None else 0) * total_lines / scroll_max), total_lines - visible_lines))
        viewport_top = int((current_top / max(1, total_lines - visible_lines)) * max(0, self.height() - 1))
        viewport_height = max(18, int(self.height() * visible_ratio))
        viewport_height = min(viewport_height, self.height() - viewport_top)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(255, 255, 255, 38), 1))
        painter.setBrush(QColor(255, 255, 255, 18))
        painter.drawRect(1, viewport_top + 1, self.width() - 3, max(12, viewport_height - 2))


class EditorTabContainer(QWidget):
    """Redaktor va o'ng tomondagi Mini-map vidjetini o'z ichiga oluvchi tab konteyneri"""

    def __init__(self, editor: ScodeScintillaEditor, show_minimap: bool = True, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.minimap = QsciScintilla()
        self.minimap_overlay = None
        self._build_ui(show_minimap)

    def _build_ui(self, show_minimap: bool):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.editor, 1)

        # Mini-map sozlamalari
        self.minimap.setFixedWidth(86)
        self.minimap.setMarginWidth(0, 0)
        self.minimap.setMarginWidth(1, 0)
        self.minimap.setMarginWidth(2, 0)
        self.minimap.setReadOnly(True)
        self.minimap.setPaper(QColor("#1e1e1e"))
        self.minimap.setColor(QColor("#a1a1aa"))
        self.minimap.setFont(QFont("Consolas", 3))
        self.minimap.setCaretLineVisible(False)
        self.minimap.setWrapMode(QsciScintilla.WrapMode.WrapNone)
        self.minimap.setExtraAscent(1)
        self.minimap.setExtraDescent(1)
        self.minimap.verticalScrollBar().setStyleSheet(
            """
            QScrollBar:vertical {
                background: transparent;
                width: 5px;
                margin: 0px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.18);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 3px;
                min-height: 40px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
                border: none;
                height: 0px;
            }
            """
        )
        self.minimap.setStyleSheet(
            "QWidget { background: #1e1e1e; border: 1px solid rgba(255, 255, 255, 0.08); }"
        )

        # Sinxronizatsiya: Matn va Scrollbar
        self.minimap.setText(self.editor.text())
        self.editor.textChanged.connect(lambda: self.minimap.setText(self.editor.text()))
        self.editor.verticalScrollBar().valueChanged.connect(self.minimap.verticalScrollBar().setValue)
        self.minimap.verticalScrollBar().valueChanged.connect(self.editor.verticalScrollBar().setValue)

        self.minimap.setVisible(show_minimap)
        self.minimap_overlay = MinimapViewportOverlay(self.minimap)
        self.minimap_overlay.setGeometry(0, 0, self.minimap.width(), self.minimap.height())
        self.minimap_overlay.setVisible(show_minimap)
        self.minimap.verticalScrollBar().valueChanged.connect(self.minimap_overlay.update)
        self.minimap.textChanged.connect(self.minimap_overlay.update)
        layout.addWidget(self.minimap)

    def set_minimap_visible(self, visible: bool):
        self.minimap.setVisible(visible)
        if self.minimap_overlay is not None:
            self.minimap_overlay.setVisible(visible)
            self.minimap_overlay.update()


class EditorView(
    PersistenceMixin,
    SplitViewMixin,
    FloatingOverlaysMixin,
    EditorCommandsMixin,
    SmartKeyBindingAndPaletteMixin,
    QWidget
):
    """
    QScintilla asosidagi kod redaktori (VS Code modular mixinlari bilan).
    """

    def __init__(self, parent=None, on_back=None):
        super().__init__(parent)
        self.parent_window = parent
        self.on_back = on_back
        self.project_path = None
        self.current_file_path = None
        self.installer_thread = None
        self.is_loading_file = False
        self.active_editor = None

        self._build_ui()
        self._setup_auto_save()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top bar panel (Breadcrumbs & Back button)
        top_bar_widget = QWidget()
        top_bar_widget.setObjectName("topBarPanel")
        top_bar = QHBoxLayout(top_bar_widget)
        top_bar.setContentsMargins(8, 4, 8, 4)
        top_bar.setSpacing(10)

        self.back_button = QPushButton(" Loyihalar")
        self.back_button.setIcon(IconManager.get_icon("arrow-left"))
        self.back_button.setIconSize(QSize(14, 14))
        self.back_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.back_button.clicked.connect(self._handle_back)
        top_bar.addWidget(self.back_button)

        self.path_label = QLabel("Loyiha tanlanmagan")
        self.path_label.setObjectName("breadcrumbPath")
        self.path_label.setWordWrap(True)
        top_bar.addWidget(self.path_label, 1)

        # Git Paneli tugmasi (Ctrl + Shift + G)
        self.git_button = QPushButton(" Git Boshqaruv")
        self.git_button.setIcon(IconManager.get_icon("git"))
        self.git_button.setIconSize(QSize(14, 14))
        self.git_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.git_button.setToolTip("Git Boshqaruv Panelini ochish (Ctrl + Shift + G)")
        self.git_button.clicked.connect(self.cmd_open_git)
        top_bar.addWidget(self.git_button)

        # Tashqi terminal tugmasi
        self.ext_terminal_button = QPushButton(" Tashqi terminal")
        self.ext_terminal_button.setIcon(IconManager.get_icon("terminal"))
        self.ext_terminal_button.setIconSize(QSize(14, 14))
        self.ext_terminal_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.ext_terminal_button.setToolTip("Loyiha papkasini operatsion tizimning alohida terminalida ochish")
        self.ext_terminal_button.clicked.connect(self.cmd_open_external_terminal)
        top_bar.addWidget(self.ext_terminal_button)

        # Matn Qidirish tugmasi (Ctrl + F)
        self.find_button = QPushButton(" Qidirish")
        self.find_button.setIcon(IconManager.get_icon("search"))
        self.find_button.setIconSize(QSize(14, 14))
        self.find_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.find_button.setToolTip("Matn Qidirish Panelini ochish (Ctrl + F)")
        self.find_button.clicked.connect(self.cmd_find_in_file)
        top_bar.addWidget(self.find_button)

        # Sozlamalar Tugmasi (Ctrl + ,)
        self.settings_button = QPushButton(" Sozlamalar")
        self.settings_button.setIcon(IconManager.get_icon("settings"))
        self.settings_button.setIconSize(QSize(14, 14))
        self.settings_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.settings_button.setToolTip("Sozlamalar (Ctrl + ,)")
        self.settings_button.clicked.connect(self.cmd_open_settings)
        top_bar.addWidget(self.settings_button)

        main_layout.addWidget(top_bar_widget)

        # Search / Replace panel (hidden by default)
        self.search_panel = SearchPanel(self)
        self.search_panel.find_next_requested.connect(lambda pattern, cs: self._find_next(pattern, cs))
        self.search_panel.find_prev_requested.connect(lambda pattern, cs: self._find_prev(pattern, cs))
        self.search_panel.replace_requested.connect(lambda a, b: self._replace_current(a, b))
        self.search_panel.replace_all_requested.connect(lambda a, b: self._replace_all(a, b))
        self.search_panel.closed.connect(self._on_search_closed)
        main_layout.addWidget(self.search_panel)

        # Breadcrumbs bar (24px height navigation bar)
        self.breadcrumbs_bar = BreadcrumbsBar(self)
        self.breadcrumbs_bar.file_selected.connect(self.open_file)
        main_layout.addWidget(self.breadcrumbs_bar)

        # Auto-Save & AppData Backup Manager
        self.backup_manager = AutoSaveBackupManager(interval_seconds=30, parent=self)

        self.top_hsplitter = QSplitter(Qt.Orientation.Horizontal)
        self.top_hsplitter.setHandleWidth(2)

        self.file_explorer = CustomFileExplorer()
        self.file_explorer.file_clicked.connect(self.open_file)

        self.model = ScodeFileSystemModel()
        self.icon_provider = ScodeTreeIconProvider(self.model)
        self.model.setIconProvider(self.icon_provider)

        self.file_tree = QTreeView()
        self.file_tree.setModel(self.model)
        self.file_tree.setAnimated(True)
        self.file_tree.setIndentation(12)
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setUniformRowHeights(True)
        self.file_tree.clicked.connect(self._handle_tree_click)
        self.file_tree.doubleClicked.connect(self._handle_tree_double_click)
        self.file_tree.expanded.connect(self._on_tree_item_expanded)
        self.file_tree.collapsed.connect(self._on_tree_item_collapsed)
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self._show_tree_context_menu)

        self.top_hsplitter.addWidget(self.file_explorer)

        # Inner Editor Splitter for side-by-side split view (Ctrl + \)
        self.editor_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.editor_splitter.setHandleWidth(2)
        self.editor_splitter.setChildrenCollapsible(False)
        self.editor_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.tab_widget = EditorTabWidget(is_secondary=False, parent=self)
        self.tab_widget.setMinimumWidth(150)
        self.tab_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.currentChanged.connect(self._on_left_tab_changed)
        self.tab_widget.split_requested.connect(self._handle_split_mode)
        self.tab_widget.split_tab_requested.connect(self._handle_split_tab)
        self.tab_widget.close_split_requested.connect(self._handle_close_split)

        self.active_tab_widget = self.tab_widget

        self.editor_splitter.addWidget(self.tab_widget)
        self.editor_splitter.setStretchFactor(0, 1)
        self.top_hsplitter.addWidget(self.editor_splitter)
        self.top_hsplitter.setStretchFactor(0, 0)
        self.top_hsplitter.setStretchFactor(1, 1)
        self.top_hsplitter.setSizes([240, 1000])
        main_layout.addWidget(self.top_hsplitter, 1)

        # Status Bar (Modern VS Code style dynamic status bar)
        status_bar_widget = QWidget()
        status_bar_widget.setStyleSheet("""
            QWidget {
                background-color: #007acc;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 11px;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 0 4px;
            }
        """)
        status_layout = QHBoxLayout(status_bar_widget)
        status_layout.setContentsMargins(10, 2, 10, 2)
        status_layout.setSpacing(12)

        self.status_label = QLabel("Tayyor")
        status_layout.addWidget(self.status_label, 1)

        self.selection_label = QLabel("")
        self.cursor_pos_label = QLabel("Ln 1, Col 1")
        self.doc_stats_label = QLabel("Lines: 0, Words: 0, Chars: 0")
        self.indent_label = QLabel("Spaces: 4")
        self.encoding_label = QLabel("UTF-8")

        status_layout.addWidget(self.selection_label)
        status_layout.addWidget(self.cursor_pos_label)
        status_layout.addWidget(self.doc_stats_label)
        status_layout.addWidget(self.indent_label)
        status_layout.addWidget(self.encoding_label)

        main_layout.addWidget(status_bar_widget)

        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        self.save_shortcut.activated.connect(self.cmd_save_file)

        # ▶ Run Shortcuts (Ctrl + F5 va F5)
        self.run_shortcut = QShortcut(QKeySequence("Ctrl+F5"), self)
        self.run_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.run_shortcut.activated.connect(self.cmd_run_active_file)
        self.f5_shortcut = QShortcut(QKeySequence("F5"), self)
        self.f5_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.f5_shortcut.activated.connect(self.cmd_run_active_file)

        # Ctrl + P Quick Open
        self.quick_open_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        self.quick_open_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.quick_open_shortcut.activated.connect(self.cmd_quick_open)

        # Ctrl + , Settings
        self.settings_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        self.settings_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        self.settings_shortcut.activated.connect(self.open_settings_dialog)

        # Find / Replace shortcuts
        self.find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.find_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.find_shortcut.activated.connect(self.cmd_find_in_file)

        self.replace_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        self.replace_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.replace_shortcut.activated.connect(self.cmd_replace_in_file)

        # Git Panel Shortcut (Ctrl + Shift + G)
        self.git_shortcut = QShortcut(QKeySequence("Ctrl+Shift+G"), self)
        self.git_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        self.git_shortcut.activated.connect(self.open_git_dialog)

        self.model = QFileSystemModel()
        self.model.setReadOnly(False)
        self.model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)
        self.file_tree.setModel(self.model)
        self.file_tree.hideColumn(1)
        self.file_tree.hideColumn(2)
        self.file_tree.hideColumn(3)

    def _setup_auto_save(self):
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.setInterval(1500)
        self.auto_save_timer.timeout.connect(self._handle_auto_save)
        # Ensure Esc hides search panel when visible
        self.escape_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.escape_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.escape_shortcut.activated.connect(self._on_escape_pressed)

    def _connect_editor_signals(self, editor: ScodeScintillaEditor) -> None:
        try:
            editor.textChanged.connect(self._on_editor_text_changed)
            editor.cursorPositionChanged.connect(self._on_cursor_position_changed)
            editor.selectionChanged.connect(self._on_selection_changed)
        except Exception:
            pass

    def _disconnect_editor_signals(self, editor: ScodeScintillaEditor) -> None:
        try:
            editor.textChanged.disconnect(self._on_editor_text_changed)
            editor.cursorPositionChanged.disconnect(self._on_cursor_position_changed)
            editor.selectionChanged.disconnect(self._on_selection_changed)
        except Exception:
            pass

    def _on_cursor_position_changed(self, line: int, col: int) -> None:
        self._update_status_bar_metrics(line=line, col=col)

    def _on_selection_changed(self) -> None:
        self._update_status_bar_metrics()

    def _update_status_bar_metrics(self, line: int = -1, col: int = -1) -> None:
        editor, _ = self.get_current_editor()
        if not editor or not hasattr(editor, "getCursorPosition"):
            return

        if line < 0 or col < 0:
            line, col = editor.getCursorPosition()

        if hasattr(self, 'cursor_pos_label') and self.cursor_pos_label:
            self.cursor_pos_label.setText(f"Ln {line + 1}, Col {col + 1}")

        if hasattr(self, 'selection_label') and self.selection_label:
            sel_text = editor.selectedText() if hasattr(editor, 'selectedText') else ""
            if sel_text:
                self.selection_label.setText(f"({len(sel_text)} characters selected)")
            else:
                self.selection_label.setText("")

        if hasattr(self, 'doc_stats_label') and self.doc_stats_label:
            text = editor.text() if hasattr(editor, 'text') else ""
            lines_cnt = editor.lines() if hasattr(editor, 'lines') else 0
            words_cnt = len(re.findall(r'\b\w+\b', text)) if text else 0
            chars_cnt = len(text)
            self.doc_stats_label.setText(f"Lines: {lines_cnt}, Words: {words_cnt}, Chars: {chars_cnt}")

        if hasattr(self, 'indent_label') and self.indent_label:
            tab_width = editor.tabWidth() if hasattr(editor, 'tabWidth') else 4
            self.indent_label.setText(f"Spaces: {tab_width}")

        if hasattr(self, 'encoding_label') and self.encoding_label:
            self.encoding_label.setText("UTF-8")

    def _on_editor_text_changed(self) -> None:
        if getattr(self, 'is_loading_file', False):
            return
        sender = self.sender()
        if not sender or not hasattr(sender, 'file_path'):
            sender, _ = self.get_current_editor()
        if sender:
            sender._dirty = True
            if hasattr(sender, "setModified"):
                sender.setModified(True)
            self._update_tab_title(sender)
            self._update_status_bar_metrics()

            # Debounce: har gal o'zgarganda taymerni stop qilib, 1500ms ga noldan boshlaymiz
            if hasattr(self, 'auto_save_timer') and self.auto_save_timer:
                self.auto_save_timer.stop()
                self.auto_save_timer.start(1500)

            if hasattr(sender, '_schedule_lint'):
                sender._schedule_lint()

    def cmd_save_file(self) -> None:
        """Manual Save triggered by Ctrl+S or Save action"""
        editor, _ = self.get_current_editor()
        self.save_file(editor=editor, is_auto_save=False)

    def save_file(self, editor=None, is_auto_save: bool = False) -> bool:
        """Save a specific editor or active editor to disk.
        If file_path is missing/Untitled and is_auto_save=False, prompt user with Save File dialog."""
        if editor is None:
            editor, _ = self.get_current_editor()
        if not editor or not hasattr(editor, "text"):
            return False

        file_path = getattr(editor, "file_path", None)

        # If file has no valid path or directory doesn't exist
        if not file_path or not os.path.isabs(file_path) or not os.path.exists(os.path.dirname(file_path)):
            if is_auto_save:
                return False
            start_dir = self.project_path or os.path.expanduser("~")
            chosen_path, _ = QFileDialog.getSaveFileName(
                self,
                "Faylni Saqlash (Save File)",
                start_dir,
                "Barcha Fayllar (*.*);;Python Fayllari (*.py);;JavaScript (*.js);;HTML (*.html)"
            )
            if chosen_path:
                file_path = os.path.normpath(chosen_path)
                editor.file_path = file_path
                apply_lexer_for_file(editor, file_path)
            else:
                return False

        try:
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(editor.text())
            editor._dirty = False
            if hasattr(editor, "setModified"):
                editor.setModified(False)
            self._update_tab_title(editor)
            self.current_file_path = file_path
            self.path_label.setText(file_path)
            if not is_auto_save:
                self.status_label.setText(f"Fayl saqlandi: {os.path.basename(file_path)}")
            if hasattr(self, "file_explorer") and self.file_explorer and self.project_path:
                self.file_explorer.set_root_path(self.project_path)
            return True
        except Exception as exc:
            if not is_auto_save:
                QMessageBox.critical(self, "Saqlashda Xatolik", f"Faylni saqlashda xatolik yuz berdi:\n{exc}")
            else:
                print(f"Auto-save xatolik ({file_path}): {exc}")
            return False

    def _handle_auto_save(self) -> None:
        if getattr(self, 'is_loading_file', False):
            return
        editors_to_save = []
        for tw in (getattr(self, 'tab_widget', None), getattr(self, 'right_tab_widget', None)):
            if not tw:
                continue
            for idx in range(tw.count()):
                w = tw.widget(idx)
                ed = self._extract_editor(w)
                if ed:
                    is_mod = getattr(ed, '_dirty', False) or (hasattr(ed, "isModified") and ed.isModified())
                    if is_mod:
                        fp = getattr(ed, "file_path", None)
                        if fp and os.path.isabs(fp) and os.path.exists(os.path.dirname(fp)):
                            editors_to_save.append(ed)

        saved_count = 0
        for ed in editors_to_save:
            if self.save_file(editor=ed, is_auto_save=True):
                saved_count += 1

        if saved_count > 0:
            self.status_label.setText(f"Avtomatik saqlandi ({saved_count} ta fayl)")

    # ----------------- Search/Replace Handlers -----------------
    def _on_find_shortcut(self):
        editor, path = self.get_current_editor()
        current = editor.text()[:editor.length()] if editor else ""
        sel_text = editor.selectedText() if editor else ""
        self.search_panel.show_find(sel_text or "")

    def _on_replace_shortcut(self):
        editor, path = self.get_current_editor()
        sel_text = editor.selectedText() if editor else ""
        self.search_panel.show_replace(sel_text or "", "")

    def _on_escape_pressed(self):
        if self.search_panel.isVisible():
            self.search_panel.hide_panel()
            editor, _ = self.get_current_editor()
            if editor:
                editor.setFocus()

    def _on_search_closed(self):
        editor, _ = self.get_current_editor()
        if editor:
            editor.setFocus()

    def _find_next(self, pattern: str, case_sensitive: bool = False):
        editor, _ = self.get_current_editor()
        if not editor:
            return
        # Use QsciScintilla findNext/findFirst
        try:
            found = False
            if not editor.findFirst(pattern, case_sensitive, True, True, False, False):
                # wrap and try again
                found = editor.findFirst(pattern, case_sensitive, True, False, False, False)
            else:
                found = True
            if not found:
                self.status_label.setText(f"Parcha topilmadi: {pattern}")
        except Exception:
            pass

    def _find_prev(self, pattern: str, case_sensitive: bool = False):
        editor, _ = self.get_current_editor()
        if not editor:
            return
        try:
            found = False
            if not editor.findFirst(pattern, case_sensitive, False, True, False, False):
                found = editor.findFirst(pattern, case_sensitive, False, False, False, False)
            else:
                found = True
            if not found:
                self.status_label.setText(f"Parcha topilmadi: {pattern}")
        except Exception:
            pass

    def _replace_current(self, find_text: str, replace_text: str) -> None:
        editor, _ = self.get_current_editor()
        if not editor:
            return
        try:
            # If current selection matches, replace it, else find next then replace
            sel = editor.selectedText()
            if sel and sel == find_text:
                editor.replaceSelectedText(replace_text)
                editor.setModified(True)
                self._update_tab_title(editor)
            else:
                self._find_next(find_text)
                sel2 = editor.selectedText()
                if sel2 and sel2 == find_text:
                    editor.replaceSelectedText(replace_text)
                    editor.setModified(True)
                    self._update_tab_title(editor)
        except Exception:
            pass

    def _replace_all(self, find_text: str, replace_text: str) -> None:
        editor, _ = self.get_current_editor()
        if not editor:
            return
        try:
            # naive replace all: iterate from top
            editor.beginUndoAction()
            editor.setCursorPosition(0, 0)
            count = 0
            while editor.findFirst(find_text, False, True, True, False, False):
                editor.replaceSelectedText(replace_text)
                count += 1
            editor.endUndoAction()
            editor.setModified(True)
            self._update_tab_title(editor)
            self.status_label.setText(f"{count} ta almashtirildi")
        except Exception as e:
            try:
                editor.endUndoAction()
            except Exception:
                pass
            self.status_label.setText(f"Replace All xatolik: {e}")

    def _show_tree_context_menu(self, position):
        index = self.file_tree.indexAt(position)

        if index.isValid():
            target_path = self.model.filePath(index)
            parent_dir = target_path if os.path.isdir(target_path) else os.path.dirname(target_path)
        else:
            target_path = self.project_path
            parent_dir = self.project_path

        if not parent_dir or not os.path.exists(parent_dir):
            return

        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #252526;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                padding: 4px;
                border-radius: 4px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 2px;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #04395e;
                color: #ffffff;
            }
            """
        )

        new_file_action = menu.addAction(IconManager.get_icon("file"), "Yangi Fayl (New File)")
        new_folder_action = menu.addAction(IconManager.get_icon("folder"), "Yangi Papka (New Folder)")

        rename_action = None
        delete_action = None

        if index.isValid():
            menu.addSeparator()
            rename_action = menu.addAction(IconManager.get_icon("edit"), "Qaytadan nomlash (Rename)")
            delete_action = menu.addAction(IconManager.get_icon("trash"), "O'chirish (Delete)")

        action = menu.exec(self.file_tree.viewport().mapToGlobal(position))

        if action == new_file_action:
            self._create_new_file(parent_dir)
        elif action == new_folder_action:
            self._create_new_folder(parent_dir)
        elif rename_action and action == rename_action:
            self._rename_item(target_path)
        elif delete_action and action == delete_action:
            self._delete_item(target_path)

    def _create_new_file(self, parent_dir: str):
        file_name, ok = QInputDialog.getText(
            self, "Yangi Fayl", "Yangi fayl nomini kiriting (masalan: script.js):"
        )
        if ok and file_name.strip():
            file_name = file_name.strip()
            new_file_path = os.path.join(parent_dir, file_name)
            if os.path.exists(new_file_path):
                QMessageBox.warning(self, "Xatolik", f"'{file_name}' nomli fayl allaqachon mavjud!")
                return
            try:
                with open(new_file_path, "w", encoding="utf-8") as f:
                    f.write("")
                self.model.setRootPath(self.project_path)
                self.open_file(new_file_path)
            except Exception as e:
                QMessageBox.critical(self, "Xatolik", f"Fayl yaratishda xatolik: {e}")

    def _create_new_folder(self, parent_dir: str):
        folder_name, ok = QInputDialog.getText(
            self, "Yangi Papka", "Yangi papka nomini kiriting:"
        )
        if ok and folder_name.strip():
            folder_name = folder_name.strip()
            new_folder_path = os.path.join(parent_dir, folder_name)
            if os.path.exists(new_folder_path):
                QMessageBox.warning(self, "Xatolik", f"'{folder_name}' nomli papka allaqachon mavjud!")
                return
            try:
                os.makedirs(new_folder_path, exist_ok=True)
                self.model.setRootPath(self.project_path)
            except Exception as e:
                QMessageBox.critical(self, "Xatolik", f"Papka yaratishda xatolik: {e}")

    def _rename_item(self, target_path: str):
        if not target_path or not os.path.exists(target_path):
            return

        old_name = os.path.basename(target_path)
        new_name, ok = QInputDialog.getText(
            self, "Qaytadan nomlash", "Yangi nomni kiriting:", text=old_name
        )
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            dir_name = os.path.dirname(target_path)
            new_path = os.path.join(dir_name, new_name)
            try:
                os.rename(target_path, new_path)
                editor, _ = self.get_current_editor()
                if editor and getattr(editor, "file_path", None) == target_path:
                    editor.file_path = new_path
                    self._update_tab_title(editor)
                    self.current_file_path = new_path
                    self.path_label.setText(new_path)
                self.model.setRootPath(self.project_path)
            except Exception as e:
                QMessageBox.critical(self, "Xatolik", f"Nomini o'zgartirishda xatolik: {e}")

    def _delete_item(self, target_path: str):
        if not target_path or not os.path.exists(target_path):
            return

        is_dir = os.path.isdir(target_path)
        item_type = "papkani" if is_dir else "faylni"
        name = os.path.basename(target_path)

        reply = QMessageBox.question(
            self,
            "O'chirishni tasdiqlang",
            f"Haqiqatan ham '{name}' {item_type} diskdan butunlay o'chirmoqchimisiz?\n\n(Bu amalni ortga qaytarib bo'lmaydi)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if is_dir:
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)
                    for idx in range(self.tab_widget.count()):
                        widget = self.tab_widget.widget(idx)
                        if isinstance(widget, ScodeScintillaEditor) and getattr(widget, "file_path", None) == target_path:
                            self._close_tab(idx)
                            break

                self.model.setRootPath(self.project_path)
            except Exception as e:
                QMessageBox.critical(self, "Xatolik", f"O'chirishda xatolik: {e}")

    def set_project_path(self, project_path: str, auto_install: bool = False) -> None:
        if not project_path:
            return

        from app.utils.config import ConfigManager
        from app.utils.cache_manager import get_cache_dir, CacheBackupWorker
        import shutil

        is_missing = not os.path.exists(project_path)
        is_empty = os.path.exists(project_path) and os.path.isdir(project_path) and len(os.listdir(project_path)) == 0

        # Agar original papka diskda topilmasa yoki bo'sh (0 ta fayl) bo'lsa -> Keshdan avtomatik tiklash
        if is_missing or is_empty:
            cfg = getattr(self.parent_window, 'config', None) or ConfigManager()
            project_id = cfg._get_project_id(project_path)
            cache_dir = os.path.join(get_cache_dir(), project_id)

            if os.path.exists(cache_dir) and os.listdir(cache_dir):
                try:
                    os.makedirs(project_path, exist_ok=True)
                    for item in os.listdir(cache_dir):
                        s = os.path.join(cache_dir, item)
                        d = os.path.join(project_path, item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)
                    if is_empty:
                        self.status_label.setText(f"⚠️ Papka bo'sh edi. AppData keshidan barcha fayllar avtomatik tiklandi: {project_path}")
                    else:
                        self.status_label.setText(f"Loyiha keshdan avtomatik tiklandi: {project_path}")
                except Exception:
                    project_path = cache_dir
                    self.status_label.setText("Loyiha AppData keshidan ochildi")
            else:
                self.status_label.setText("Loyiha papkasi topilmadi")
                if is_missing:
                    return
        else:
            # Original papka diskda bor va fayllar mavjud bo'lsa => Background QThread da keshni yangilash
            self.backup_worker = CacheBackupWorker(project_path)
            self.backup_worker.start()

        self.project_path = project_path
        self.current_file_path = None
        self.path_label.setText(project_path or "Loyiha tanlanmagan")

        if hasattr(self, "file_explorer") and self.file_explorer:
            self.file_explorer.set_root_path(project_path)

        self.model.setRootPath(project_path)
        root_index = self.model.index(project_path)
        self.file_tree.setRootIndex(root_index)
        self.file_tree.viewport().update()

        if hasattr(self, "terminal_panel") and self.terminal_panel:
            self.terminal_panel.set_project_path(project_path)

        # AppData/Local/ScodeEditor dan saqlangan tablarni tiklash
        if hasattr(self, "restore_session_state"):
            self.restore_session_state()

    def _on_tree_item_expanded(self, index: QModelIndex) -> None:
        """Papka yoyilganda ikonkalarni dinamik yangilash (folder-open.svg / folder-src-open.svg)"""
        if hasattr(self, 'icon_provider') and self.icon_provider:
            self.icon_provider.set_expanded(index, True)
        if hasattr(self, 'model') and hasattr(self.model, 'on_expanded'):
            self.model.on_expanded(index)

    def _on_tree_item_collapsed(self, index: QModelIndex) -> None:
        """Papka yopilganda ikonkalarni dinamik yangilash (folder.svg / folder-src.svg)"""
        if hasattr(self, 'icon_provider') and self.icon_provider:
            self.icon_provider.set_expanded(index, False)
        if hasattr(self, 'model') and hasattr(self.model, 'on_collapsed'):
            self.model.on_collapsed(index)

    def refresh_tree_icons(self) -> None:
        """Keshni tozalab, File Explorer ikonkalari ko'rinishini majburiy yangilaydi"""
        if hasattr(self, 'icon_provider') and self.icon_provider:
            self.icon_provider.clear_cache()
        if hasattr(self, 'model') and self.project_path:
            self.model.layoutChanged.emit()
        if hasattr(self, 'file_tree') and self.file_tree:
            self.file_tree.viewport().update()

        if auto_install:
            self._start_installation()

    def _start_installation(self) -> None:
        if not self.project_path:
            return

        self.status_label.setText("Kutubxonalar o'rnatilmoqda...")
        self.installer_thread = PackageInstallerThread(self.project_path)
        self.installer_thread.output_signal.connect(self._handle_install_output)
        self.installer_thread.finished_signal.connect(self._handle_install_finished)
        self.installer_thread.start()

    def _handle_install_output(self, text: str) -> None:
        self.status_label.setText(text)

    def _handle_install_finished(self, success: bool, message: str) -> None:
        self.status_label.setText(message)

    def _handle_back(self) -> None:
        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
            self._handle_auto_save()
        if hasattr(self, "save_session_state"):
            self.save_session_state()
        if self.on_back:
            self.on_back()

    def _handle_tree_click(self, index) -> None:
        file_path = self.model.filePath(index)
        if not file_path:
            return

        if os.path.isdir(file_path):
            if self.file_tree.isExpanded(index):
                self.file_tree.collapse(index)
            else:
                self.file_tree.expand(index)
            return

        if not os.path.isfile(file_path):
            return

        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            self.cmd_open_file_in_split(file_path)
        else:
            self.open_file(file_path)

    def _handle_tree_double_click(self, index) -> None:
        file_path = self.model.filePath(index)
        if not file_path or os.path.isdir(file_path):
            return

        if not os.path.isfile(file_path):
            return

        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            self.cmd_open_file_in_split(file_path)
        else:
            self.open_file(file_path)

    def _extract_editor(self, widget: QWidget):
        from app.ui.image_editor import ImageEditorWidget
        if isinstance(widget, EditorTabContainer):
            return widget.editor
        elif isinstance(widget, (ScodeScintillaEditor, ScodeTextEdit, ImageEditorWidget)):
            return widget
        elif hasattr(widget, 'file_path'):
            return widget
        return None

    def open_file(self, file_path: str, in_split: bool = False) -> None:
        if not file_path or not os.path.exists(file_path):
            return

        normalized_path = os.path.normpath(file_path)

        # 1. Agar in_split bo'lmasa, fayl allaqachon ochilganini tekshirish
        if not in_split:
            panes_to_check = []
            if hasattr(self, 'active_tab_widget') and self.active_tab_widget:
                panes_to_check.append(self.active_tab_widget)
            if hasattr(self, 'tab_widget') and self.tab_widget not in panes_to_check:
                panes_to_check.append(self.tab_widget)
            if hasattr(self, 'right_tab_widget') and self.right_tab_widget and self.right_tab_widget not in panes_to_check:
                panes_to_check.append(self.right_tab_widget)

            for tw in panes_to_check:
                if tw and tw.isVisible():
                    for idx in range(tw.count()):
                        w = tw.widget(idx)
                        ed = self._extract_editor(w)
                        if ed and os.path.normcase(os.path.normpath(getattr(ed, "file_path", ""))) == os.path.normcase(normalized_path):
                            tw.setCurrentIndex(idx)
                            self.active_tab_widget = tw
                            self.active_editor = ed
                            tw.show()
                            tw.setVisible(True)
                            tw.raise_()
                            try:
                                ed.setFocus()
                            except Exception:
                                pass
                            return
        else:
            # in_split=True holatida faqat right_tab_widget ichini tekshiramiz
            if hasattr(self, 'right_tab_widget') and self.right_tab_widget and self.right_tab_widget.isVisible():
                for idx in range(self.right_tab_widget.count()):
                    w = self.right_tab_widget.widget(idx)
                    ed = self._extract_editor(w)
                    if ed and os.path.normcase(os.path.normpath(getattr(ed, "file_path", ""))) == os.path.normcase(normalized_path):
                        self.right_tab_widget.setCurrentIndex(idx)
                        self.active_tab_widget = self.right_tab_widget
                        self.active_editor = ed
                        try:
                            ed.setFocus()
                        except Exception:
                            pass
                        return

        # 2. Yangi faylni ochish uchun faol pane'ni (kursor bor tomondagi oynani) aniqlash
        if in_split:
            self._ensure_split_widget()
            target_tabs = self.right_tab_widget
            self.active_tab_widget = self.right_tab_widget
        else:
            target_tabs = getattr(self, 'active_tab_widget', None) or self.tab_widget
            if hasattr(self, 'right_tab_widget') and target_tabs == self.right_tab_widget and not self.right_tab_widget.isVisible():
                target_tabs = self.tab_widget

        if target_tabs:
            target_tabs.show()
            target_tabs.setVisible(True)
            target_tabs.raise_()

        if in_split and hasattr(self, 'editor_splitter') and self.editor_splitter:
            sizes = self.editor_splitter.sizes()
            if len(sizes) >= 2 and (sizes[1] == 0 or sizes[0] == 0):
                total = sum(sizes) if sum(sizes) > 0 else 1000
                self.editor_splitter.setSizes([total // 2, total // 2])
            self.editor_splitter.refresh()
            self.editor_splitter.update()

        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
            self._handle_auto_save()

        # Check if file is image
        ext = os.path.splitext(normalized_path)[1].lower()
        if ext in ('.png', '.jpg', '.jpeg', '.svg', '.ico', '.bmp', '.webp', '.gif'):
            from app.ui.image_editor import ImageEditorWidget
            image_widget = ImageEditorWidget(file_path=normalized_path, parent=target_tabs)
            tab_index = target_tabs.addTab(image_widget, os.path.basename(normalized_path))
            target_tabs.setTabToolTip(tab_index, normalized_path)
            target_tabs.setCurrentIndex(tab_index)

            self.active_tab_widget = target_tabs
            self.active_editor = image_widget
            self.current_file_path = normalized_path
            self.path_label.setText(normalized_path)
            self.status_label.setText(f"Rasm ko'rish oynasida ochildi ({ext})")

            if hasattr(self, "save_session_state"):
                self.save_session_state()
            return

        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                content = handle.read()
        except Exception as exc:
            QMessageBox.critical(self, "Xatolik", f"Fayl o'qishda xatolik: {exc}")
            return

        cfg = self.parent_window.config if self.parent_window and hasattr(self.parent_window, "config") else ConfigManager()
        settings = cfg.get_settings()

        editor = ScodeScintillaEditor(parent=target_tabs)
        editor.file_path = normalized_path
        apply_lexer_for_file(editor, normalized_path)
        editor.apply_settings(
            font_family=settings.get("font_family", "Consolas"),
            font_size=settings.get("font_size", 11),
            tab_size=settings.get("tab_size", 4),
        )
        self._connect_editor_signals(editor)
        self.is_loading_file = True
        try:
            editor.setText(content)
        finally:
            self.is_loading_file = False
        if hasattr(editor, '_schedule_lint'):
            editor._schedule_lint()
        editor.setModified(False)

        container = EditorTabContainer(editor, show_minimap=settings.get("show_minimap", True), parent=target_tabs)
        tab_index = target_tabs.addTab(container, os.path.basename(normalized_path))
        target_tabs.setTabToolTip(tab_index, normalized_path)
        target_tabs.setCurrentIndex(tab_index)

        self.active_tab_widget = target_tabs
        self.active_editor = editor
        self.current_file_path = normalized_path
        self.path_label.setText(normalized_path)
        self.status_label.setText(f"Fayl ochildi ({os.path.splitext(normalized_path)[1]})")

        if hasattr(self, "breadcrumbs_bar") and self.breadcrumbs_bar:
            self.breadcrumbs_bar.set_file_path(normalized_path, self.project_path)
        if hasattr(self, "backup_manager") and self.backup_manager:
            self.backup_manager.track_file(normalized_path, editor)

        try:
            editor.setFocus()
            editor.activateWindow()
        except Exception:
            pass

        if hasattr(self, "save_session_state"):
            self.save_session_state()

    def get_current_editor(self):
        target_tabs = getattr(self, 'active_tab_widget', None) or self.tab_widget
        if not target_tabs or target_tabs.count() == 0:
            target_tabs = self.tab_widget
        widget = target_tabs.currentWidget() if target_tabs else None
        editor = self._extract_editor(widget)
        if editor:
            return editor, getattr(editor, "file_path", None)
        if target_tabs != self.tab_widget and self.tab_widget and self.tab_widget.count() > 0:
            widget = self.tab_widget.currentWidget()
            editor = self._extract_editor(widget)
            if editor:
                return editor, getattr(editor, "file_path", None)
        return None, None

    def _on_left_tab_changed(self, index: int) -> None:
        self.active_tab_widget = self.tab_widget
        self._on_tab_changed(index)

    def _on_right_tab_changed(self, index: int) -> None:
        if hasattr(self, 'right_tab_widget') and self.right_tab_widget:
            self.active_tab_widget = self.right_tab_widget
            widget = self.right_tab_widget.widget(index)
            editor = self._extract_editor(widget)
            if editor and isinstance(editor, ScodeScintillaEditor):
                self.active_editor = editor
                self.current_file_path = getattr(editor, "file_path", None)
                if self.current_file_path:
                    apply_lexer_for_file(editor, self.current_file_path)
                self.path_label.setText(self.current_file_path or self.project_path or "Loyiha tanlanmagan")
                self.status_label.setText(
                    f"{os.path.basename(self.current_file_path)} — Split Tab faollashtirildi"
                    if self.current_file_path
                    else "Yangi yozuv tab'ini oching"
                )
                try:
                    editor.setFocus()
                    editor.activateWindow()
                except Exception:
                    pass

    def _on_tab_changed(self, index: int) -> None:
        # Tab o'zgarganda avtomatik saqlashni bajarish
        self._handle_auto_save()

        target_tabs = getattr(self, 'active_tab_widget', None) or self.tab_widget
        widget = target_tabs.widget(index) if target_tabs else None
        editor = self._extract_editor(widget)

        if editor and isinstance(editor, ScodeScintillaEditor):
            self.active_editor = editor
            self.current_file_path = getattr(editor, "file_path", None)
            if self.current_file_path:
                apply_lexer_for_file(editor, self.current_file_path)
            self.path_label.setText(self.current_file_path or self.project_path or "Loyiha tanlanmagan")
            if hasattr(self, "breadcrumbs_bar") and self.breadcrumbs_bar:
                self.breadcrumbs_bar.set_file_path(self.current_file_path or "", self.project_path or "")
            self.status_label.setText(
                f"{os.path.basename(self.current_file_path)} — Tab faollashtirildi"
                if self.current_file_path
                else "Yangi yozuv tab'ini oching"
            )
            self._connect_editor_signals(editor)
            self._update_tab_title(editor)
            self._update_status_bar_metrics()
            try:
                editor.setFocus()
                editor.activateWindow()
            except Exception:
                pass
        else:
            self.active_editor = None
            self.current_file_path = None
            self.path_label.setText(self.project_path or "Loyiha tanlanmagan")

    def _close_tab(self, index: int) -> None:
        self._close_tab_in_widget(self.tab_widget, index)

    def _close_tab_in_widget(self, target_tabs: QTabWidget, index: int) -> None:
        widget = target_tabs.widget(index)
        editor = self._extract_editor(widget)
        if not editor or not isinstance(editor, ScodeScintillaEditor):
            target_tabs.removeTab(index)
            return

        file_path = getattr(editor, "file_path", None)
        if editor.isModified():
            reply = QMessageBox.question(
                self,
                "Saqlansinmi?",
                f"'{os.path.basename(file_path or 'Fayl')}' faylida saqlanmagan o'zgarishlar mavjud. Saqlab yopilsinmi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                if not self._save_editor(editor):
                    return

        self._disconnect_editor_signals(editor)
        target_tabs.removeTab(index)
        if target_tabs.count() == 0:
            if target_tabs == self.tab_widget:
                self.path_label.setText(self.project_path or "Loyiha tanlanmagan")
                self.status_label.setText("Tayyor")
            elif hasattr(self, 'right_tab_widget') and target_tabs == self.right_tab_widget:
                self.right_tab_widget.setVisible(False)
                self.active_tab_widget = self.tab_widget
        else:
            self._on_tab_changed(target_tabs.currentIndex())

        if hasattr(self, "save_session_state"):
            self.save_session_state()

    def _save_editor(self, editor: ScodeScintillaEditor) -> bool:
        file_path = getattr(editor, "file_path", None)
        if not file_path:
            QMessageBox.information(self, "Ma'lumot", "Saqlash uchun avval fayl tanlang.")
            return False
        try:
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(editor.text())
            editor.setModified(False)
            self.status_label.setText(f"{file_path} — (Saqlandi!)")
            self._update_tab_title(editor)
            return True
        except Exception as exc:
            QMessageBox.critical(self, "Xatolik", f"Faylni saqlashda xatolik: {exc}")
            return False

    def save_current_file(self) -> None:
        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()

        editor, file_path = self.get_current_editor()
        if not editor or not file_path:
            QMessageBox.information(self, "Ma'lumot", "Saqlash uchun avval fayl tanlang.")
            return

        self._save_editor(editor)

    def cmd_save_file(self) -> None:
        """Alias for save_current_file"""
        self.save_current_file()

    def cmd_run_active_file(self) -> None:
        """Alias for run_active_file"""
        self.run_active_file()

    def cmd_open_git(self) -> None:
        """Alias for open_git_dialog"""
        self.open_git_dialog()

    def cmd_open_settings(self) -> None:
        """Alias for open_settings_dialog"""
        self.open_settings_dialog()

    def _connect_editor_signals(self, editor: ScodeScintillaEditor):
        if not editor or not isinstance(editor, ScodeScintillaEditor):
            return
        try:
            editor.cursorPositionChanged.connect(lambda l, c, ed=editor: self._on_editor_focused(ed))
            editor.modificationChanged.connect(lambda mod, ed=editor: self._update_tab_title(ed))
        except Exception:
            pass

    def _disconnect_editor_signals(self, editor: ScodeScintillaEditor):
        if not editor or not isinstance(editor, ScodeScintillaEditor):
            return
        try:
            editor.cursorPositionChanged.disconnect()
            editor.modificationChanged.disconnect()
        except Exception:
            pass

    def _on_editor_focused(self, editor: ScodeScintillaEditor):
        if not editor:
            return
        self.active_editor = editor
        self.current_file_path = getattr(editor, "file_path", None)

        if hasattr(self, 'right_tab_widget') and self.right_tab_widget and self.right_tab_widget.isVisible():
            for i in range(self.right_tab_widget.count()):
                if self._extract_editor(self.right_tab_widget.widget(i)) == editor:
                    self.active_tab_widget = self.right_tab_widget
                    return
        if hasattr(self, 'tab_widget') and self.tab_widget:
            for i in range(self.tab_widget.count()):
                if self._extract_editor(self.tab_widget.widget(i)) == editor:
                    self.active_tab_widget = self.tab_widget
                    return

    def _update_tab_title(self, editor: ScodeScintillaEditor) -> None:
        file_path = getattr(editor, "file_path", None)
        title = os.path.basename(file_path) if file_path else "Untitled"
        if editor.isModified():
            title = f"{title}*"

        for idx in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(idx)
            ed = self._extract_editor(widget)
            if ed == editor:
                self.tab_widget.setTabText(idx, title)
                if file_path:
                    self.tab_widget.setTabToolTip(idx, file_path)
                break

    # ----------------- ▶ Run, Quick Open (Ctrl+P) & Settings (Ctrl+,) Handlers -----------------
    def run_active_file(self):
        """Aktiv faylni avto-saqlab, kengaytmasiga ko'ra alohida konsol yoki brauzerda ishga tushirish (▶ Run / Ctrl+F5)"""
        editor, file_path = self.get_current_editor()
        if not editor or not file_path:
            QMessageBox.information(self, "Ma'lumot", "Ishga tushirish uchun fayl tanlanmagan.")
            return

        self.save_current_file()

        ext = os.path.splitext(file_path)[1].lower()
        quoted_path = f'"{file_path}"'
        cwd = os.path.dirname(file_path) or self.project_path or os.getcwd()

        if hasattr(self, "terminal_panel") and self.terminal_panel:
            if ext == ".py":
                self.terminal_panel.execute_command(f"python {quoted_path}")
            elif ext in [".js", ".ts"]:
                self.terminal_panel.execute_command(f"node {quoted_path}")
            elif ext in [".html", ".htm"]:
                webbrowser.open(file_path)
            else:
                self.terminal_panel.execute_command(f"python {quoted_path}")
            return

        # Tashqi konsol oynasida ishga tushirish
        import subprocess
        try:
            if ext == ".py":
                self.status_label.setText(f"Python ishga tushirilmoqda: {file_path}")
                if os.name == 'nt':
                    subprocess.Popen(["cmd.exe", "/K", "python", file_path], cwd=cwd, creationflags=0x10)
                else:
                    subprocess.Popen(["python3", file_path], cwd=cwd)
            elif ext in [".js", ".ts"]:
                self.status_label.setText(f"Node.js ishga tushirilmoqda: {file_path}")
                if os.name == 'nt':
                    subprocess.Popen(["cmd.exe", "/K", "node", file_path], cwd=cwd, creationflags=0x10)
                else:
                    subprocess.Popen(["node", file_path], cwd=cwd)
            elif ext in [".html", ".htm"]:
                self.status_label.setText(f"Brauzerda ochilmoqda: {file_path}")
                webbrowser.open(file_path)
            else:
                self.status_label.setText(f"Ishga tushirilmoqda: {file_path}")
                if os.name == 'nt':
                    subprocess.Popen(["cmd.exe", "/K", "python", file_path], cwd=cwd, creationflags=0x10)
                else:
                    subprocess.Popen(["python3", file_path], cwd=cwd)
        except Exception as e:
            QMessageBox.critical(self, "Xatolik", f"Faylni ishga tushirishda xatolik: {e}")

    def open_external_terminal(self):
        """Loyiha papkasida operatsion tizimning alohida tashqi terminal oynasini ochish"""
        path = self.project_path if (self.project_path and os.path.exists(self.project_path)) else os.getcwd()
        try:
            if os.name == 'nt':
                # Windows: Yangi konsol oynasida PowerShell ochish
                CREATE_NEW_CONSOLE = 0x00000010
                subprocess.Popen(
                    ["powershell.exe", "-NoExit"],
                    creationflags=CREATE_NEW_CONSOLE,
                    cwd=path
                )
            elif sys.platform == 'darwin':
                # macOS: Terminal.app ilovasida papkani ochish
                subprocess.Popen(["open", "-a", "Terminal", path])
            else:
                # Linux: gnome-terminal yoki x-terminal-emulator
                try:
                    subprocess.Popen(["gnome-terminal", f"--working-directory={path}"])
                except FileNotFoundError:
                    try:
                        subprocess.Popen(["x-terminal-emulator"], cwd=path)
                    except FileNotFoundError:
                        subprocess.Popen(["xterm"], cwd=path)
            self.status_label.setText(f"Tashqi terminal ochildi: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Xatolik", f"Tashqi terminalni ochishda xatolik yuz berdi: {e}")

    def open_git_dialog(self):
        """Git boshqaruv modal oynasini (Source Control) ochish (Ctrl + Shift + G)"""
        from app.ui.git_panel import GitPanel

        dialog = QDialog(self)
        dialog.setWindowTitle("Scode Editor — Git Source Control")
        dialog.setMinimumSize(750, 520)

        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.setContentsMargins(0, 0, 0, 0)

        git_panel = GitPanel(dialog, project_path=self.project_path)
        dlg_layout.addWidget(git_panel)

        # Markazda joylashtirish
        geo = self.geometry()
        x = geo.x() + (geo.width() - dialog.width()) // 2
        y = geo.y() + (geo.height() - dialog.height()) // 2
        dialog.move(max(0, x), max(0, y))

        dialog.exec()

    def cmd_open_git(self):
        """Ctrl + Shift + G shortcut alias"""
        self.open_git_dialog()

    def open_quick_open_dialog(self):
        """Ctrl + P tezkor fayl qidiruv modalini ochish"""
        if not self.project_path:
            return
        dialog = QuickOpenDialog(self, self.project_path)
        # Markazda joylashtirish
        geo = self.geometry()
        x = geo.x() + (geo.width() - dialog.width()) // 2
        y = geo.y() + (geo.height() - dialog.height()) // 2
        dialog.move(x, y)

        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_file_path:
            self.open_file(dialog.selected_file_path)

    def open_settings_dialog(self):
        """Ctrl + , Sozlamalar modalini ochish"""
        cfg = self.parent_window.config if self.parent_window and hasattr(self.parent_window, "config") else ConfigManager()
        dialog = SettingsDialog(self, config=cfg)
        dialog.settings_saved.connect(self.apply_global_settings)
        dialog.exec()

    def cmd_open_settings(self):
        """Ctrl + , shortcut alias"""
        self.open_settings_dialog()

    def apply_global_settings(self, settings: dict = None):
        """Sozlamalarni barcha ochiq tab va vidjetlarga tatbiq etish"""
        if not settings:
            cfg = self.parent_window.config if self.parent_window and hasattr(self.parent_window, "config") else ConfigManager()
            settings = cfg.get_settings()

        interval_ms = settings.get("auto_save_interval", 2) * 1000
        self.auto_save_timer.setInterval(interval_ms)

        font_family = settings.get("font_family", "Consolas")
        font_size = settings.get("font_size", 11)
        tab_size = settings.get("tab_size", 4)
        show_minimap = settings.get("show_minimap", True)

        for idx in range(self.tab_widget.count()):
            container = self.tab_widget.widget(idx)
            if isinstance(container, EditorTabContainer):
                container.editor.apply_settings(font_family, font_size, tab_size)
                container.set_minimap_visible(show_minimap)
            elif isinstance(container, ScodeScintillaEditor):
                container.apply_settings(font_family, font_size, tab_size)

    def save_all_modified_files(self) -> None:
        """Dastur yopilayotganda barcha ochiq tablardagi saqlanmagan o'zgarishlarni diskka yozish"""
        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
        self._handle_auto_save()

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, 'top_hsplitter') and self.top_hsplitter:
            self.top_hsplitter.setSizes([240, max(600, self.width() - 240)])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_refresh_split_layout'):
            self._refresh_split_layout()
