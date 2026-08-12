from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QFormLayout,
    QWidget,
    QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.utils.config import ConfigManager


class SettingsDialog(QDialog):
    """
    Scode Editor Sozlamalar modali (Ctrl + ,).
    Shriftlar, Tab hajmi, Avto saqlash intervali va Mini-map boshqaruvi bilan.
    Sozlamalar AppData/Local/ScodeEditor/config.json fayliga saqlanadi.
    """

    settings_saved = pyqtSignal(dict)

    def __init__(self, parent=None, config: ConfigManager = None):
        super().__init__(parent)
        self.config = config or ConfigManager()
        self.settings_data = self.config.get_settings()

        self.setWindowTitle("Scode Editor — Sozlamalar")
        self.setFixedSize(520, 440)

        self._build_ui()
        self._load_current_values()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #252526;
                color: #ffffff;
            }
            QLabel {
                color: #cccccc;
                font-size: 12px;
            }
            QLabel#headerTitle {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #1c1c1c;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #007acc;
            }
            QCheckBox {
                color: #cccccc;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: #1c1c1c;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #007acc;
                border: 1px solid #007acc;
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Yuqori Title
        header_title = QLabel("Sozlamalar (Settings)")
        header_title.setObjectName("headerTitle")
        layout.addWidget(header_title)

        # Live Search Field
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Sozlamalarni qidirish...")
        self.search_input.textChanged.connect(self._filter_settings)
        layout.addWidget(self.search_input)

        # Scrollable form container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        self.form_layout = QFormLayout(scroll_content)
        self.form_layout.setSpacing(12)

        # 0. Interfeys Mavzusi (Theme)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "Dark (One Dark Pro)",
            "Dark (Dracula)",
            "Dark+ (VS Code)",
            "Light (GitHub)"
        ])
        self.form_layout.addRow("Rangli Mavzu (Theme):", self.theme_combo)

        # 1. Shrift Turi (Font Family)
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Consolas", "Cascadia Code", "Fira Code", "Courier New", "Arial"])
        self.form_layout.addRow("Shrift turi (Font Family):", self.font_combo)

        # 2. Shrift O'lchami (Font Size)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 32)
        self.form_layout.addRow("Shrift o'lchami (Font Size):", self.font_size_spin)

        # 3. Tab Hajmi (Tab Size)
        self.tab_size_combo = QComboBox()
        self.tab_size_combo.addItems(["2 Spaces", "4 Spaces"])
        self.form_layout.addRow("Tab o'lchami (Tab Size):", self.tab_size_combo)

        # 4. Avto Saqlash Interval (Auto Save Interval)
        self.auto_save_spin = QSpinBox()
        self.auto_save_spin.setRange(1, 30)
        self.auto_save_spin.setSuffix(" soniya")
        self.form_layout.addRow("Avto-saqlash intervali:", self.auto_save_spin)

        # 5. Mini-map Boshqaruvi
        self.minimap_check = QCheckBox("Kod Mini-map panelini ko'rsatish")
        self.form_layout.addRow("Mini-map:", self.minimap_check)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # Lower action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Bekor qilish")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Saqlash")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load_current_values(self):
        """Mavjud sozlamalarni vidjetlarga biriktirish"""
        theme_name = self.settings_data.get("theme", "Dark (One Dark Pro)")
        t_idx = self.theme_combo.findText(theme_name)
        if t_idx >= 0:
            self.theme_combo.setCurrentIndex(t_idx)

        font_family = self.settings_data.get("font_family", "Consolas")
        idx = self.font_combo.findText(font_family)
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)

        self.font_size_spin.setValue(self.settings_data.get("font_size", 11))

        tab_size = self.settings_data.get("tab_size", 4)
        self.tab_size_combo.setCurrentIndex(0 if tab_size == 2 else 1)

        self.auto_save_spin.setValue(self.settings_data.get("auto_save_interval", 2))
        self.minimap_check.setChecked(self.settings_data.get("show_minimap", True))

    def _filter_settings(self, text: str):
        query = text.strip().lower()
        for i in range(self.form_layout.rowCount()):
            label_item = self.form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
            field_item = self.form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)

            show_row = True
            if query and label_item and label_item.widget():
                lbl_text = label_item.widget().text().lower()
                show_row = query in lbl_text

            if label_item and label_item.widget():
                label_item.widget().setVisible(show_row)
            if field_item and field_item.widget():
                field_item.widget().setVisible(show_row)

    def save_settings(self):
        tab_val = 2 if self.tab_size_combo.currentIndex() == 0 else 4
        theme_val = self.theme_combo.currentText()
        updated = {
            "theme": theme_val,
            "font_family": self.font_combo.currentText(),
            "font_size": self.font_size_spin.value(),
            "tab_size": tab_val,
            "auto_save_interval": self.auto_save_spin.value(),
            "show_minimap": self.minimap_check.isChecked(),
        }

        self.config.save_settings(updated)

        # Main Window yoki parent oyna bo'ylab mavzuni zudlik bilan almashtirish
        p = self.parent()
        while p:
            if hasattr(p, "change_theme"):
                p.change_theme(theme_val)
                break
            p = p.parent()

        self.settings_saved.emit(updated)
        self.accept()
