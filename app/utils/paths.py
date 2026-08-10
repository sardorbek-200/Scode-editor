import os
import shutil
from PyQt6.QtCore import QStandardPaths


def get_app_data_dir() -> str:
    """
    Platformaga mos holda AppData/Local papkasini aniqlaydi va yaratadi.
    Windows: %LOCALAPPDATA%/ScodeEditor/ (C:\\Users\\<User>\\AppData\\Local\\ScodeEditor)
    Linux/macOS: ~/.local/share/ScodeEditor/
    """
    path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    if not path:
        if os.name == 'nt':
            base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        else:
            base = os.path.expanduser('~/.local/share')
        path = os.path.join(base, 'ScodeEditor')
    else:
        if not path.endswith("ScodeEditor"):
            path = os.path.join(path, "ScodeEditor")

    os.makedirs(path, exist_ok=True)
    return path


def get_projects_dir() -> str:
    """Loyihalar konfiguratsiyasi saqlanadigan papka (%LOCALAPPDATA%/ScodeEditor/projects/)"""
    d = os.path.join(get_app_data_dir(), "projects")
    os.makedirs(d, exist_ok=True)
    return d


def get_icons_dir() -> str:
    """SVG va ikonkalar saqlanadigan papka (%LOCALAPPDATA%/ScodeEditor/assets/icons/)"""
    d = os.path.join(get_app_data_dir(), "assets", "icons")
    os.makedirs(d, exist_ok=True)
    return d


def sync_local_assets() -> None:
    """
    Loyiha ildizidagi ./assets papkasining barcha tarkibini (shu jumladan icon.png)
    %LOCALAPPDATA%/ScodeEditor/assets/ papkasiga avtomatik ko'chirish/nusxalash.
    """
    app_data_assets_dir = os.path.join(get_app_data_dir(), "assets")
    os.makedirs(app_data_assets_dir, exist_ok=True)

    # Loyiha ildizidagi assets papkasi yo'li
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    local_assets_dir = os.path.join(project_root, "assets")

    if os.path.exists(local_assets_dir):
        for item in os.listdir(local_assets_dir):
            src = os.path.join(local_assets_dir, item)
            dst = os.path.join(app_data_assets_dir, item)
            if os.path.isfile(src):
                try:
                    shutil.copy2(src, dst)
                except Exception as e:
                    print(f"Asset nusxalashda xatolik ({item}): {e}")


def get_app_icon_path() -> str:
    """
    main.py va ilova uchun ikonka yo'lini %LOCALAPPDATA%/ScodeEditor/assets/icon.png papkasidan olish
    """
    sync_local_assets()
    icon_path = os.path.join(get_app_data_dir(), "assets", "icon.png")
    return icon_path


def ensure_app_data_dirs() -> None:
    """AppData/Local ichidagi barcha papkalar yaratilishini ta'minlash"""
    get_app_data_dir()
    get_projects_dir()
    get_icons_dir()
    sync_local_assets()
