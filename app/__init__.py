import os
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtGui import QIcon

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scode Editor")
        self.setGeometry(100, 100, 1000, 600)
        
        # Oyna ikonkasini o'rnatish
        # Ikonka fayli 'assets/icon.png' yo'lida bo'lishi kerak
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Ikonka topilmadi: {icon_path}")