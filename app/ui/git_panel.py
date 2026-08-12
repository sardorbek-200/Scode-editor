"""
Scode Editor - Git Control Panel (Source Control Manager)
Subprocess va xavfsiz QThread yordamida Git status, init, add, commit, push, pull, tags, remote wizard va avto .gitignore boshqaruvi.
"""

import os
import subprocess
import html
import time
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QGroupBox,
    QMessageBox,
    QInputDialog,
    QSplitter,
    QDialog,
    QFormLayout,
)
from PyQt6.QtGui import QCursor, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from app.utils.icon_manager import IconManager


class GitSetupDialog(QDialog):
    """
    Dastlabki Git sozlash modali (First-time Git Setup Wizard).
    GitHub URL va Branch nomini kiritish uchun modal oyna.
    """

    def __init__(self, parent=None, current_remote="", current_branch="main"):
        super().__init__(parent)
        self.setWindowTitle("Git Dastlabki Sozlash — Setup Wizard")
        self.setFixedSize(500, 240)

        self.remote_url = ""
        self.branch_name = "main"

        self.setStyleSheet("""
            QDialog {
                background-color: #252526;
                color: #ffffff;
                font-family: "Segoe UI", sans-serif;
            }
            QLabel {
                color: #cccccc;
                font-size: 12px;
            }
            QLabel#titleLabel {
                color: #569cd6;
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #1c1c1c;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 7px 18px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton#cancelBtn {
                background-color: #3c3c3c;
            }
            QPushButton#cancelBtn:hover {
                background-color: #4a4a4a;
            }
        """)

        self._build_ui(current_remote, current_branch)

    def _build_ui(self, current_remote, current_branch):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QLabel("Git Remote & Branch Sozlamalari Wizard")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.remote_input = QLineEdit()
        self.remote_input.setPlaceholderText("https://github.com/user/repository.git")
        self.remote_input.setText(current_remote)
        form_layout.addRow("GitHub Remote URL:", self.remote_input)

        self.branch_input = QLineEdit()
        self.branch_input.setPlaceholderText("main")
        self.branch_input.setText(current_branch or "main")
        form_layout.addRow("Asosiy Branch nomi:", self.branch_input)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Bekor qilish")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Saqlash va Sozlash")
        save_btn.clicked.connect(self._handle_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _handle_save(self):
        remote = self.remote_input.text().strip()
        branch = self.branch_input.text().strip() or "main"

        if not remote:
            QMessageBox.warning(self, "Ogohlantirish", "Iltimos, GitHub Remote URL manzilini kiriting!")
            return

        self.remote_url = remote
        self.branch_name = branch
        self.accept()


class GitCommandThread(QThread):
    """
    Xavfsiz va bloklanmaydigan Git buyruq bajarish tridi.
    `terminate()` ishlatilmaydi, `proc.kill()` yordamida toza to'xtatiladi.
    """
    output_line = pyqtSignal(str, bool)
    finished = pyqtSignal(int)

    def __init__(self, args: list, cwd: str):
        super().__init__()
        self.args = args
        self.cwd = cwd
        self.proc = None
        self._is_stop_requested = False

    def stop(self):
        """Trid va uning subprotsessini xavfsiz to'xtatish"""
        self._is_stop_requested = True
        if self.proc:
            try:
                self.proc.kill()
            except Exception:
                pass

    def run(self) -> None:
        creationflags = 0x08000000 if os.name == "nt" else 0

        # Git terminalda parol so'rab qotib qolmasligi uchun
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_ASKPASS"] = "echo"

        try:
            self.proc = subprocess.Popen(
                ["git"] + self.args,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags,
                env=env,
            )

            stdout, stderr = self.proc.communicate(timeout=30)

            if stdout:
                for line in stdout.splitlines():
                    if self._is_stop_requested:
                        break
                    self.output_line.emit(line, False)

            if stderr:
                for line in stderr.splitlines():
                    if self._is_stop_requested:
                        break
                    self.output_line.emit(line, True)

            self.finished.emit(self.proc.returncode if self.proc else 1)

        except subprocess.TimeoutExpired:
            if self.proc:
                self.proc.kill()
            self.output_line.emit("Xatolik: Git buyrug'i vaqti tugadi (Timeout: 30s). Serverga ulanishni tekshiring!", True)
            self.finished.emit(1)
        except Exception as exc:
            self.output_line.emit(f"Xatolik: {exc}", True)
            self.finished.emit(1)


class GitPanel(QWidget):
    """
    Scode Editor uchun to'liq va mukammal Git manbasi boshqaruv paneli.
    """

    def __init__(self, parent=None, project_path=None):
        super().__init__(parent)
        self.project_path = project_path or os.getcwd()
        self._active_thread = None

        self._build_ui()
        if self.project_path and os.path.exists(self.project_path):
            self.refresh_git_status()

    def set_project_path(self, path: str):
        """Aktiv loyiha papkasini o'zgartirish va holatni yangilash"""
        if path and os.path.exists(path):
            self.project_path = os.path.abspath(path)
            self.path_label.setText(f"[{self.project_path}]")
            self.refresh_git_status()

    def closeEvent(self, event):
        """Panel yopilganda tridni xavfsiz to'xtatish (Crash bo'lmaydi)"""
        self._stop_active_thread()
        super().closeEvent(event)

    def _stop_active_thread(self):
        """Trid va uning subprocess'ini xotirani buzmasdan to'xtatish"""
        if self._active_thread and self._active_thread.isRunning():
            self._active_thread.stop()
            self._active_thread.quit()
            self._active_thread.wait(1000)
            self._active_thread = None

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #cccccc;
                font-family: "Segoe UI", sans-serif;
            }
            QGroupBox {
                border: 1px solid #2d2d2d;
                border-radius: 4px;
                margin-top: 6px;
                font-size: 11px;
                font-weight: bold;
                color: #569cd6;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            QListWidget {
                background-color: #181818;
                border: 1px solid #2d2d2d;
                border-radius: 4px;
                color: #cccccc;
                font-family: "Cascadia Code", Consolas, monospace;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 4px 6px;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
            QListWidget::item:selected {
                background-color: #04395e;
                color: #ffffff;
            }
            QLineEdit {
                background-color: #252526;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #094771;
            }
            QPushButton#secondaryBtn {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #3c3c3c;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #37373d;
                color: #ffffff;
            }
            QTextEdit#gitLog {
                background-color: #141414;
                color: #cccccc;
                border: 1px solid #2d2d2d;
                font-family: "Cascadia Code", Consolas, monospace;
                font-size: 10pt;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # 1. Top Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        title_label = QLabel("GIT SOURCE CONTROL")
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #ffffff;")
        header_layout.addWidget(title_label)

        self.branch_label = QLabel("Branch: main")
        self.branch_label.setStyleSheet("color: #4ec9b0; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(self.branch_label)

        self.path_label = QLabel(f"[{self.project_path}]")
        self.path_label.setStyleSheet("color: #777777; font-size: 10px;")
        header_layout.addWidget(self.path_label, 1)

        setup_btn = QPushButton(" Git Sozlash (Remote Wizard)")
        setup_btn.setObjectName("secondaryBtn")
        setup_btn.setToolTip("GitHub Repository URL va Branch nomini sozlash")
        setup_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        setup_btn.clicked.connect(self.run_first_time_setup_dialog)
        header_layout.addWidget(setup_btn)

        refresh_btn = QPushButton(" Yangilash")
        refresh_btn.setIcon(IconManager.get_icon("clear"))
        refresh_btn.setObjectName("secondaryBtn")
        refresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        refresh_btn.clicked.connect(self.refresh_git_status)
        header_layout.addWidget(refresh_btn)

        gitignore_btn = QPushButton(" Auto .gitignore")
        gitignore_btn.setObjectName("secondaryBtn")
        gitignore_btn.setToolTip("Loyiha turiga ko'ra mos .gitignore faylini yaratish")
        gitignore_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        gitignore_btn.clicked.connect(self.create_smart_gitignore)
        header_layout.addWidget(gitignore_btn)

        main_layout.addLayout(header_layout)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        # 2. O'zgargan fayllar ro'yxati
        status_group = QGroupBox(" O'ZGARGANI FAYLLAR (CHANGES)")
        status_vbox = QVBoxLayout(status_group)
        status_vbox.setContentsMargins(6, 6, 6, 6)

        self.file_list = QListWidget()
        status_vbox.addWidget(self.file_list, 1)

        stage_btn_layout = QHBoxLayout()

        self.init_btn = QPushButton(" Git Init (Repozitoriy Yaratish)")
        self.init_btn.setObjectName("secondaryBtn")
        self.init_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.init_btn.clicked.connect(self.git_init_repo)
        stage_btn_layout.addWidget(self.init_btn)

        stage_btn_layout.addStretch()

        self.stage_all_btn = QPushButton(" Barchasini Sahnalashtirish (Git Add .)")
        self.stage_all_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.stage_all_btn.clicked.connect(self.git_add_all)
        stage_btn_layout.addWidget(self.stage_all_btn)

        status_vbox.addLayout(stage_btn_layout)
        top_layout.addWidget(status_group, 1)

        # 3. Commit Section
        commit_group = QGroupBox(" COMMIT BO'LIMI")
        commit_vbox = QVBoxLayout(commit_group)
        commit_vbox.setContentsMargins(6, 6, 6, 6)

        commit_input_layout = QHBoxLayout()
        self.commit_msg_input = QLineEdit()
        self.commit_msg_input.setPlaceholderText("Commit xabarini kiriting (masalan: feat: add new feature)...")
        self.commit_msg_input.returnPressed.connect(self.git_commit)
        commit_input_layout.addWidget(self.commit_msg_input, 1)

        commit_btn = QPushButton(" Commit qilish")
        commit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        commit_btn.clicked.connect(self.git_commit)
        commit_input_layout.addWidget(commit_btn)

        commit_vbox.addLayout(commit_input_layout)
        top_layout.addWidget(commit_group)

        # 4. Push, Pull & Tag Boshqaruvi
        sync_group = QGroupBox(" SERVER VA TAGLAR (SYNC & TAGS)")
        sync_vbox = QVBoxLayout(sync_group)
        sync_vbox.setContentsMargins(6, 6, 6, 6)

        sync_btn_layout = QHBoxLayout()

        pull_btn = QPushButton(" ⬇ Git Pull")
        pull_btn.setObjectName("secondaryBtn")
        pull_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        pull_btn.clicked.connect(self.git_pull)
        sync_btn_layout.addWidget(pull_btn)

        push_btn = QPushButton(" ⬆ Git Push")
        push_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        push_btn.clicked.connect(self.git_push)
        sync_btn_layout.addWidget(push_btn)

        sync_btn_layout.addSpacing(16)

        tag_create_btn = QPushButton(" Tag Yaratish")
        tag_create_btn.setObjectName("secondaryBtn")
        tag_create_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        tag_create_btn.clicked.connect(self.git_create_tag)
        sync_btn_layout.addWidget(tag_create_btn)

        push_tags_btn = QPushButton(" Push Tags")
        push_tags_btn.setObjectName("secondaryBtn")
        push_tags_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        push_tags_btn.clicked.connect(self.git_push_tags)
        sync_btn_layout.addWidget(push_tags_btn)

        sync_vbox.addLayout(sync_btn_layout)
        top_layout.addWidget(sync_group)

        splitter.addWidget(top_container)

        # 5. Git konsol chiqishi
        self.log_area = QTextEdit()
        self.log_area.setObjectName("gitLog")
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("Git amallari va natijalari shu yerda ko'rinadi...")
        splitter.addWidget(self.log_area)

        splitter.setSizes([320, 120])
        main_layout.addWidget(splitter, 1)

    def _log(self, text: str, is_error: bool = False):
        color = "#f48771" if is_error else "#23d160"
        formatted = f"<span style='color: {color};'><b>></b> {html.escape(text)}</span><br>"
        self.log_area.append(formatted)

    def run_git_command(self, args: list, callback=None):
        """Git buyrug'ini xavfsiz ishga tushirish"""
        if not self.project_path or not os.path.isdir(self.project_path):
            self._log("Loyiha papkasi mavjud emas!", is_error=True)
            return

        # Oldingi tridni xavfsiz to'xtatamiz
        self._stop_active_thread()

        cmd_str = " ".join(args)
        self._log(f"Bajarilmoqda: git {cmd_str}")

        self._last_stdout = ""
        self._last_stderr = ""

        self._active_thread = GitCommandThread(args, self.project_path)

        def _on_output(txt, err):
            if not err:
                self._last_stdout += txt + "\n"
            else:
                self._last_stderr += txt + "\n"
            self._log(txt, is_error=err)

        self._active_thread.output_line.connect(_on_output)

        def _on_finish(rc: int):
            if callback:
                callback(self._last_stdout, self._last_stderr, rc)

        self._active_thread.finished.connect(_on_finish)
        self._active_thread.start()

    def check_git_initialized(self) -> bool:
        """Loyiha papkasida .git mavjudligini tekshirish"""
        if not self.project_path:
            return False
        git_dir = os.path.join(self.project_path, ".git")
        return os.path.exists(git_dir) and os.path.isdir(git_dir)

    def git_init_repo(self):
        """git init buyrug'ini bajarish"""
        def _after_init(stdout, stderr, code):
            if code == 0:
                self._log("Git repozitoriyasi muvaffaqiyatli ishga tushirildi (git init)!")
                self.refresh_git_status()
                self.run_first_time_setup_dialog()
            else:
                self._log("Git init bajarishda xatolik!", is_error=True)

        self.run_git_command(["init"], _after_init)

    def run_first_time_setup_dialog(self):
        """Git Wizard dialogini ochish"""
        current_remote = ""
        current_branch = "main"

        try:
            cp_remote = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=3
            )
            if cp_remote.returncode == 0:
                current_remote = cp_remote.stdout.strip()

            cp_branch = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=3
            )
            if cp_branch.returncode == 0 and cp_branch.stdout.strip():
                current_branch = cp_branch.stdout.strip()
        except Exception:
            pass

        dialog = GitSetupDialog(self, current_remote=current_remote, current_branch=current_branch)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            remote_url = dialog.remote_url
            branch_name = dialog.branch_name

            if not self.check_git_initialized():
                self.run_git_command(["init"])

            self.run_git_command(["branch", "-M", branch_name])

            def _set_remote():
                if current_remote:
                    self.run_git_command(["remote", "set-url", "origin", remote_url], lambda a, b, c: self.refresh_git_status())
                else:
                    self.run_git_command(["remote", "add", "origin", remote_url], lambda a, b, c: self.refresh_git_status())

            _set_remote()
            self._log(f"Git Remote muvaffaqiyatli sozlandi: origin -> {remote_url} ({branch_name})")

    def refresh_git_status(self):
        """Fayllar holatini va branch nomini yangilash"""
        self.file_list.clear()

        if not self.check_git_initialized():
            item = QListWidgetItem(" Git repozitoriyasi topilmadi (.git yo'q). 'Git Init' tugmasini bosing.")
            item.setForeground(QColor("#f44747"))
            self.file_list.addItem(item)
            self.branch_label.setText("Branch: (Yo'q)")
            return

        def _on_branch(stdout, stderr, code):
            branch = stdout.strip() or "main / master"
            self.branch_label.setText(f"Branch: {branch}")

        self.run_git_command(["branch", "--show-current"], _on_branch)

        def _on_status(stdout, stderr, code):
            if code != 0:
                self.file_list.addItem(" Git status olishda xatolik yuz berdi")
                return

            lines = stdout.splitlines()
            if not lines:
                item = QListWidgetItem(" Repozitoriy toza (O'zgarishlar yo'q)")
                item.setForeground(QColor("#4ec9b0"))
                self.file_list.addItem(item)
                return

            for line in lines:
                if len(line) >= 3:
                    status_code = line[:2]
                    file_path = line[3:]
                    item = QListWidgetItem(f"[{status_code.strip()}]  {file_path}")

                    if 'M' in status_code:
                        item.setForeground(QColor("#e5c07b"))
                    elif 'A' in status_code:
                        item.setForeground(QColor("#23d160"))
                    elif '?' in status_code:
                        item.setForeground(QColor("#569cd6"))
                    elif 'D' in status_code:
                        item.setForeground(QColor("#f44747"))

                    self.file_list.addItem(item)

        self.run_git_command(["status", "--porcelain"], _on_status)

    def git_add_all(self):
        """git add ."""
        if not self.check_git_initialized():
            QMessageBox.warning(self, "Ogohlantirish", "Avval 'Git Init' tugmasi orqali repozitoriy yarating!")
            return

        def _after_add(stdout, stderr, code):
            if code == 0:
                self._log("Barcha fayllar muvaffaqiyatli sahnalashtirildi (git add .)")
                self.refresh_git_status()
            else:
                self._log("Fayllarni sahnalashtirishda xatolik!", is_error=True)

        self.run_git_command(["add", "."], _after_add)

    def git_commit(self):
        """git commit -m"""
        if not self.check_git_initialized():
            QMessageBox.warning(self, "Ogohlantirish", "Avval 'Git Init' tugmasi orqali repozitoriy yarating!")
            return

        msg = self.commit_msg_input.text().strip()
        if not msg:
            QMessageBox.warning(self, "Ogohlantirish", "Iltimos, commit xabarini kiriting!")
            return

        def _after_commit(stdout, stderr, code):
            if code == 0:
                self._log(f"Commit muvaffaqiyatli bajarildi: '{msg}'")
                self.commit_msg_input.clear()
                self.refresh_git_status()
            else:
                self._log("Commit bajarishda xatolik! Avval git add qiling.", is_error=True)

        self.run_git_command(["commit", "-m", msg], _after_commit)

    def git_push(self):
        """git push"""
        if not self.check_git_initialized():
            QMessageBox.warning(self, "Ogohlantirish", "Avval Git repozitoriyasini va Remote URL ni sozlang!")
            return

        def _after_push(stdout, stderr, code):
            if code == 0:
                self._log("Serverga push muvaffaqiyatli yakunlandi!")
            else:
                self._log("Push qilishda xatolik yuz berdi! SSH kalit yoki Credential Manager sozlamalarini tekshiring.", is_error=True)
            self.refresh_git_status()

        self.run_git_command(["push", "-u", "origin", "HEAD"], _after_push)

    def git_pull(self):
        """git pull"""
        if not self.check_git_initialized():
            QMessageBox.warning(self, "Ogohlantirish", "Avval Git repozitoriyasini va Remote URL ni sozlang!")
            return

        def _after_pull(stdout, stderr, code):
            if code == 0:
                self._log("Serverdan yangiliklar tortib olindi (pull)!")
            else:
                self._log("Pull qilishda xatolik yuz berdi!", is_error=True)
            self.refresh_git_status()

        self.run_git_command(["pull"], _after_pull)

    def git_create_tag(self):
        """git tag -a"""
        if not self.check_git_initialized():
            return

        tag_name, ok = QInputDialog.getText(self, "Yangi Git Tag", "Tag nomini kiriting (masalan: v1.0.0):")
        if not ok or not tag_name.strip():
            return

        tag_name = tag_name.strip()
        msg, ok_msg = QInputDialog.getText(self, "Tag Izohi", f"'{tag_name}' uchun izoh kiriting:")
        comment = msg.strip() if ok_msg and msg.strip() else f"Release {tag_name}"

        def _after_tag(stdout, stderr, code):
            if code == 0:
                self._log(f"Tag muvaffaqiyatli yaratildi: {tag_name}")
            else:
                self._log("Tag yaratishda xatolik!", is_error=True)

        self.run_git_command(["tag", "-a", tag_name, "-m", comment], _after_tag)

    def git_push_tags(self):
        """git push origin --tags"""
        if not self.check_git_initialized():
            return

        def _after_push_tags(stdout, stderr, code):
            if code == 0:
                self._log("Barcha taglar serverga muvaffaqiyatli push qilindi!")
            else:
                self._log("Taglarni push qilishda xatolik!", is_error=True)

        self.run_git_command(["push", "origin", "--tags"], _after_push_tags)

    def create_smart_gitignore(self):
        """.gitignore yaratish"""
        if not self.project_path or not os.path.exists(self.project_path):
            return

        gitignore_path = os.path.join(self.project_path, ".gitignore")

        gitignore_content = """# ==========================================
# Scode Editor - Avtomatik Yaratilgan .gitignore
# ==========================================

# Dependency / Node modules
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# Python & Environment
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
*.egg-info/

# IDE & Editor files
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# Environment variables & Local logs
.env
.env.local
*.log
scratch/
"""

        try:
            if os.path.exists(gitignore_path):
                reply = QMessageBox.question(
                    self,
                    ".gitignore Mavjud",
                    ".gitignore fayli allaqachon mavjud! Uni yangilamoqchimisiz?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write(gitignore_content)

            self._log(".gitignore fayli muvaffaqiyatli yaratildi va saqlandi!")
            self.refresh_git_status()
        except Exception as e:
            self._log(f".gitignore yaratishda xatolik: {e}", is_error=True)