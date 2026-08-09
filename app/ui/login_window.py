import requests
import keyring
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt

class LoginView(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        title = QLabel("<h2>Scode Editor</h2><p>Tizimga kirish</p>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedWidth(280)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Parol")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedWidth(280)
        layout.addWidget(self.password_input)

        self.login_btn = QPushButton("Kirish")
        self.login_btn.setFixedWidth(280)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Xatolik", "Username va parolni kiriting!")
            return

        try:
            url = "https://sstudio.uz/api/scode/login-check"
            res = requests.post(url, json={"username": username, "password": password}, timeout=5)

            if res.status_code == 200:
                data = res.json()
                if data.get("has_active_subscription"):
                    # Keyring'ga xavfsiz saqlash
                    keyring.set_password("scode_editor", "username", username)
                    keyring.set_password("scode_editor", "password", password)

                    # Redaktor sahifasiga o'tkazish
                    self.on_login_success()
                else:
                    QMessageBox.warning(
                        self,
                        "Obuna cheklovi",
                        "Sizda faol obuna topilmadi!\nObuna narxi: 3 000 UZS/oy.\nTo'lov uchun adminga murojaat qiling."
                    )
            else:
                QMessageBox.warning(self, "Xatolik", "Username yoki parol noto'g'ri!")

        except Exception as e:
            QMessageBox.critical(self, "Xatolik", f"Serverga ulanib bo'lmadi: {e}")