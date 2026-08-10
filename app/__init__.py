import os
import requests
import keyring
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from PyQt6.QtGui import QIcon

from app.ui.login_window import LoginView
from app.ui.projects_view import ProjectsView
from app.ui.editor_view import EditorView
from app.ui.styles import get_app_stylesheet
from app.utils.config import ConfigManager
from app.utils.paths import get_app_icon_path


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scode Editor")
        self.setGeometry(100, 100, 1000, 650)
        self.setStyleSheet(get_app_stylesheet())

        # 1. AppData/Local Config menejerini yuklash
        self.config = ConfigManager()

        # Window Ikonkasini AppData/Local dan yuklash
        icon_path = get_app_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 2. Sahifalar Staki (QStackedWidget)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Index 0: Login Sahifasi
        self.login_view = LoginView(on_login_success=self.show_projects)
        self.stack.addWidget(self.login_view)

        # Index 1: Loyihalar Sahifasi (ProjectsView)
        self.projects_view = ProjectsView(
            config=self.config, 
            on_project_selected=self.show_editor
        )
        self.stack.addWidget(self.projects_view)

        # Index 2: Redaktor Sahifasi
        self.editor_view = EditorView(parent=self, on_back=self.show_projects)
        self.stack.addWidget(self.editor_view)

        # Dastur ochilganda avto-login tekshiruvi
        self.check_on_startup()

    def check_on_startup(self):
        username = keyring.get_password("scode_editor", "username")
        password = keyring.get_password("scode_editor", "password")

        if username and password:
            try:
                url = "https://sstudio.uz/api/scode/login-check"
                res = requests.post(url, json={"username": username, "password": password}, timeout=5)

                if res.status_code == 200 and res.json().get("has_active_subscription"):
                    self.show_projects()
                    return
            except Exception:
                pass  # Server bilan aloqa bo'lmasa login sahifasiga o'tadi

        self.show_login()

    def show_login(self):
        self.stack.setCurrentIndex(0)

    def show_projects(self):
        # Loyihalar sahifasini ochish va kartalarni qayta yuklash
        self.projects_view.load_recent_projects()
        self.stack.setCurrentIndex(1)

    def show_editor(self, project_path, auto_install=False):
        self.editor_view.set_project_path(project_path, auto_install=auto_install)
        self.stack.setCurrentIndex(2)