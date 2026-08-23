import os
import sys
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from app.utils.paths import ensure_app_data_dirs, get_app_icon_path
from app.utils.icon_manager import IconManager
from app.ui.splash_screen import SplashScreen
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

    # 1. Splash Screen'ni DARHOL (0.1s ichida) ekranga chiqarish
    splash = SplashScreen()
    splash.show()
    splash.set_progress(20, "AppData va sozlamalar yuklanmoqda...")
    app.processEvents()

    # 2. AppData papkalari va SVG ikonkalarini tayyorlash
    ensure_app_data_dirs()
    splash.set_progress(45, "Dinamik ikonka va aktivlar yuklanmoqda...")
    IconManager.ensure_icons()

    # 3. QApplication uchun xavfsiz ikonkani biriktirish
    if os.path.exists(ICON_PATH):
        app_icon = QIcon(ICON_PATH)
        app.setWindowIcon(app_icon)
    else:
        app_icon = QIcon()

    splash.set_progress(75, "Interfeys va tahrirlagich tayyorlanmoqda...")

    # 4. Asosiy Oyna (MainWindow / App) obyektini fonda yaratish
    window = App()

    # 5. Window va Taskbar uchun ikonkani biriktirish
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)

    splash.set_progress(100, "Tayyor!")

    # 6. Splash Screen'ni berkitish hamda Asosiy Oynani namoyish etish
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
