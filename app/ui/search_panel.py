from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal


class SearchPanel(QWidget):
    """Compact find/replace panel for the editor.

    Methods on this panel call back into the EditorView via provided callbacks.
    """

    find_next_requested = pyqtSignal(str, bool)
    find_prev_requested = pyqtSignal(str, bool)
    replace_requested = pyqtSignal(str, str)
    replace_all_requested = pyqtSignal(str, str)
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("searchPanel")
        self.setVisible(False)

        self.setStyleSheet("""
            QWidget#searchPanel {
                background-color: #252526;
                border: 1px solid #007acc;
                border-radius: 4px;
                padding: 2px;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 3px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #094771;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find...")
        layout.addWidget(self.find_input)

        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedWidth(28)
        layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton(">")
        self.next_btn.setFixedWidth(28)
        layout.addWidget(self.next_btn)

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace...")
        self.replace_input.setVisible(False)
        layout.addWidget(self.replace_input)

        self.replace_btn = QPushButton("Replace")
        self.replace_btn.setVisible(False)
        layout.addWidget(self.replace_btn)

        self.replace_all_btn = QPushButton("Replace All")
        self.replace_all_btn.setVisible(False)
        layout.addWidget(self.replace_all_btn)

        self.close_btn = QPushButton("X")
        self.close_btn.setFixedWidth(28)
        layout.addWidget(self.close_btn)

        # Connections
        self.next_btn.clicked.connect(self._on_next)
        self.prev_btn.clicked.connect(self._on_prev)
        self.replace_btn.clicked.connect(self._on_replace)
        self.replace_all_btn.clicked.connect(self._on_replace_all)
        self.close_btn.clicked.connect(self._on_close)

        # Enter in find input => next
        self.find_input.returnPressed.connect(self._on_next)

    def show_find(self, text: str = ""):
        self.replace_input.setVisible(False)
        self.replace_btn.setVisible(False)
        self.replace_all_btn.setVisible(False)
        self.find_input.setText(text)
        self.setVisible(True)
        self.raise_()
        self.find_input.setFocus()
        self.find_input.selectAll()

    def show_replace(self, find_text: str = "", replace_text: str = ""):
        self.replace_input.setVisible(True)
        self.replace_btn.setVisible(True)
        self.replace_all_btn.setVisible(True)
        self.find_input.setText(find_text)
        self.replace_input.setText(replace_text)
        self.setVisible(True)
        self.raise_()
        self.find_input.setFocus()
        self.find_input.selectAll()

    def hide_panel(self):
        self.setVisible(False)
        self.closed.emit()

    def _on_next(self):
        pattern = self.find_input.text()
        if not pattern:
            return
        # case-insensitive by default
        self.find_next_requested.emit(pattern, False)

    def _on_prev(self):
        pattern = self.find_input.text()
        if not pattern:
            return
        self.find_prev_requested.emit(pattern, False)

    def _on_replace(self):
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        if not find_text:
            return
        self.replace_requested.emit(find_text, replace_text)

    def _on_replace_all(self):
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        if not find_text:
            return
        self.replace_all_requested.emit(find_text, replace_text)

    def _on_close(self):
        self.hide_panel()
