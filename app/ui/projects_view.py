import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFileDialog,
)
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt

from app.utils.project_inspector import ProjectInspector
from app.ui.project_card import ProjectCard


class ProjectsView(QWidget):
    """Loyihalar ro'yxatini ko'rsatish va yangi papka ochish vidjeti."""

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
        open_btn.setFixedHeight(35)
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

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_projects_list()

    def refresh_projects_list(self):
        """AppData/Local/ScodeEditor/index.json faylidan loyihalarni qayta yuklash"""
        self.load_recent_projects()

    def load_recent_projects(self):
        """So'nggi loyihalarni qayta yuklash"""
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
            is_valid_non_empty = path and os.path.exists(path) and os.path.isdir(path) and len(os.listdir(path)) > 0
            if is_valid_non_empty:
                project_meta = ProjectInspector.inspect(path)
                saved_data = self.config.load_project_data(path)

                if saved_data and saved_data.get("name"):
                    project_meta["name"] = saved_data.get("name")
                elif p.get("name"):
                    project_meta["name"] = p.get("name")

                self.config.save_project_data(path, extra_data=project_meta)

                card = ProjectCard(
                    project_info=project_meta,
                    config=self.config,
                    on_open=self.on_project_selected,
                    on_icon_changed=self.load_recent_projects,
                    on_refresh=self.load_recent_projects
                )
                self.cards_layout.addWidget(card)
            elif path:
                # Original papka yo'q bo'lsa yoki bo'sh (0 ta fayl) bo'lsa -> AppData keshidan avtomatik tiklash
                self._handle_missing_or_empty_project(p)

    def _handle_missing_or_empty_project(self, project_info: dict):
        """Original papka topilmaganda yoki bo'sh (0 ta fayl) bo'lganda, keshdan avtomatik asl o'rniga tiklash"""
        path = project_info.get("path")
        if not path:
            return

        from app.utils.cache_manager import get_cache_dir
        import shutil
        project_id = self.config._get_project_id(path)
        cache_dir = os.path.join(get_cache_dir(), project_id)

        if os.path.exists(cache_dir) and os.listdir(cache_dir):
            try:
                os.makedirs(path, exist_ok=True)
                for item in os.listdir(cache_dir):
                    s = os.path.join(cache_dir, item)
                    d = os.path.join(path, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
            except Exception:
                pass

        # Kartani qayta ko'rsatish uchun metadata saqlash
        if os.path.exists(path):
            project_meta = ProjectInspector.inspect(path)
            project_meta["name"] = project_info.get("name", os.path.basename(path))
            self.config.save_project_data(path, extra_data=project_meta)
            card = ProjectCard(
                project_info=project_meta,
                config=self.config,
                on_open=self.on_project_selected,
                on_icon_changed=self.load_recent_projects,
                on_refresh=self.load_recent_projects
            )
            self.cards_layout.addWidget(card)

    def open_folder(self):
        """
        Papka tanlanganda (bo'sh yoki to'la bo'lishidan qat'i nazar),
        loyihani ochish va background QThread da AppData zaxirasini yarata boshlash.
        """
        folder = QFileDialog.getExistingDirectory(self, "Loyiha papkasini tanlang")
        if folder:
            project_meta = ProjectInspector.inspect(folder)
            saved_data = self.config.load_project_data(folder)
            if saved_data and saved_data.get("name"):
                project_meta["name"] = saved_data.get("name")

            self.config.save_project_data(folder, extra_data=project_meta)
            self.refresh_projects_list()

            # Background QThread orqali AppData kesh zaxirasini yozish (10 GB disk joyi sharti bilan)
            from app.utils.cache_manager import CacheBackupWorker
            self.backup_worker = CacheBackupWorker(folder)
            self.backup_worker.start()

            self.on_project_selected(folder, False)