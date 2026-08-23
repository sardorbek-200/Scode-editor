import os
import requests
import keyring
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QThread

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
        
        # 1. AppData/Local Config menejerini yuklash
        self.config = ConfigManager()
        current_theme = self.config.get_settings().get("theme", "Dark (One Dark Pro)")
        self.change_theme(current_theme)

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

        # Global Shortcuts on Top-Level Window (ApplicationShortcut context)
        from PyQt6.QtGui import QKeySequence, QShortcut
        from PyQt6.QtCore import Qt

        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_save.activated.connect(lambda: self.editor_view.cmd_save_file())

        self.shortcut_settings = QShortcut(QKeySequence("Ctrl+,"), self)
        self.shortcut_settings.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_settings.activated.connect(lambda: self.editor_view.open_settings_dialog())

        self.shortcut_git = QShortcut(QKeySequence("Ctrl+Shift+G"), self)
        self.shortcut_git.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_git.activated.connect(lambda: self.editor_view.open_git_dialog())

        # Dastur ochilganda avto-login tekshiruvi (Server ishlamayotgani sababli vaqtincha izohga olindi)
        # self.check_on_startup()
        self.show_projects()
        self.showMaximized()

    # def check_on_startup(self):
    #     username = keyring.get_password("scode_editor", "username")
    #     password = keyring.get_password("scode_editor", "password")
    #
    #     if username and password:
    #         try:
    #             url = "https://sstudio.uz/api/scode/login-check"
    #             res = requests.post(url, json={"username": username, "password": password}, timeout=5)
    #
    #             if res.status_code == 200 and res.json().get("has_active_subscription"):
    #                 self.show_projects()
    #                 return
    #         except Exception:
    #             pass  # Server bilan aloqa bo'lmasa login sahifasiga o'tadi
    #
    #     self.show_login()

    def show_login(self):
        self.stack.setCurrentIndex(0)

    def closeEvent(self, event):
        """Safely terminate all background QThreads, auto-save modified files, and save session state before exit."""
        if hasattr(self, 'editor_view') and self.editor_view:
            try:
                if hasattr(self.editor_view, 'save_all_modified_files'):
                    self.editor_view.save_all_modified_files()
                if hasattr(self.editor_view, 'save_session_state'):
                    self.editor_view.save_session_state()
            except Exception as e:
                print(f"CloseEvent save error: {e}")
        for thread in self.findChildren(QThread):
            if thread.isRunning():
                try:
                    thread.quit()
                    thread.wait(3000)  # wait up to 3 seconds
                except Exception:
                    pass
        event.accept()

    def show_projects(self):
        # Loyihalar sahifasini ochish va kartalarni qayta yuklash
        self.projects_view.load_recent_projects()
        self.stack.setCurrentIndex(1)

    def show_editor(self, project_path, auto_install=False):
        self.editor_view.set_project_path(project_path, auto_install=auto_install)
        self.stack.setCurrentIndex(2)

    def change_theme(self, theme_name: str):
        """Mavzuni darhol o'zgartirish va butun ilovaga va saqlashga tatbiq etish"""
        from app.utils.themes import get_stylesheet
        stylesheet = get_stylesheet(theme_name)
        self.setStyleSheet(stylesheet)

        settings = self.config.get_settings()
        settings["theme"] = theme_name
        self.config.save_settings(settings)