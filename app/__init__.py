import os
import requests
import keyring
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QLabel, QVBoxLayout, QWidget, QMessageBox
from PyQt6.QtGui import QIcon

from app.ui.login_window import LoginView

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scode Editor")
        self.setGeometry(100, 100, 1000, 600)

        # Ikonkani o'rnatish
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Yagona oyna ichida sahifalarni almashtirish (QStackedWidget)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # 1. Login Sahifasi
        self.login_view = LoginView(on_login_success=self.show_editor)
        self.stack.addWidget(self.login_view)

        # 2. Redaktor Sahifasi
        self.editor_view = QWidget()
        editor_layout = QVBoxLayout()
        editor_layout.addWidget(QLabel("<h1>Scode Editor — Kod Tahrirlovchi</h1>"))
        self.editor_view.setLayout(editor_layout)
        self.stack.addWidget(self.editor_view)

        # Faqat dastur ochilganda 1 marta tekshirish
        self.check_on_startup()

    def check_on_startup(self):
        username = keyring.get_password("scode_editor", "username")
        password = keyring.get_password("scode_editor", "password")

        if username and password:
            try:
                url = "https://sstudio.uz/api/scode/login-check"
                res = requests.post(url, json={"username": username, "password": password}, timeout=5)

                if res.status_code == 200 and res.json().get("has_active_subscription"):
                    self.show_editor()
                    return
            except Exception:
                pass  # Serverga ulanib bo'lmasa yoki xato bo'lsa login sahifasi ochiladi

        self.show_login()

    def show_editor(self):
        self.stack.setCurrentIndex(1)  # Redaktor sahifasi

    def show_login(self):
        self.stack.setCurrentIndex(0)  # Login sahifasi