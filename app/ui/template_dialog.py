from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QLineEdit
)
from PyQt6.QtCore import Qt

class TemplateDialog(QDialog):
    def __init__(self, parent=None, default_name="MyProject"):
        super().__init__(parent)
        self.setWindowTitle("Yangi Loyiha Shablonini Tanlang")
        self.setFixedSize(400, 220)
        self.setStyleSheet("""
            QDialog {
                background-color: #252526;
                color: #ffffff;
            }
            QLabel {
                color: #cccccc;
                font-size: 13px;
            }
            QLineEdit, QComboBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton#cancelBtn {
                background-color: #555555;
            }
            QPushButton#cancelBtn:hover {
                background-color: #666666;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Title
        title_label = QLabel("<b>Papka bo'sh. Qaysi shablon asosida yaratamiz?</b>")
        layout.addWidget(title_label)

        # Loyiha nomi
        layout.addWidget(QLabel("Loyiha nomi:"))
        self.name_input = QLineEdit(default_name)
        layout.addWidget(self.name_input)

        # Freymvork / Texnologiya
        layout.addWidget(QLabel("Shablon turi:"))
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "PyQt6 Desktop App (Python)",
            "Express Backend App (Node.js)",
            "React App (Vite / JS)",
            "Bo'sh loyiha bo'lib qolsin"
        ])
        layout.addWidget(self.template_combo)

        # Tugmalar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Bekor qilish")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)

        create_btn = QPushButton("Yaratish")
        create_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(create_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_selected_template(self):
        return {
            "name": self.name_input.text().strip() or "MyProject",
            "template": self.template_combo.currentText()
        }