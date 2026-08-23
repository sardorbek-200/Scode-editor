import os
import time
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QGraphicsDropShadowEffect,
    QApplication,
)
from PyQt6.QtGui import QPixmap, QIcon, QColor

from app.utils.paths import get_app_icon_path


class SplashScreen(QWidget):
    """
    Dastur ishga tushganda eng kamida 1.2 soniya (1200ms) ekranda ko'rinadigan,
    silliq QProgressBar animatsiyasiga ega Splash Screen komponenti.
    """

    def __init__(self, parent=None, min_display_ms: int = 1200):
        super().__init__(parent)
        self.min_display_ms = min_display_ms
        self.start_time = time.time()

        # Oyna xususiyatlari: Ramkasiz (Frameless), Ustki oyna (SplashScreen/WindowStaysOnTop) va Shaffof fon
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.SplashScreen
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(520, 310)

        self._build_ui()

        # Silliq progress animatsiyasi
        self.anim = QPropertyAnimation(self.progress_bar, b"value")
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)

    def _build_ui(self):
        # Asosiy konteyner layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(15, 15, 15, 15)

        # Asosiy qorong'u kartochka vidjeti (Rounded Corners & Dark Theme)
        card = QWidget(self)
        card.setObjectName("splashCard")
        card.setStyleSheet("""
            QWidget#splashCard {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 14px;
            }
        """)

        # Soya effekti (Drop Shadow)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 35, 35, 25)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Markazdagi Logo va Sarlavha Layouti
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logotip (App Icon)
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(64, 64)

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(base_dir, "assets", "app_icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(base_dir, "assets", "icon.png")
        if not os.path.exists(icon_path):
            icon_path = get_app_icon_path()

        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(
                64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(pixmap)

        header_layout.addWidget(self.logo_label)

        # Sarlavha va Versiya
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        self.title_label = QLabel("Scode Editor")
        self.title_label.setStyleSheet("color: #ffffff; font-size: 26px; font-weight: bold; font-family: 'Segoe UI', sans-serif;")
        title_box.addWidget(self.title_label)

        self.version_label = QLabel("v1.0.0 — Modern & Fast Code Editor")
        self.version_label.setStyleSheet("color: #007acc; font-size: 12px; font-weight: 500; font-family: 'Segoe UI', sans-serif;")
        title_box.addWidget(self.version_label)

        header_layout.addLayout(title_box)
        card_layout.addLayout(header_layout)

        card_layout.addSpacing(35)

        # 2. Status Matni
        self.status_label = QLabel("Initsializatsiya qilinmoqda...")
        self.status_label.setStyleSheet("color: #888888; font-size: 11px; font-family: 'Segoe UI', sans-serif;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        card_layout.addWidget(self.status_label)

        card_layout.addSpacing(6)

        # 3. Minimalist Yuklanish Indikatori (QProgressBar)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(5)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2d2d2d;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 2px;
            }
        """)
        card_layout.addWidget(self.progress_bar)

        outer_layout.addWidget(card)

        # Ekranning aniq markazida chiqarish
        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.availableGeometry()
            x = (screen_geom.width() - self.width()) // 2
            y = (screen_geom.height() - self.height()) // 2
            self.move(x, y)

    def set_progress(self, target_value: int, message: str = ""):
        """Silliq progress bar animatsiyasi va holat matnini yangilash"""
        if message:
            self.status_label.setText(message)

        self.anim.stop()
        self.anim.setDuration(300)
        self.anim.setStartValue(self.progress_bar.value())
        self.anim.setEndValue(target_value)
        self.anim.start()

        QApplication.processEvents()

    def finish(self, main_window):
        """
        Eng kamida 1.2 soniya (1200ms) ko'ringandan so'ng va QProgressBar 100% bo'lgach
        Splash Screen'ni silliq yopish va main_window'ni namoyish qilish.
        """
        elapsed_ms = int((time.time() - self.start_time) * 1000)
        remaining_ms = max(0, self.min_display_ms - elapsed_ms)

        self.set_progress(100, "Tayyor!")

        if remaining_ms > 0:
            QTimer.singleShot(remaining_ms, lambda: self._do_finish(main_window))
        else:
            self._do_finish(main_window)

    def _do_finish(self, main_window):
        if main_window:
            main_window.show()
            main_window.raise_()
            main_window.activateWindow()
        self.close()
