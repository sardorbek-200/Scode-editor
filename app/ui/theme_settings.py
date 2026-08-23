import os
import json
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QColorDialog,
    QLineEdit,
    QFormLayout,
    QGroupBox,
    QMessageBox,
    QScrollArea,
    QWidget,
)

from app.utils.paths import get_app_data_dir


def get_themes_dir() -> str:
    """
    AppData/Roaming/ScodeEditor/themes/ (va platformaga mos AppData papkasi) yo'lini qaytaradi.
    """
    roaming = os.environ.get("APPDATA")
    if roaming:
        base_dir = os.path.join(roaming, "ScodeEditor", "themes")
    else:
        base_dir = os.path.join(get_app_data_dir(), "themes")

    os.makedirs(base_dir, exist_ok=True)
    return base_dir


DEFAULT_THEME_KEYS = {
    "bg_editor": "#1e1e1e",
    "fg_text": "#d4d4d4",
    "bg_margin": "#1e1e1e",
    "fg_margin": "#656e7b",
    "color_keyword": "#569CD6",
    "color_string": "#CE9178",
    "color_comment": "#6A9955",
    "color_number": "#B5CEA8",
    "color_function": "#DCDCAA",
    "color_identifier": "#9CDCFE",
}


class ColorButton(QPushButton):
    """Rang tanlash va hex rangini ko'rsatish tugmasi."""

    color_changed = pyqtSignal(str)

    def __init__(self, color_hex: str = "#ffffff", parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(110)
        self.clicked.connect(self._choose_color)
        self.update_color(color_hex)

    def update_color(self, color_hex: str):
        self.color_hex = color_hex
        c = QColor(color_hex)
        luminance = (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue())
        text_color = "#000000" if luminance > 128 else "#ffffff"

        self.setText(color_hex.upper())
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                color: {text_color};
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
            }}
            QPushButton:hover {{
                border-color: #007acc;
            }}
        """)

    def _choose_color(self):
        col = QColorDialog.getColor(QColor(self.color_hex), self, "Rangni tanlang")
        if col.isValid():
            self.update_color(col.name())
            self.color_changed.emit(col.name())


class ThemeCustomizerDialog(QDialog):
    """
    Scode Editor Ranglar Mavzusini Sozlash Oynasi (Theme Customizer).
    Mavzular AppData/Roaming/ScodeEditor/themes/ papkasida JSON fayllar sifatida saqlanadi va yuklanadi.
    """

    theme_applied = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.themes_dir = get_themes_dir()
        self.current_theme_colors = dict(DEFAULT_THEME_KEYS)
        self.color_buttons = {}

        self.setWindowTitle("Scode Editor — Ranglar Mavzusini Sozlash (Theme Customizer)")
        self.setFixedSize(560, 580)

        self._build_ui()
        self._load_available_themes()

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
            QLabel#titleLabel {
                color: #ffffff;
                font-size: 15px;
                font-weight: bold;
            }
            QComboBox, QLineEdit {
                background-color: #1c1c1c;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QComboBox:focus, QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QGroupBox {
                color: #007acc;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QPushButton#btnSave {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 7px 18px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton#btnSave:hover {
                background-color: #1177bb;
            }
            QPushButton#btnCancel {
                background-color: #3c3c3c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 7px 16px;
                font-size: 12px;
            }
            QPushButton#btnCancel:hover {
                background-color: #4a4a4a;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Yuqori Mavzu Tanlash va Saqlash paneli
        top_box = QHBoxLayout()
        lbl_select = QLabel("Mavzu (Theme):")
        top_box.addWidget(lbl_select)

        self.combo_themes = QComboBox()
        self.combo_themes.currentIndexChanged.connect(self._on_theme_selected)
        top_box.addWidget(self.combo_themes, 1)

        btn_new_theme = QPushButton("+ Yangi Mavzu")
        btn_new_theme.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #04395e;
                color: #ffffff;
            }
        """)
        btn_new_theme.clicked.connect(self._create_new_theme)
        top_box.addWidget(btn_new_theme)

        layout.addLayout(top_box)

        # Scroll Area ichida Redaktor va Sintaksis Ranglari
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)

        # Group 1: Redaktor Foni va Margin Ranglari
        group_editor = QGroupBox("Redaktor Fon va Margin Ranglari")
        form_editor = QFormLayout(group_editor)
        form_editor.setSpacing(10)

        self._add_color_field(form_editor, "Redaktor Foni (Background):", "bg_editor")
        self._add_color_field(form_editor, "Asosiy Matn (Foreground):", "fg_text")
        self._add_color_field(form_editor, "Margin Foni (Line Numbers BG):", "bg_margin")
        self._add_color_field(form_editor, "Margin Matni (Line Numbers FG):", "fg_margin")

        scroll_layout.addWidget(group_editor)

        # Group 2: Sintaksis Ranglari (Syntax Highlighting)
        group_syntax = QGroupBox("Sintaksis Ranglari (Syntax Colors)")
        form_syntax = QFormLayout(group_syntax)
        form_syntax.setSpacing(10)

        self._add_color_field(form_syntax, "Kalit so'zlar (Keywords):", "color_keyword")
        self._add_color_field(form_syntax, "Matnlar (Strings):", "color_string")
        self._add_color_field(form_syntax, "Izohlar (Comments):", "color_comment")
        self._add_color_field(form_syntax, "Raqamlar (Numbers):", "color_number")
        self._add_color_field(form_syntax, "Funksiyalar (Functions):", "color_function")
        self._add_color_field(form_syntax, "Identifikatorlar (Identifiers):", "color_identifier")

        scroll_layout.addWidget(group_syntax)
        scroll.setWidget(scroll_content)

        layout.addWidget(scroll, 1)

        # Pastki Harakat Tugmalari
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Bekor qilish")
        btn_cancel.setObjectName("btnCancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("JSON Saqlash va Tatbiq etish")
        btn_save.setObjectName("btnSave")
        btn_save.clicked.connect(self._save_and_apply)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def _add_color_field(self, form_layout: QFormLayout, label_text: str, key: str):
        btn = ColorButton(self.current_theme_colors.get(key, "#ffffff"))
        btn.color_changed.connect(lambda hex_val, k=key: self._on_color_changed(k, hex_val))
        self.color_buttons[key] = btn
        form_layout.addRow(label_text, btn)

    def _on_color_changed(self, key: str, hex_val: str):
        self.current_theme_colors[key] = hex_val

    def _load_available_themes(self):
        """AppData/Roaming/ScodeEditor/themes/ ichidagi barcha JSON fayllarni va standart mavzularni yuklash."""
        self.combo_themes.blockSignals(True)
        self.combo_themes.clear()

        # Built-in themes
        self.combo_themes.addItem("Dark (One Dark Pro) [Built-in]")
        self.combo_themes.addItem("Dark+ (VS Code) [Built-in]")
        self.combo_themes.addItem("Dracula [Built-in]")

        # Custom JSON themes from AppData/Roaming/ScodeEditor/themes/
        if os.path.exists(self.themes_dir):
            for file_name in sorted(os.listdir(self.themes_dir)):
                if file_name.endswith(".json"):
                    theme_name = os.path.splitext(file_name)[0]
                    self.combo_themes.addItem(f"★ {theme_name}")

        self.combo_themes.blockSignals(False)
        self._on_theme_selected(0)

    def _on_theme_selected(self, index: int):
        theme_title = self.combo_themes.currentText()
        if not theme_title:
            return

        if "One Dark Pro" in theme_title:
            colors = {
                "bg_editor": "#282c34", "fg_text": "#abb2bf", "bg_margin": "#21252b", "fg_margin": "#5c6370",
                "color_keyword": "#c678dd", "color_string": "#98c379", "color_comment": "#5c6370",
                "color_number": "#d19a66", "color_function": "#61afef", "color_identifier": "#e06c75"
            }
        elif "VS Code" in theme_title:
            colors = dict(DEFAULT_THEME_KEYS)
        elif "Dracula" in theme_title:
            colors = {
                "bg_editor": "#282a36", "fg_text": "#f8f8f2", "bg_margin": "#21222c", "fg_margin": "#6272a4",
                "color_keyword": "#ff79c6", "color_string": "#f1fa8c", "color_comment": "#6272a4",
                "color_number": "#bd93f9", "color_function": "#50fa7b", "color_identifier": "#8be9fd"
            }
        elif theme_title.startswith("★ "):
            raw_name = theme_title.replace("★ ", "").strip()
            file_path = os.path.join(self.themes_dir, f"{raw_name}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        colors = json.load(f)
                except Exception:
                    colors = dict(DEFAULT_THEME_KEYS)
            else:
                colors = dict(DEFAULT_THEME_KEYS)
        else:
            colors = dict(DEFAULT_THEME_KEYS)

        self.current_theme_colors.update(colors)
        for k, btn in self.color_buttons.items():
            if k in colors:
                btn.update_color(colors[k])

    def _create_new_theme(self):
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Yangi Mavzu Yaratish", "Yangi ranglar mavzusi nomini kiriting:")
        if ok and name.strip():
            clean_name = name.strip()
            file_path = os.path.join(self.themes_dir, f"{clean_name}.json")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.current_theme_colors, f, indent=4, ensure_ascii=False)
                self._load_available_themes()
                # Select the newly created theme
                idx = self.combo_themes.findText(f"★ {clean_name}")
                if idx >= 0:
                    self.combo_themes.setCurrentIndex(idx)
            except Exception as e:
                QMessageBox.critical(self, "Xatolik", f"Mavzu yaratishda xatolik: {e}")

    def _save_and_apply(self):
        theme_title = self.combo_themes.currentText()
        if theme_title.startswith("★ "):
            clean_name = theme_title.replace("★ ", "").strip()
        else:
            clean_name = "custom_theme"

        file_path = os.path.join(self.themes_dir, f"{clean_name}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.current_theme_colors, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Mavzu faylini saqlashda xatolik: {e}")

        self.theme_applied.emit(self.current_theme_colors)
        self.accept()
