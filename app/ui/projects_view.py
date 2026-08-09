import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtGui import QPixmap, QCursor
from PyQt6.QtCore import Qt

from app.utils.project_inspector import ProjectInspector
from app.utils.installer import PackageInstallerThread


class ProjectCard(QFrame):
    def __init__(self, project_info, config, on_open, on_icon_changed):
        super().__init__()
        self.config = config
        self.project_info = project_info
        self.on_open = on_open
        self.on_icon_changed = on_icon_changed

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

        # 1. Ikonka tugmasi (80x80 px ga kattalashtirildi)
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
        
        name_label = QLabel(f"<b>{project_info['name']}</b>")
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

        self.setLayout(layout)

    def update_icon_display(self):
        """Ikonkani kattaroq ko'rsatish"""
        icon_path = self.config.get_project_icon(
            self.project_info['path'], 
            default_auto_icon=self.project_info.get("icon")
        )

        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                # 80x80 o'lchamga sifatli masshtablash
                scaled_pixmap = pixmap.scaled(
                    80, 80, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.icon_btn.setPixmap(scaled_pixmap)
                self.icon_btn.setStyleSheet("border-radius: 8px; background-color: #1e1e1e; padding: 4px;")
        else:
            self.icon_btn.setText("📁")
            self.icon_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.icon_btn.setStyleSheet("""
                QLabel {
                    font-size: 48px; 
                    background-color: #333333; 
                    border-radius: 8px; 
                }
            """)

    def change_icon(self, event):
        """Ikonkani o'zgartirish uchun fayl dialogi"""
        if event.button() == Qt.MouseButton.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Loyiha uchun ikonka tanlang",
                "",
                "Rasm Fayllari (*.png *.jpg *.jpeg *.ico *.svg)",
            )
            if file_path:
                self.config.set_project_icon(self.project_info['path'], file_path)
                self.update_icon_display()
                if self.on_icon_changed:
                    self.on_icon_changed()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.change_icon(event)
        super().mousePressEvent(event)

class ProjectsView(QWidget):
    def __init__(self, config, on_project_selected):
        super().__init__()
        self.config = config
        self.on_project_selected = on_project_selected

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Yuqori panel
        top_layout = QHBoxLayout()
        title = QLabel("<h2>Scode Editor — Loyihalar</h2>")
        top_layout.addWidget(title)

        open_btn = QPushButton("+ Papkani Ochish")
        open_btn.setFixedHeight(35)  # setHeight -> setFixedHeight ga tuzatildi
        open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #23d160; 
                color: white; 
                font-weight: bold; 
                padding: 8px 16px; 
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #20bc55;
            }
        """)
        open_btn.clicked.connect(self.open_folder)
        top_layout.addWidget(open_btn, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addLayout(top_layout)

        # Skroll bo'ladigan ro'yxat
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        self.setLayout(main_layout)
        self.load_recent_projects()

    def load_recent_projects(self):
        for i in reversed(range(self.cards_layout.count())): 
            widget = self.cards_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        recent_projects = self.config.get_recent_projects()

        if not recent_projects:
            no_proj = QLabel("Hozircha hech qanday loyiha ochilmagan.")
            no_proj.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_proj.setStyleSheet("color: #777777; font-size: 14px; margin-top: 50px;")
            self.cards_layout.addWidget(no_proj)
            return

        for p in recent_projects:
            path = p.get("path")
            if path and os.path.exists(path):
                project_meta = ProjectInspector.inspect(path)
                self.config.save_project_data(path, extra_data=project_meta)

                card = ProjectCard(
                    project_info=project_meta, 
                    config=self.config,
                    on_open=self.on_project_selected,
                    on_icon_changed=self.load_recent_projects
                )
                self.cards_layout.addWidget(card)

    # ProjectsView klassidagi open_folder metodiga quyidagi qo'shimcha kiritiladi:
    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Loyiha papkasini tanlang")
        if folder:
            # Papka bo'sh yoki yo'qligini tekshirish
            if not os.listdir(folder):
                from app.ui.template_dialog import TemplateDialog
                from app.utils.project_generator import ProjectGenerator

                dialog = TemplateDialog(self, default_name=os.path.basename(folder))
                if dialog.exec():
                    data = dialog.get_selected_template()
                    template_type = data["template"]
                    app_name = data["name"]

                    if "PyQt6" in template_type:
                        ProjectGenerator.create_pyqt6_app(folder, app_name)
                    elif "Express" in template_type:
                        ProjectGenerator.create_express_app(folder, app_name)
                    elif "React" in template_type:
                        ProjectGenerator.create_react_app(folder, app_name)

                    if os.path.exists(folder):
                        self.on_project_selected(folder, True)
                        return

            project_meta = ProjectInspector.inspect(folder)
            self.config.save_project_data(folder, extra_data=project_meta)
            self.load_recent_projects()
            self.on_project_selected(folder, False)