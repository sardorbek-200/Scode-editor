import os
import shutil

from PyQt6.QtCore import Qt, QDir, QTimer, QSize
from PyQt6.QtGui import QCursor, QKeySequence, QShortcut, QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTreeView,
    QVBoxLayout,
    QWidget,
    QMenu,
    QInputDialog,
)

try:
    from PyQt6.QtWidgets import QFileSystemModel
except ImportError:
    from PyQt6.QtGui import QFileSystemModel

from app.utils.installer import PackageInstallerThread
from app.utils.icon_manager import IconManager
from app.ui.editor_scintilla import ScodeScintillaEditor
from app.ui.terminal_panel import TerminalPanel


class EditorView(QWidget):
    """
    QScintilla asosidagi kod redaktori, QTimer Auto Save, 
    SVG ikonkali File Explorer kontekst menyusi va Avto-skroll qiluvchi Terminal Paneli.
    """

    def __init__(self, parent=None, on_back=None):
        super().__init__(parent)
        self.parent_window = parent
        self.on_back = on_back
        self.project_path = None
        self.current_file_path = None
        self.installer_thread = None
        self.is_loading_file = False

        self._build_ui()
        self._setup_auto_save()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background-color: #1e1e1e;
                color: #f5f5f5;
            }
            QLabel {
                color: #d4d4d4;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QTreeView {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                color: #f5f5f5;
            }
            """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # 1. Yuqori Navigatsiya Paneli (SVG arrow-left ikonkasi bilan)
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.back_button = QPushButton(" Loyihalar")
        self.back_button.setIcon(IconManager.get_icon("arrow-left"))
        self.back_button.setIconSize(QSize(16, 16))
        self.back_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.back_button.clicked.connect(self._handle_back)
        top_bar.addWidget(self.back_button)

        self.path_label = QLabel("Loyiha tanlanmagan")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        top_bar.addWidget(self.path_label, 1)

        main_layout.addLayout(top_bar)

        # 2. Vertikal QSplitter (Yuqorida: Fayllar + Redaktor, Pastda: Terminal)
        self.main_vsplitter = QSplitter(Qt.Orientation.Vertical)
        self.main_vsplitter.setHandleWidth(4)

        # Yuqori Gorizontal Splitter (Fayllar Daraxti | QScintilla Redaktori)
        self.top_hsplitter = QSplitter(Qt.Orientation.Horizontal)
        self.top_hsplitter.setHandleWidth(4)

        # 2.1. Fayllar Daraxti (QTreeView)
        self.file_tree = QTreeView()
        self.file_tree.setAnimated(True)
        self.file_tree.setIndentation(16)
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setUniformRowHeights(True)
        self.file_tree.doubleClicked.connect(self._handle_tree_double_click)

        # Context Menu Sozlamasi
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self._show_tree_context_menu)

        self.top_hsplitter.addWidget(self.file_tree)

        # 2.2. QScintilla Kod Redaktori
        self.editor = ScodeScintillaEditor()
        self.top_hsplitter.addWidget(self.editor)

        self.top_hsplitter.setSizes([220, 780])
        self.main_vsplitter.addWidget(self.top_hsplitter)

        # 2.3. Ixcham Terminal Paneli (Pastda, moslashuvchan balandlik bilan)
        self.terminal_panel = TerminalPanel(parent=self, project_path=self.project_path)
        self.main_vsplitter.addWidget(self.terminal_panel)

        # Terminal paneli uchun yetarlicha balandlik nisbatini belgilash
        self.main_vsplitter.setSizes([450, 250])
        main_layout.addWidget(self.main_vsplitter, 1)

        # 3. Eng pastki Holat satri (Status Bar - Auto Save shu yerda ko'rinadi)
        self.status_label = QLabel("Tayyor")
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        main_layout.addWidget(self.status_label)

        # Hotkey Ctrl+S
        shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self.save_current_file)

        # File System Model
        self.model = QFileSystemModel()
        self.model.setReadOnly(False)
        self.model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)
        self.file_tree.setModel(self.model)
        self.file_tree.hideColumn(1)
        self.file_tree.hideColumn(2)
        self.file_tree.hideColumn(3)

    def _setup_auto_save(self):
        """1.5 soniyalik QTimer asosida Auto Save taymerini ulash"""
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.setInterval(1500)
        self.auto_save_timer.timeout.connect(self._handle_auto_save)

        # QScintilla matni o'zgarganda taymerni ishga tushirish
        self.editor.textChanged.connect(self._on_editor_text_changed)

    def _on_editor_text_changed(self):
        """Foydalanuvchi tugmalarni bosganda taymerni qayta boshlash"""
        if not self.is_loading_file and self.current_file_path:
            self.status_label.setText(f"{self.current_file_path} — (Tahrirlanmoqda...)")
            self.auto_save_timer.start()

    def _handle_auto_save(self):
        """1.5s dan so'ng faylni diskka avtomatik saqlash"""
        if self.current_file_path and os.path.exists(self.current_file_path):
            try:
                with open(self.current_file_path, "w", encoding="utf-8") as handle:
                    handle.write(self.editor.text())
                self.status_label.setText(f"{self.current_file_path} — (Auto-saved)")
            except Exception as exc:
                self.status_label.setText(f"Auto-save xatolik: {exc}")

    # -------------------------------------------------------------
    # FAYLLAR DARAXTI KONTEKST MENYUSI AMALLARI (File Explorer Context Menu with SVG Icons)
    # -------------------------------------------------------------
    def _show_tree_context_menu(self, position):
        """File Explorer sichqoncha o'ng tugmasi kontekst menyusi (SVG Ikonkalar bilan)"""
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
        menu.setStyleSheet("""
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
        """)

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
        """Yangi fayl yaratish"""
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
        """Yangi papka yaratish"""
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
        """Fayl yoki papka nomini o'zgartirish"""
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
                if self.current_file_path == target_path:
                    self.current_file_path = new_path
                    self.path_label.setText(new_path)
                self.model.setRootPath(self.project_path)
            except Exception as e:
                QMessageBox.critical(self, "Xatolik", f"Nomini o'zgartirishda xatolik: {e}")

    def _delete_item(self, target_path: str):
        """Fayl yoki papkani diskdan o'chirish"""
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
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if is_dir:
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)
                    if self.current_file_path == target_path:
                        self.current_file_path = None
                        self.editor.clear()
                        self.path_label.setText(self.project_path or "Loyiha tanlanmagan")

                self.model.setRootPath(self.project_path)
            except Exception as e:
                QMessageBox.critical(self, "Xatolik", f"O'chirishda xatolik: {e}")

    # -------------------------------------------------------------
    # REDAKTOR VA LOYIHA BOSHQARUVI
    # -------------------------------------------------------------
    def set_project_path(self, project_path: str, auto_install: bool = False) -> None:
        self.project_path = project_path
        self.current_file_path = None
        self.editor.clear()
        self.path_label.setText(project_path or "Loyiha tanlanmagan")
        self.status_label.setText("Loyiha ochildi. Fayl tanlang")

        if not project_path or not os.path.exists(project_path):
            return

        self.model.setRootPath(project_path)
        root_index = self.model.index(project_path)
        self.file_tree.setRootIndex(root_index)

        # Terminalga papkani sozlash
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

    def open_file(self, file_path: str) -> None:
        if not file_path or not os.path.exists(file_path):
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

        self.is_loading_file = True
        self.current_file_path = file_path

        self.editor.set_lexer_for_file(file_path)
        self.editor.setText(content)

        self.is_loading_file = False

        ext = os.path.splitext(file_path)[1]
        self.path_label.setText(file_path)
        self.status_label.setText(f"Fayl ochildi ({ext})")

    def save_current_file(self) -> None:
        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()

        if not self.current_file_path:
            QMessageBox.information(self, "Ma'lumot", "Saqlash uchun avval fayl tanlang.")
            return

        try:
            with open(self.current_file_path, "w", encoding="utf-8") as handle:
                handle.write(self.editor.text())
        except Exception as exc:
            QMessageBox.critical(self, "Xatolik", f"Faylni saqlashda xatolik: {exc}")
            return

        self.status_label.setText(f"{self.current_file_path} — (Saqlandi!)")
