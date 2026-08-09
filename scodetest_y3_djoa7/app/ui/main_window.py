from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Scode PyQt6 Starter")
        self.resize(960, 640)
        self.setMinimumSize(760, 520)
        self._apply_styles()
        self._build_ui()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background-color: #0f172a;
                color: #f8fafc;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QLabel#titleLabel {
                font-size: 28px;
                font-weight: 700;
            }
            QLabel#subtitleLabel {
                font-size: 14px;
                color: #94a3b8;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                background-color: #2563eb;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton#secondaryButton {
                background-color: #334155;
            }
            QPushButton#secondaryButton:hover {
                background-color: #475569;
            }
            """
        )

    def _build_ui(self) -> None:
        container = QWidget(self)
        container.setObjectName("mainContainer")
        self.setCentralWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)

        title = QLabel("Welcome to your new desktop app")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)

        subtitle = QLabel("This starter uses a clean structure with separate UI, core, and utility layers.")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        button_row = QHBoxLayout()
        button_row.setSpacing(12)

        primary_button = QPushButton("Continue")
        primary_button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_row.addWidget(primary_button)

        secondary_button = QPushButton("Open settings")
        secondary_button.setObjectName("secondaryButton")
        secondary_button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_row.addWidget(secondary_button)

        button_row.addStretch()
        layout.addLayout(button_row)

        layout.addStretch()
        self.statusBar().showMessage("Ready")
