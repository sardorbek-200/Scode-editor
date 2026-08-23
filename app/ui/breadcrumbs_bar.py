import os
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMenu,
    QSizePolicy,
)
from PyQt6.QtGui import QAction, QIcon
from app.ui.tree_icon_provider import ScodeTreeIconProvider


class BreadcrumbsBar(QWidget):
    """
    Tepadagi tablar va tahrirlagich o'rtasida joylashadigan 24px balandlikdagi
    Breadcrumbs navigatsiya paneli. Fayl yo'li segmentlarini ko'rsatadi hamda
    har bir segment bosilganda katalogni ochuvchi QMenu chiqaradi.
    """

    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(24)
        self.project_path = ""
        self.current_file_path = ""
        self.icon_provider = ScodeTreeIconProvider()

        self.setStyleSheet("""
            BreadcrumbsBar {
                background-color: #1e1e1e;
                border-bottom: 1px solid #2d2d2d;
            }
            QPushButton {
                background: transparent;
                color: #cccccc;
                border: none;
                padding: 0px 4px;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2a2d2e;
                color: #ffffff;
            }
            QLabel {
                color: #6e6e6e;
                font-size: 10px;
                padding: 0 2px;
            }
            QMenu {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                font-size: 11px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 4px 20px 4px 10px;
            }
            QMenu::item:selected {
                background-color: #04395e;
                color: #ffffff;
            }
        """)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 0, 8, 0)
        self.layout.setSpacing(2)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def set_file_path(self, file_path: str, project_path: str = ""):
        """Joriy aktiv fayl yo'lini berish va Breadcrumbs tugmalarini hosil qilish"""
        self.current_file_path = os.path.normpath(file_path) if file_path else ""
        self.project_path = os.path.normpath(project_path) if project_path else ""

        self.clear_breadcrumbs()

        if not self.current_file_path:
            return

        rel_path = self.current_file_path
        if self.project_path and self.current_file_path.startswith(self.project_path):
            proj_name = os.path.basename(self.project_path) or self.project_path
            rel_part = os.path.relpath(self.current_file_path, self.project_path)
            segments = [proj_name] + [s for s in rel_part.split(os.sep) if s]
            base_dir = self.project_path
        else:
            segments = [s for s in self.current_file_path.split(os.sep) if s]
            if os.name == 'nt' and ':' in self.current_file_path:
                drive, rest = os.path.splitdrive(self.current_file_path)
                segments = [drive] + [s for s in rest.split(os.sep) if s]
            base_dir = ""

        accumulated_path = self.project_path if self.project_path else ""

        for idx, seg in enumerate(segments):
            if idx == 0 and self.project_path:
                current_dir = self.project_path
            elif idx == 0:
                current_dir = segments[0] + os.sep
                accumulated_path = current_dir
            else:
                accumulated_path = os.path.join(accumulated_path, seg)
                current_dir = os.path.dirname(accumulated_path) if idx == len(segments) - 1 else accumulated_path

            # Segment tugmasi
            btn = QPushButton(seg)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            # Ikonkani biriktirish
            if idx == len(segments) - 1 and os.path.isfile(self.current_file_path):
                ext = os.path.splitext(seg)[1]
                ic = self.icon_provider._get_file_icon(seg, ext)
                btn.setIcon(ic)
            else:
                ic = self.icon_provider._get_folder_icon(seg, is_open=False)
                btn.setIcon(ic)

            # Menyuni ulash (Dropdown Menu)
            btn.clicked.connect(self._create_menu_closure(current_dir, btn))

            self.layout.addWidget(btn)

            # Ajratgich (Separator)
            if idx < len(segments) - 1:
                sep = QLabel("›")
                self.layout.addWidget(sep)

    def clear_breadcrumbs(self):
        """Layout dagi barcha vidjetlarni tozalash"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _create_menu_closure(self, directory: str, button: QPushButton):
        """Tugma bosilganda o'sha katalogni QMenu menyusi sifatida ko'rsatish"""
        def _show_menu():
            if not os.path.exists(directory) or not os.path.isdir(directory):
                return

            menu = QMenu(self)
            try:
                entries = sorted(os.listdir(directory), key=lambda x: (not os.path.isdir(os.path.join(directory, x)), x.lower()))
                for entry in entries:
                    full_p = os.path.normpath(os.path.join(directory, entry))
                    is_d = os.path.isdir(full_p)

                    action = QAction(entry, menu)
                    if is_d:
                        ic = self.icon_provider._get_folder_icon(entry, is_open=False)
                    else:
                        ext = os.path.splitext(entry)[1]
                        ic = self.icon_provider._get_file_icon(entry, ext)
                    action.setIcon(ic)

                    action.triggered.connect(self._create_action_closure(full_p))
                    menu.addAction(action)

                menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
            except Exception:
                pass

        return _show_menu

    def _create_action_closure(self, path: str):
        def _on_trigger():
            if os.path.isfile(path):
                self.file_selected.emit(path)
            elif os.path.isdir(path):
                self.set_file_path(path, self.project_path)
        return _on_trigger
