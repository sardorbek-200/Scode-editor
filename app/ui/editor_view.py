import os
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
)
from PyQt6.QtCore import Qt, QDir, QTimer, QSize, QUrl
from PyQt6.QtGui import QCursor, QKeySequence, QShortcut, QColor, QFont, QDesktopServices

def apply_lexer_for_file(editor, filepath: str):
    """
    Fayl kengaytmasiga ko'ra QsciLexer obyektini biriktirish va GC dan saqlash uchun editor.current_lexer ga biriktirish
    """
    if not editor or not filepath:
        return

    ext = os.path.splitext(filepath)[1].lower()
    font = QFont("Consolas", 11)

    lexer = None
    if ext in ['.html', '.htm', '.xml']:
        lexer = QsciLexerHTML(editor)
    elif ext == '.py':
        lexer = QsciLexerPython(editor)
    elif ext in ['.js', '.jsx', '.ts', '.tsx', '.json']:
        lexer = QsciLexerJavaScript(editor)
    elif ext in ['.css', '.scss', '.less']:
        lexer = QsciLexerCSS(editor)
    elif ext in ['.cpp', '.c', '.h', '.hpp', '.cs']:
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

        # Lexer Garbage Collector tomonidan o'chirilmasligi uchun editor.current_lexer ga bog'laymiz
        editor.current_lexer = lexer
        editor.set_lexer_for_file(filepath)
    else:
        editor.current_lexer = None
        editor.setLexer(None)

    if hasattr(editor, "_enforce_dark_margins"):
        editor._enforce_dark_margins()
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
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
from app.ui.terminal_panel import TerminalPanel
from app.ui.search_panel import SearchPanel
from app.ui.quick_open import QuickOpenDialog
from app.ui.settings_dialog import SettingsDialog


class EditorTabContainer(QWidget):
    """Redaktor va o'ng tomondagi Mini-map vidjetini o'z ichiga oluvchi tab konteyneri"""

    def __init__(self, editor: ScodeScintillaEditor, show_minimap: bool = True):
        super().__init__()
        self.editor = editor
        self.minimap = QsciScintilla()
        self._build_ui(show_minimap)

    def _build_ui(self, show_minimap: bool):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.editor, 1)

        # Mini-map sozlamalari
        self.minimap.setFixedWidth(110)
        self.minimap.setMarginWidth(0, 0)
        self.minimap.setMarginWidth(1, 0)
        self.minimap.setMarginWidth(2, 0)
        self.minimap.setReadOnly(True)
        self.minimap.setPaper(QColor("#181818"))
        self.minimap.setColor(QColor("#777777"))
        self.minimap.setFont(QFont("Consolas", 3))
        self.minimap.setCaretLineVisible(False)
        self.minimap.setWrapMode(QsciScintilla.WrapMode.WrapNone)

        # Sinxronizatsiya: Matn va Scrollbar
        self.minimap.setText(self.editor.text())
        self.editor.textChanged.connect(lambda: self.minimap.setText(self.editor.text()))
        self.editor.verticalScrollBar().valueChanged.connect(self.minimap.verticalScrollBar().setValue)
        self.minimap.verticalScrollBar().valueChanged.connect(self.editor.verticalScrollBar().setValue)

        self.minimap.setVisible(show_minimap)
        layout.addWidget(self.minimap)

    def set_minimap_visible(self, visible: bool):
        self.minimap.setVisible(visible)


class EditorView(QWidget):
    """
    QScintilla asosidagi kod redaktori, endi ko'p faylli tab rejimi bilan.
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

        # Tashqi terminal tugmasi
        self.ext_terminal_button = QPushButton(" Tashqi terminal")
        self.ext_terminal_button.setIcon(IconManager.get_icon("terminal"))
        self.ext_terminal_button.setIconSize(QSize(14, 14))
        self.ext_terminal_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.ext_terminal_button.setToolTip("Loyiha papkasini operatsion tizimning alohida terminalida ochish")
        self.ext_terminal_button.clicked.connect(self.open_external_terminal)
        top_bar.addWidget(self.ext_terminal_button)

        # Sozlamalar Tugmasi (Ctrl + ,)
        self.settings_button = QPushButton(" Sozlamalar")
        self.settings_button.setIcon(IconManager.get_icon("settings"))
        self.settings_button.setIconSize(QSize(14, 14))
        self.settings_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.settings_button.setToolTip("Sozlamalar (Ctrl + ,)")
        self.settings_button.clicked.connect(self.open_settings_dialog)
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

        self.top_hsplitter = QSplitter(Qt.Orientation.Horizontal)
        self.top_hsplitter.setHandleWidth(2)

        self.file_tree = QTreeView()
        self.file_tree.setAnimated(True)
        self.file_tree.setIndentation(12)
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setUniformRowHeights(True)
        self.file_tree.doubleClicked.connect(self._handle_tree_double_click)
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self._show_tree_context_menu)
        self.top_hsplitter.addWidget(self.file_tree)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.top_hsplitter.addWidget(self.tab_widget)

        self.top_hsplitter.setSizes([220, 780])
        main_layout.addWidget(self.top_hsplitter, 1)

        # Status Bar
        status_bar_widget = QWidget()
        status_bar_widget.setStyleSheet("""
            QWidget {
                background-color: #007acc;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 11px;
            }
        """)
        status_layout = QHBoxLayout(status_bar_widget)
        status_layout.setContentsMargins(10, 2, 10, 2)
        self.status_label = QLabel("Tayyor")
        status_layout.addWidget(self.status_label)
        main_layout.addWidget(status_bar_widget)

        shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self.save_current_file)

        # ▶ Run Shortcuts (Ctrl + F5 va F5)
        self.run_shortcut = QShortcut(QKeySequence("Ctrl+F5"), self)
        self.run_shortcut.activated.connect(self.run_active_file)
        self.f5_shortcut = QShortcut(QKeySequence("F5"), self)
        self.f5_shortcut.activated.connect(self.run_active_file)

        # Ctrl + P Quick Open
        self.quick_open_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        self.quick_open_shortcut.activated.connect(self.open_quick_open_dialog)

        # Ctrl + , Settings
        self.settings_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        self.settings_shortcut.activated.connect(self.open_settings_dialog)

        # Find / Replace shortcuts
        self.find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.find_shortcut.activated.connect(self._on_find_shortcut)

        self.replace_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        self.replace_shortcut.activated.connect(self._on_replace_shortcut)

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
        self.escape_shortcut.activated.connect(self._on_escape_pressed)

    def _connect_editor_signals(self, editor: ScodeScintillaEditor) -> None:
        try:
            editor.textChanged.connect(self._on_editor_text_changed)
        except Exception:
            pass

    def _disconnect_editor_signals(self, editor: ScodeScintillaEditor) -> None:
        try:
            editor.textChanged.disconnect(self._on_editor_text_changed)
        except Exception:
            pass

    def _on_editor_text_changed(self) -> None:
        editor, file_path = self.get_current_editor()
        if editor and not self.is_loading_file and file_path:
            self.status_label.setText(f"{file_path} — (Tahrirlanmoqda...)")
            self.auto_save_timer.start()
            self._update_tab_title(editor)

    def _handle_auto_save(self) -> None:
        editor, file_path = self.get_current_editor()
        if editor and file_path and os.path.exists(file_path):
            try:
                with open(file_path, "w", encoding="utf-8") as handle:
                    handle.write(editor.text())
                editor.setModified(False)
                self.status_label.setText(f"{file_path} — (Auto-saved)")
                self._update_tab_title(editor)
            except Exception as exc:
                self.status_label.setText(f"Auto-save xatolik: {exc}")

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
                editor.replaceSelected(replace_text)
                editor.setModified(True)
                self._update_tab_title(editor)
            else:
                self._find_next(find_text)
                sel2 = editor.selectedText()
                if sel2 and sel2 == find_text:
                    editor.replaceSelected(replace_text)
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
                editor.replaceSelected(replace_text)
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
        self.project_path = project_path
        self.current_file_path = None
        self.path_label.setText(project_path or "Loyiha tanlanmagan")
        self.status_label.setText("Loyiha ochildi. Fayl tanlang")

        if not project_path or not os.path.exists(project_path):
            return

        self.model.setRootPath(project_path)
        root_index = self.model.index(project_path)
        self.file_tree.setRootIndex(root_index)

        if hasattr(self, "terminal_panel") and self.terminal_panel:
            self.terminal_panel.set_project_path(project_path)

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
        if self.on_back:
            self.on_back()

    def _handle_tree_double_click(self, index) -> None:
        file_path = self.model.filePath(index)
        if not file_path or not os.path.isfile(file_path):
            return

        self.open_file(file_path)

    def _extract_editor(self, widget: QWidget):
        if isinstance(widget, EditorTabContainer):
            return widget.editor
        elif isinstance(widget, ScodeScintillaEditor):
            return widget
        return None

    def open_file(self, file_path: str) -> None:
        if not file_path or not os.path.exists(file_path):
            return

        normalized_path = os.path.normpath(file_path)
        for idx in range(self.tab_widget.count()):
            w = self.tab_widget.widget(idx)
            ed = self._extract_editor(w)
            if ed and os.path.normcase(os.path.normpath(getattr(ed, "file_path", ""))) == os.path.normcase(normalized_path):
                self.tab_widget.setCurrentIndex(idx)
                return

        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
            self._handle_auto_save()

        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                content = handle.read()
        except Exception as exc:
            QMessageBox.critical(self, "Xatolik", f"Fayl o'qishda xatolik: {exc}")
            return

        # Config sozlamalarini yuklash
        cfg = self.parent_window.config if self.parent_window and hasattr(self.parent_window, "config") else ConfigManager()
        settings = cfg.get_settings()

        editor = ScodeScintillaEditor()
        editor.file_path = normalized_path
        apply_lexer_for_file(editor, normalized_path)
        editor.apply_settings(
            font_family=settings.get("font_family", "Consolas"),
            font_size=settings.get("font_size", 11),
            tab_size=settings.get("tab_size", 4),
        )
        self._connect_editor_signals(editor)
        editor.setText(content)
        editor.setModified(False)

        container = EditorTabContainer(editor, show_minimap=settings.get("show_minimap", True))
        tab_index = self.tab_widget.addTab(container, os.path.basename(normalized_path))
        self.tab_widget.setTabToolTip(tab_index, normalized_path)
        self.tab_widget.setCurrentIndex(tab_index)

        self.current_file_path = normalized_path
        self.path_label.setText(normalized_path)
        self.status_label.setText(f"Fayl ochildi ({os.path.splitext(normalized_path)[1]})")

    def get_current_editor(self):
        widget = self.tab_widget.currentWidget()
        editor = self._extract_editor(widget)
        if editor:
            return editor, getattr(editor, "file_path", None)
        return None, None

    def _on_tab_changed(self, index: int) -> None:
        widget = self.tab_widget.widget(index)
        editor = self._extract_editor(widget)

        previous_editor = self.active_editor
        if previous_editor is not None and previous_editor != editor:
            self._disconnect_editor_signals(previous_editor)

        if editor and isinstance(editor, ScodeScintillaEditor):
            self.active_editor = editor
            self.current_file_path = getattr(editor, "file_path", None)
            if self.current_file_path:
                apply_lexer_for_file(editor, self.current_file_path)
            self.path_label.setText(self.current_file_path or self.project_path or "Loyiha tanlanmagan")
            self.status_label.setText(
                f"{os.path.basename(self.current_file_path)} — Tab faollashtirildi"
                if self.current_file_path
                else "Yangi yozuv tab'ini oching"
            )
            self._connect_editor_signals(editor)
            self._update_tab_title(editor)
        else:
            self.active_editor = None
            self.current_file_path = None
            self.path_label.setText(self.project_path or "Loyiha tanlanmagan")

    def _close_tab(self, index: int) -> None:
        widget = self.tab_widget.widget(index)
        editor = self._extract_editor(widget)
        if not editor or not isinstance(editor, ScodeScintillaEditor):
            self.tab_widget.removeTab(index)
            return

        file_path = getattr(editor, "file_path", None)
        if editor.isModified():
            reply = QMessageBox.question(
                self,
                "Saqlansinmi?",
                f"'{os.path.basename(file_path)}' faylida saqlanmagan o'zgarishlar mavjud. Saqlab yopilsinmi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                if not self._save_editor(editor):
                    return

        self._disconnect_editor_signals(editor)
        self.tab_widget.removeTab(index)
        if self.tab_widget.count() == 0:
            self.path_label.setText(self.project_path or "Loyiha tanlanmagan")
            self.status_label.setText("Tayyor")
        else:
            self._on_tab_changed(self.tab_widget.currentIndex())

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
