import os
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMenu,
    QInputDialog,
    QMessageBox,
    QFileDialog,
)
from PyQt6.QtGui import QPixmap, QCursor, QIcon
from PyQt6.QtCore import Qt, QSize

from app.utils.icon_manager import IconManager


class ProjectCard(QFrame):
    """
    Loyiha kartasi vidjeti.
    Loyiha ma'lumotlari, SVG ikonka va QIcon kontekst menyusi tugmasini o'z ichiga oladi.
    """

    def __init__(self, project_info, config, on_open, on_icon_changed=None, on_refresh=None):
        super().__init__()
        self.config = config
        self.project_info = project_info
        self.on_open = on_open
        self.on_icon_changed = on_icon_changed
        self.on_refresh = on_refresh or on_icon_changed

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 8px;
                padding: 12px;
            }
            QFrame:hover {
                background-color: #2d2d2d;
                border: 1px solid #007acc;
            }
            QLabel { color: #cccccc; border: none; }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # 1. Ikonka vidjeti (80x80 px)
        self.icon_btn = QLabel()
        self.icon_btn.setFixedSize(80, 80)
        self.icon_btn.setScaledContents(True)
        self.icon_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.icon_btn.setToolTip("Ikonkani o'zgartirish uchun bosing")
        self.update_icon_display()
        layout.addWidget(self.icon_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 2. Loyiha haqida ma'lumotlar
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        # Nomi va Versiyasi
        title_box = QHBoxLayout()
        title_box.setSpacing(8)

        name_text = project_info.get("name", os.path.basename(project_info['path']))
        name_label = QLabel(f"<b>{name_text}</b>")
        name_label.setStyleSheet("font-size: 17px; color: #ffffff;")

        ver_label = QLabel(f"v{project_info.get('version', '0.1.0')}")
        ver_label.setStyleSheet("color: #888888; font-size: 12px;")

        title_box.addWidget(name_label)
        title_box.addWidget(ver_label)
        title_box.addStretch()
        info_layout.addLayout(title_box)

        # Yo'li
        path_label = QLabel(project_info['path'])
        path_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        info_layout.addWidget(path_label)

        # Badjlar
        badges = []
        if project_info.get("git_branch"):
            badges.append(f"Git: {project_info['git_branch']}")
        if project_info.get("venv_path"):
            badges.append("Venv: Active")

        badge_text = " | ".join(badges) if badges else "No Git/Venv"
        badge_label = QLabel(badge_text)
        badge_label.setStyleSheet("color: #007acc; font-size: 11px; font-weight: bold;")
        info_layout.addWidget(badge_label)

        layout.addLayout(info_layout, 1)

        # 3. Ochish tugmasi
        open_btn = QPushButton("Ochish")
        open_btn.setFixedSize(90, 36)
        open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c; 
                color: white; 
                border: none; 
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        open_btn.clicked.connect(lambda: self.on_open(project_info['path']))
        layout.addWidget(open_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 4. SVG Kontekst Menyusi Tugmasi (more-vertical.svg)
        self.menu_btn = QPushButton()
        self.menu_btn.setIcon(IconManager.get_icon("more-vertical"))
        self.menu_btn.setIconSize(QSize(20, 20))
        self.menu_btn.setFixedSize(32, 36)
        self.menu_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.menu_btn.setToolTip("Variantlar")
        self.menu_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #3e3e42;
            }
        """)
        self.menu_btn.clicked.connect(self.show_context_menu)
        layout.addWidget(self.menu_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    def show_context_menu(self):
        """Kontekst menyuni SVG ikonkalar bilan ochish"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #252526;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                padding: 4px;
                border-radius: 4px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 2px;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #04395e;
                color: #ffffff;
            }
        """)

        edit_action = menu.addAction(IconManager.get_icon("edit"), "Nomini tahrirlash")
        delete_action = menu.addAction(IconManager.get_icon("trash"), "Ro'yxatdan o'chirish")

        action = menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))

        if action == edit_action:
            self.edit_project_name()
        elif action == delete_action:
            self.delete_project()

    def edit_project_name(self):
        """QInputDialog orqali loyihaga yangi nom berish va config'ga saqlash"""
        current_name = self.project_info.get("name", os.path.basename(self.project_info['path']))
        new_name, ok = QInputDialog.getText(
            self,
            "Nomini tahrirlash",
            "Loyiha uchun yangi nom kiriting:",
            text=current_name
        )
        if ok and new_name.strip():
            new_name = new_name.strip()
            try:
                self.config.rename_project(self.project_info['path'], new_name)
                if self.on_refresh:
                    self.on_refresh()
            except Exception as e:
                QMessageBox.critical(self, "Xatolik", f"Loyiha nomini saqlashda xatolik: {e}")

    def delete_project(self):
        """QMessageBox.question orqali tasdiq so'rab, loyihani ro'yxatdan o'chirish"""
        proj_name = self.project_info.get("name", os.path.basename(self.project_info['path']))
        reply = QMessageBox.question(
            self,
            "Loyihani o'chirish",
            f"'{proj_name}' loyihasini ro'yxatdan o'chirishni tasdiqlaysizmi?\n\n(Eslatma: Diskdagi fayllaringiz o'chirilmaydi)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.config.remove_project(self.project_info['path'])
                if self.on_refresh:
                    self.on_refresh()
            except Exception as e:
                QMessageBox.critical(self, "Xatolik", f"Loyihani o'chirishda xatolik: {e}")

    def update_icon_display(self):
        """Ikonkani SVG yoki rasm sifatini ko'rsatish"""
        icon_path = self.config.get_project_icon(
            self.project_info['path'], 
            default_auto_icon=self.project_info.get("icon")
        )

        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    80, 80, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.icon_btn.setPixmap(scaled_pixmap)
                self.icon_btn.setStyleSheet("border-radius: 8px; background-color: #1e1e1e; padding: 4px;")
                return

        # Zaxira sifatida folder.svg ikonkasi
        pixmap = IconManager.get_pixmap("folder", 64, 64)
        self.icon_btn.setPixmap(pixmap)
        self.icon_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_btn.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e; 
                border-radius: 8px; 
                padding: 8px;
            }
        """)

    def change_icon(self, event):
        """Ikonkani o'zgartirish fayl dialogi"""
        if event.button() == Qt.MouseButton.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Loyiha uchun ikonka tanlang",
                "",
                "Rasm Fayllari (*.png *.jpg *.jpeg *.ico *.svg)",
            )
            if file_path:
                self.config.save_custom_icon(self.project_info['path'], file_path)
                self.update_icon_display()
                if self.on_icon_changed:
                    self.on_icon_changed()

    def mousePressEvent(self, event):
        if self.icon_btn.geometry().contains(event.pos()):
            self.change_icon(event)
        super().mousePressEvent(event)
