import os
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QLabel,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QKeyEvent

from app.utils.icon_manager import IconManager


class QuickOpenDialog(QDialog):
    """
    VS Code uslubidagi Ctrl + P (Quick Open / Tezkor Fayl Qidiruv) pop-up modali.
    Loyiha ichidagi barcha fayllarni (.git, venv, __pycache__ siz) qidiradi va tezkor ochadi.
    """

    IGNORE_DIRS = {
        ".git",
        "venv",
        ".venv",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        ".idea",
        ".vscode",
    }

    def __init__(self, parent=None, project_path=None):
        super().__init__(parent)
        self.project_path = project_path or ""
        self.selected_file_path = None
        self.all_files = []  # list of (relative_path, full_path)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(620, 360)

        self._build_ui()
        self._scan_files()
        self.filter_files("")

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #252526;
                border: 1px solid #007acc;
                border-radius: 6px;
            }
            QLineEdit {
                background-color: #1c1c1c;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QListWidget {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #2d2d2d;
                border-radius: 4px;
                outline: none;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 6px 10px;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #37373d;
                color: #ffffff;
            }
            QLabel {
                color: #888888;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Qidiruv input box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Fayl nomini kiriting... (Ctrl + P / Esc - yopish)")
        self.search_input.textChanged.connect(self.filter_files)
        self.search_input.installEventFilter(self)
        layout.addWidget(self.search_input)

        # Fayllar ro'yxati (QListWidget)
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_accepted)
        layout.addWidget(self.list_widget, 1)

        # Pastki yordamchi izoh
        info_label = QLabel("↑/↓ — tanlash | Enter — ochish | Esc — bekor qilish")
        info_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(info_label)

    def _scan_files(self):
        """Loyihaning barcha fayllarini skanerlash"""
        self.all_files.clear()
        if not self.project_path or not os.path.exists(self.project_path):
            return

        for root, dirs, files in os.walk(self.project_path):
            # Ignore qilinadigan papkalarni o'tkazib yuborish
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]

            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.project_path)
                self.all_files.append((rel_path, full_path))

    def filter_files(self, text: str):
        """Kiritilgan matnga mos fayllarni saralash"""
        query = text.strip().lower()
        self.list_widget.clear()

        matched = []
        for rel_path, full_path in self.all_files:
            file_name = os.path.basename(rel_path).lower()
            rel_lower = rel_path.lower()

            if not query or query in file_name or query in rel_lower:
                matched.append((rel_path, full_path))

        for rel_path, full_path in matched[:100]:  # Cheklangan 100 ta natija
            item = QListWidgetItem(rel_path)
            item.setData(Qt.ItemDataRole.UserRole, full_path)
            item.setIcon(IconManager.get_icon("file"))
            self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._on_item_accepted(self.list_widget.currentItem())
            return
        elif event.key() == Qt.Key.Key_Down:
            curr = self.list_widget.currentRow()
            if curr < self.list_widget.count() - 1:
                self.list_widget.setCurrentRow(curr + 1)
            return
        elif event.key() == Qt.Key.Key_Up:
            curr = self.list_widget.currentRow()
            if curr > 0:
                self.list_widget.setCurrentRow(curr - 1)
            return
        super().keyPressEvent(event)

    def _on_item_accepted(self, item: QListWidgetItem):
        if item:
            self.selected_file_path = item.data(Qt.ItemDataRole.UserRole)
            self.accept()
