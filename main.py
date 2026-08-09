import sys
import os
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from app import App

def main():
    # 1. Windows taskbarga bu alohida ilova ekanligini bildiramiz
    try:
        myappid = 'scode.editor.app.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    
    # 2. Bosh ikonkani butun ilovaning o'ziga (App level) o'rnatamiz
    icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = App()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()