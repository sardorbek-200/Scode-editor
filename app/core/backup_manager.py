import os
import shutil
import time
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from app.utils.paths import get_app_data_dir


class AutoSaveBackupManager(QObject):
    """
    Auto-Save va AppData Backup menejeri.
    Fayllar tahrirlanganda yoki har 30 soniyada ularning xavfsiz zaxira nusxasini
    AppData/Roaming/ScodeEditor/backups/ papkasiga avtomatik saqlab boradi.
    """

    backup_saved = pyqtSignal(str, str)  # (original_path, backup_path)

    def __init__(self, interval_seconds: int = 30, parent=None):
        super().__init__(parent)
        self.interval_ms = interval_seconds * 1000
        self.backup_dir = os.path.join(get_app_data_dir(), "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

        self.timer = QTimer(self)
        self.timer.setInterval(self.interval_ms)
        self.timer.timeout.connect(self._perform_auto_backup)
        self.timer.start()

        self._tracked_files = {}  # filepath: editor_widget_ref

    def track_file(self, filepath: str, editor_widget):
        """Kuzatuv ostidagi faylni qo'shish"""
        if filepath and os.path.exists(filepath):
            norm_p = os.path.normpath(filepath)
            self._tracked_files[norm_p] = editor_widget

    def untrack_file(self, filepath: str):
        """Kuzatuvdan chiqarish"""
        if filepath:
            norm_p = os.path.normpath(filepath)
            self._tracked_files.pop(norm_p, None)

    def backup_now(self, filepath: str, content: str = None) -> str:
        """Berilgan fayldan zaxira nusxa (backup) olish"""
        if not filepath:
            return ""

        try:
            norm_p = os.path.normpath(filepath)
            safe_name = norm_p.replace(":", "_").replace("\\", "_").replace("/", "_")
            backup_file_path = os.path.join(self.backup_dir, safe_name)

            if content is not None:
                with open(backup_file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            elif os.path.exists(norm_p):
                shutil.copy2(norm_p, backup_file_path)

            self.backup_saved.emit(norm_p, backup_file_path)
            return backup_file_path
        except Exception:
            return ""

    def _perform_auto_backup(self):
        """Taymer bo'yicha fonda zaxiralash"""
        for filepath, editor in list(self._tracked_files.items()):
            try:
                if hasattr(editor, "text"):
                    text_content = editor.text()
                    self.backup_now(filepath, text_content)
                elif os.path.exists(filepath):
                    self.backup_now(filepath)
            except Exception:
                pass
