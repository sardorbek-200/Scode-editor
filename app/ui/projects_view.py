import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt

from app.utils.project_inspector import ProjectInspector

class ProjectCard(QFrame):
    def __init__(self, project_info, on_open):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 6px;
            }
            QFrame:hover {
                background-color: #2a2d2e;
                border: 1px solid #007acc;
            }
            QLabel { color: #cccccc; }
        """)

        layout = QHBoxLayout()

        # 1. Loyiha Ikonkasi
        icon_label = QLabel()
        icon_path = project_info.get("icon")
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("📁")
            icon_label.setStyleSheet("font-size: 28px;")
        layout.addWidget(icon_label)

        # 2. Loyiha Nomi va Yo'li
        info_layout = QVBoxLayout()
        name_label = QLabel(f"<b>{project_info['name']}</b> <span style='color: #888888;'>v{project_info.get('version', '0.1.0')}</span>")
        name_label.setStyleSheet("font-size: 14px; color: #ffffff;")
        
        path_label = QLabel(project_info['path'])
        path_label.setStyleSheet("color: #888888; font-size: 11px;")

        # Badjlar (Git branch, Venv)
        badges = []
        if project_info.get("git_branch"):
            badges.append(f"<b>Git:</b> {project_info['git_branch']}")
        if project_info.get("venv_path"):
            badges.append("<b>Venv:</b> Active")
        
        badge_label = QLabel("  |  ".join(badges) if badges else "No Git/Venv")
        badge_label.setStyleSheet("color: #007acc; font-size: 11px;")

        info_layout.addWidget(name_label)
        info_layout.addWidget(path_label)
        info_layout.addWidget(badge_label)
        layout.addLayout(info_layout, 1)

        # 3. Ochish Tugmasi
        open_btn = QPushButton("Ochish")
        open_btn.setStyleSheet("background-color: #0e639c; color: white; border: none; padding: 6px 12px; border-radius: 4px;")
        open_btn.clicked.connect(lambda: on_open(project_info['path']))
        layout.addWidget(open_btn)

        self.setLayout(layout)


class ProjectsView(QWidget):
    def __init__(self, config, on_project_selected):
        super().__init__()
        self.config = config
        self.on_project_selected = on_project_selected

        main_layout = QVBoxLayout()

        # Yuqori qism: Sarlavha va Yangi Loyiha/Papka Ochish
        top_layout = QHBoxLayout()
        title = QLabel("<h2>Scode Editor — Loyihalar</h2>")
        top_layout.addWidget(title)

        open_btn = QPushButton("+ Papkani Ochish")
        open_btn.setFixedHeight(35)
        open_btn.setStyleSheet("background-color: #23d160; color: white; font-weight: bold; padding: 0 15px; border-radius: 4px;")
        open_btn.clicked.connect(self.open_folder)
        top_layout.addWidget(open_btn, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addLayout(top_layout)

        # Skroll bo'ladigan loyihalar kartalari ro'yxati
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        self.setLayout(main_layout)
        self.load_recent_projects()

    def load_recent_projects(self):
        # Eski kartalarni tozalash
        for i in reversed(range(self.cards_layout.count())): 
            widget = self.cards_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        recent_projects = self.config.get_recent_projects()

        if not recent_projects:
            no_proj = QLabel("Hozircha hech qanday loyiha ochilmagan.")
            no_proj.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.addWidget(no_proj)
            return

        for p in recent_projects:
            path = p.get("path")
            if path and os.path.exists(path):
                # Har bir loyiha papkasini skanerlaymiz
                project_meta = ProjectInspector.inspect(path)
                
                # AppData/Local/ScodeEditor/projects/<ID>.json ga metama'lumotlarni yozamiz
                self.config.save_project_data(path, extra_data=project_meta)

                # Kartochkani chiqarish
                card = ProjectCard(project_meta, on_open=self.on_project_selected)
                self.cards_layout.addWidget(card)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Loyiha papkasini tanlang")
        if folder:
            project_meta = ProjectInspector.inspect(folder)
            self.config.save_project_data(folder, extra_data=project_meta)
            self.load_recent_projects()
            self.on_project_selected(folder)