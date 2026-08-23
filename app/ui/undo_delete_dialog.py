import os
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
)


class UndoDeleteDialog(QDialog):
    """
    5-soniyali bekor qilish (Undo / Cancel) tugmasi bilan ishlaydigan loyihani o'chirish tasdiqlash dialogi.
    """

    COUNTDOWN_SECONDS = 5

    def __init__(self, project_name: str, project_path: str, parent=None):
        super().__init__(parent)
        self.project_name = project_name
        self.project_path = project_path
        self.remaining_seconds = self.COUNTDOWN_SECONDS

        self.setWindowTitle("Loyihani O'chirish — Scode Editor")
        self.setFixedSize(480, 240)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self._build_ui()
        self._start_timer()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #252526;
                border: 2px solid #e74c3c;
                border-radius: 8px;
            }
            QLabel#titleLabel {
                color: #e74c3c;
                font-size: 16px;
                font-weight: bold;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            QLabel#infoLabel {
                color: #cccccc;
                font-size: 13px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            QLabel#countdownLabel {
                color: #f1c40f;
                font-size: 14px;
                font-weight: bold;
            }
            QProgressBar {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                text-align: center;
                height: 14px;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 3px;
            }
            QPushButton#cancelBtn {
                background-color: #27ae60;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#cancelBtn:hover {
                background-color: #2ecc71;
            }
            QPushButton#confirmBtn {
                background-color: #c0392b;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 10px 16px;
                font-size: 12px;
            }
            QPushButton#confirmBtn:hover {
                background-color: #e74c3c;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Sarlavha
        title = QLabel("⚠️ Loyihani O'chirishni Tasdiqlash", objectName="titleLabel")
        layout.addWidget(title)

        # Izoh matni
        info_text = (
            f"<b>Loyiha:</b> {self.project_name}<br>"
            f"<span style='color: #888888;'>Yo'l: {self.project_path}</span><br><br>"
            "AppData ichidagi loyihaga tegishli kesh va konfiguratsiyalar tozalansinmi?<br>"
            "<i>(Asl manba papkasiga mutlaqo teginilmaydi).</i>"
        )
        self.info_label = QLabel(info_text, objectName="infoLabel")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # 5-soniyalik progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.COUNTDOWN_SECONDS * 10)
        self.progress_bar.setValue(self.COUNTDOWN_SECONDS * 10)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Taymer matni
        self.countdown_label = QLabel(f"O'chirilishiga {self.remaining_seconds} soniya qoldi...", objectName="countdownLabel")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.countdown_label)

        # Tugmalar paneli
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.cancel_button = QPushButton("🛡 Bekor Qilish (Cancel)", objectName="cancelBtn")
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.cancel_button, 2)

        self.confirm_now_button = QPushButton("Hozir O'chirish", objectName="confirmBtn")
        self.confirm_now_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_now_button.clicked.connect(self.accept)
        btn_layout.addWidget(self.confirm_now_button, 1)

        layout.addLayout(btn_layout)

    def _start_timer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(100)  # Har 100ms da yangilash
        self.timer.timeout.connect(self._on_timer_tick)
        self.timer.start()

    def _on_timer_tick(self):
        val = self.progress_bar.value() - 1
        self.progress_bar.setValue(max(0, val))

        sec = (val + 9) // 10
        if sec != self.remaining_seconds:
            self.remaining_seconds = sec
            self.countdown_label.setText(f"O'chirilishiga {max(0, self.remaining_seconds)} soniya qoldi...")

        if val <= 0:
            self.timer.stop()
            self.accept()

    def _on_cancel(self):
        if hasattr(self, 'timer'):
            self.timer.stop()
        self.reject()
