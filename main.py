import os
import sys
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from app.utils.paths import ensure_app_data_dirs, get_app_icon_path
from app.utils.icon_manager import IconManager
from app import App

# 1. Windows Taskbar / Task Manager AppUserModelID ni ro'yxatdan o'tkazish
# Bu Python guruhidan ajratib, dasturning shaxsiy .ico ikonkasini ko'rsatishni ta'minlaydi
if sys.platform == 'win32':
    try:
        myappid = 'sardorbek.scode.editor.v1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

# 2. Xavfsiz va mutloq (absolute) ikonka yo'lini aniqlash
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.abspath(os.path.join(BASE_DIR, "assets", "app_icon.ico"))

if not os.path.exists(ICON_PATH):
    ICON_PATH = os.path.abspath(os.path.join(BASE_DIR, "assets", "icon.png"))

if not os.path.exists(ICON_PATH):
    ICON_PATH = os.path.abspath(get_app_icon_path())


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ScodeEditor")

    # AppData papkalari va SVG ikonkalarini tayyorlash
    ensure_app_data_dirs()
    IconManager.ensure_icons()

    # 3. QApplication va oyna uchun xavfsiz ikonkani biriktirish
    if os.path.exists(ICON_PATH):
        app_icon = QIcon(ICON_PATH)
        app.setWindowIcon(app_icon)
    else:
        app_icon = QIcon()

    # 4. Asosiy Oyna (MainWindow / App) obyektini yaratish
    window = App()

    # 5. Window va Taskbar uchun ikonkani biriktirish
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
