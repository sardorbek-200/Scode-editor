import os

from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QCursor, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

try:
    from PyQt6.QtWidgets import QFileSystemModel
except ImportError:
    from PyQt6.QtGui import QFileSystemModel

from app.utils.installer import PackageInstallerThread


class EditorView(QWidget):
    """Loyiha papkasi uchun fayl explorer va kod redaktori."""

    def __init__(self, parent=None, on_back=None):
        super().__init__(parent)
        self.parent_window = parent
        self.on_back = on_back
        self.project_path = None
        self.current_file_path = None
        self.installer_thread = None

        self._build_ui()

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
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QTreeView {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                color: #f5f5f5;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #f5f5f5;
                border: 1px solid #3c3c3c;
                font-family: Consolas, monospace;
                font-size: 11pt;
            }
            """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.back_button = QPushButton("← Loyihalar")
        self.back_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.back_button.clicked.connect(self._handle_back)
        top_bar.addWidget(self.back_button)

        self.path_label = QLabel("Loyiha tanlanmagan")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        top_bar.addWidget(self.path_label, 1)

        self.save_button = QPushButton("Saqlash (Ctrl+S)")
        self.save_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_button.clicked.connect(self.save_current_file)
        top_bar.addWidget(self.save_button)

        main_layout.addLayout(top_bar)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(2)

        self.file_tree = QTreeView()
        self.file_tree.setAnimated(True)
        self.file_tree.setIndentation(16)
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setUniformRowHeights(True)
        self.file_tree.doubleClicked.connect(self._handle_tree_double_click)
        self.splitter.addWidget(self.file_tree)

        self.editor = QTextEdit()
        self.editor.setAcceptRichText(False)
        self.editor.setPlaceholderText("Fayl tanlang va kodni tahrirlang...")
        self.splitter.addWidget(self.editor)

        main_layout.addWidget(self.splitter, 1)

        self.status_label = QLabel("Yuklanmoqda...")
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        main_layout.addWidget(self.status_label)

        shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self.save_current_file)

        self.model = QFileSystemModel()
        self.model.setReadOnly(False)
        self.model.setFilter(QDir.Filter.AllEntries)
        self.file_tree.setModel(self.model)
        self.file_tree.hideColumn(1)
        self.file_tree.hideColumn(2)
        self.file_tree.hideColumn(3)

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
        if success:
            self.status_label.setText(f"{message}")
        else:
            self.status_label.setText(f"{message}")

    def _handle_back(self) -> None:
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

        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                content = handle.read()
        except Exception as exc:
            QMessageBox.critical(self, "Xatolik", f"Fayl o'qishda xatolik: {exc}")
            return

        self.current_file_path = file_path
        self.editor.setPlainText(content)
        self.path_label.setText(file_path)
        self.status_label.setText("Fayl ochildi")

    def save_current_file(self) -> None:
        if not self.current_file_path:
            QMessageBox.information(self, "Ma'lumot", "Saqlash uchun avval fayl tanlang.")
            return

        try:
            with open(self.current_file_path, "w", encoding="utf-8") as handle:
                handle.write(self.editor.toPlainText())
        except Exception as exc:
            QMessageBox.critical(self, "Xatolik", f"Faylni saqlashda xatolik: {exc}")
            return

        self.status_label.setText(f"{self.current_file_path} — (Saqlandi!)")
        self.setWindowTitle("Scode Editor — (Saqlandi!)")
        self.path_label.setText(f"{self.current_file_path} — (Saqlandi!)")
