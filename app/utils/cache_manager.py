import os
import shutil
import json
from PyQt6.QtCore import QThread, pyqtSignal, QStorageInfo
from PyQt6.QtWidgets import QMessageBox

from app.utils.paths import get_app_data_dir, get_projects_dir, get_icons_dir
from app.utils.config import ConfigManager


def get_cache_dir() -> str:
    """AppData/Local/ScodeEditor/cache papkasi yo'li"""
    path = os.path.join(get_app_data_dir(), "cache")
    os.makedirs(path, exist_ok=True)
    return path


class DiskSpaceChecker:
    """Disk bo'sh hajmini tekshiruvchi yordamchi klass (10 GB sharti)"""

    MIN_REQUIRED_BYTES = 10 * 1024 * 1024 * 1024  # 10 GB

    @classmethod
    def check_free_space(cls, target_path: str = None) -> tuple[bool, float]:
        """
        Target papka joylashgan diskdagi bo'sh joyni tekshirish.
        Returns: (has_enough_space: bool, free_gb: float)
        """
        if not target_path:
            target_path = get_app_data_dir()

        try:
            total, used, free = shutil.disk_usage(target_path)
            free_gb = free / (1024 ** 3)
            return free >= cls.MIN_REQUIRED_BYTES, free_gb
        except Exception:
            # QStorageInfo orqali zaxira tekshirish
            storage = QStorageInfo(target_path)
            free = storage.bytesAvailable()
            free_gb = free / (1024 ** 3)
            return free >= cls.MIN_REQUIRED_BYTES, free_gb


class CacheBackupWorker(QThread):
    """
    Loyiha papkasi (.git, .vscode, node_modules va barcha fayllar) ni
    AppData/Local/ScodeEditor/cache/<project_id>/ papkasiga asinxron nusxalash oqimi.
    """

    progress_signal = pyqtSignal(int, str)  # (foiz, holat matni)
    finished_signal = pyqtSignal(bool, str)  # (muvaffaqiyat, xabar)

    def __init__(self, project_path: str, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.config_mgr = ConfigManager()

    def run(self):
        if not self.project_path or not os.path.exists(self.project_path):
            self.finished_signal.emit(False, "Original loyiha papkasi mavjud emas!")
            return

        # 1. 10 GB Disk bo'sh joyini tekshirish
        has_space, free_gb = DiskSpaceChecker.check_free_space(get_app_data_dir())
        if not has_space:
            self.finished_signal.emit(
                False,
                f"⚠️ Diskda yetarli joy yo'q! Kesh zaxirasi uchun kamida 10 GB bo'sh joy kerak.\n(Hozirgi bo'sh joy: {free_gb:.2f} GB)"
            )
            return

        project_id = self.config_mgr._get_project_id(self.project_path)
        dest_cache_dir = os.path.join(get_cache_dir(), project_id)

        try:
            self.progress_signal.emit(10, "Kesh papkasi tayyorlanmoqda...")
            os.makedirs(dest_cache_dir, exist_ok=True)

            # Loyihadagi barcha fayl va papkalarni nusxalash
            all_entries = []
            for root, dirs, files in os.walk(self.project_path):
                for f in files:
                    all_entries.append(os.path.join(root, f))

            total_files = max(1, len(all_entries))
            copied_count = 0

            for root, dirs, files in os.walk(self.project_path):
                rel_root = os.path.relpath(root, self.project_path)
                target_root = os.path.join(dest_cache_dir, rel_root) if rel_root != "." else dest_cache_dir
                os.makedirs(target_root, exist_ok=True)

                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(target_root, file)
                    try:
                        shutil.copy2(src_file, dst_file)
                    except Exception:
                        pass

                    copied_count += 1
                    percent = int((copied_count / total_files) * 80) + 10
                    self.progress_signal.emit(percent, f"Nusxalanmoqda: {file}")

            # Loyiha metadatalarini JSON va ikonkaga saqlash
            self.progress_signal.emit(95, "Metadata saqlanmoqda...")
            self.config_mgr.save_project_data(self.project_path, {
                "has_cache": True,
                "cache_path": dest_cache_dir
            })

            self.progress_signal.emit(100, "Kesh zaxirasi muvaffaqiyatli yaratildi!")
            self.finished_signal.emit(True, f"Loyiha AppData keshiga muvaffaqiyatli nusxalandi! ({free_gb:.2f} GB bo'sh joy qoldi)")
        except Exception as e:
            self.finished_signal.emit(False, f"Kesh nusxasini yaratishda xatolik: {e}")


class CacheDeleteWorker(QThread):
    """
    Loyiha o'chirilganda AppData ichidagi kesh, json metadata va ikonka fayllarini avtomatik to'liq tozalash oqimi.
    (Asl manba papkasiga mutlaqo teginmaydi).
    """

    finished_signal = pyqtSignal(bool, str)

    def __init__(self, project_path: str, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.config_mgr = ConfigManager()

    def run(self):
        try:
            project_id = self.config_mgr._get_project_id(self.project_path)
            cache_dir = os.path.join(get_cache_dir(), project_id)

            # 1. AppData kesh papkasini avtomatik va to'liq o'chirish
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir, ignore_errors=True)

            # 2. Config JSON, Ikonka va Index.json dan to'liq tozalash
            self.config_mgr.remove_project(self.project_path)

            self.finished_signal.emit(True, "Loyihaning barcha metadata, ikonka va keshlari AppData'dan avtomatik tozalandi.")
        except Exception as e:
            self.finished_signal.emit(False, f"O'chirishda xatolik: {e}")


class CacheRestoreWorker(QThread):
    """
    Original papka yo'qolganda AppData keshidan loyihani qayta tiklash oqimi.
    """

    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, project_path: str, restore_dest_path: str, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.restore_dest_path = restore_dest_path
        self.config_mgr = ConfigManager()

    def run(self):
        try:
            project_id = self.config_mgr._get_project_id(self.project_path)
            cache_dir = os.path.join(get_cache_dir(), project_id)

            if not os.path.exists(cache_dir):
                self.finished_signal.emit(False, "AppData kesh zaxirasi topilmadi!")
                return

            self.progress_signal.emit(10, "Manzil papka yaratilmoqda...")
            os.makedirs(self.restore_dest_path, exist_ok=True)

            # Keshdan fayllarni qayta tiklash
            all_entries = []
            for root, dirs, files in os.walk(cache_dir):
                for f in files:
                    all_entries.append(os.path.join(root, f))

            total_files = max(1, len(all_entries))
            copied = 0

            for root, dirs, files in os.walk(cache_dir):
                rel_root = os.path.relpath(root, cache_dir)
                target_root = os.path.join(self.restore_dest_path, rel_root) if rel_root != "." else self.restore_dest_path
                os.makedirs(target_root, exist_ok=True)

                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(target_root, file)
                    shutil.copy2(src_file, dst_file)
                    copied += 1
                    self.progress_signal.emit(int((copied / total_files) * 90), f"Qayta tiklanmoqda: {file}")

            self.config_mgr.save_project_data(self.restore_dest_path)
            self.finished_signal.emit(True, "Loyiha keshdan muvaffaqiyatli tiklandi!")
        except Exception as e:
            self.finished_signal.emit(False, f"Keshdan tiklashda xatolik: {e}")
