import os
import sys
import shutil
import subprocess
from pathlib import Path
from PyQt6.QtCore import pyqtSignal, Qt, QFileInfo
from PyQt6.QtWidgets import (
    QWidget,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QMenu,
    QPushButton,
    QInputDialog,
    QMessageBox,
    QApplication,
    QSizePolicy,
)
from PyQt6.QtGui import QAction, QPixmap, QPainter, QIcon, QCursor
from PyQt6.QtSvg import QSvgRenderer

from app.ui.tree_icon_provider import ScodeTreeIconProvider, load_svg_icon


class FileTreeItemFrame(QFrame):
    """
    Har bir fayl va papkani ifodalovchi maxsus QFrame vidjeti.
    Git holatiga qarab ranglarni o'zgartirish hamda sichqoncha o'ng tugmasi (Context Menu) ni qo'llab-quvvatlaydi.
    """

    def __init__(self, full_path: str, is_dir: bool, depth: int, explorer, parent=None):
        super().__init__(parent)
        self.full_path = os.path.normpath(full_path)
        self.is_dir = is_dir
        self.depth = depth
        self.explorer = explorer
        self.is_expanded = False

        self.setFixedHeight(26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
            QFrame:hover {
                background-color: #2a2d2e;
                border-radius: 4px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(depth * 14 + 6, 0, 8, 0)
        layout.setSpacing(6)

        # 1. Yoyilish ko'rsatkichi (Arrow / Indicator)
        if is_dir:
            self.arrow_label = QLabel("▶")
            self.arrow_label.setFixedWidth(10)
            self.arrow_label.setStyleSheet("color: #858585; font-size: 10px; font-weight: bold;")
            layout.addWidget(self.arrow_label)
        else:
            self.arrow_label = QLabel("")
            self.arrow_label.setFixedWidth(10)
            layout.addWidget(self.arrow_label)

        # 2. SVG Ikonka uchun QLabel
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(18, 18)
        layout.addWidget(self.icon_label)

        # 3. Fayl / Papka nomi uchun QLabel (Git Status rangini qo'llash)
        name_text = os.path.basename(self.full_path) or self.full_path
        self.name_label = QLabel(name_text)

        color = self.explorer.git_status_map.get(self.full_path, "#cccccc")
        self.name_label.setStyleSheet(f"color: {color}; font-size: 13px; font-family: 'Segoe UI', sans-serif;")
        layout.addWidget(self.name_label, 1)

        self.child_container = None
        self.update_icon()

    def update_icon(self):
        """AppData SVG ikonkasini QLabel ga joylashtirish"""
        info = QFileInfo(self.full_path)
        folder_name = info.fileName()

        if self.is_dir:
            ic = self.explorer.icon_provider._get_folder_icon(folder_name, is_open=self.is_expanded)
        else:
            ic = self.explorer.icon_provider._get_file_icon(folder_name, info.suffix())

        pix = ic.pixmap(18, 18)
        self.icon_label.setPixmap(pix)

    def mousePressEvent(self, event):
        """Chaqqon chertish va bosish hodisalari (Chap va O'ng tugma)"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_dir:
                self.toggle_expand()
            else:
                self.explorer.select_item(self)
                self.explorer.file_clicked.emit(self.full_path)
        elif event.button() == Qt.MouseButton.RightButton:
            self.explorer.select_item(self)
            self.explorer.show_context_menu(self, event.globalPosition().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def toggle_expand(self):
        """Papka ochilishi va yopilishi mantig'i"""
        if not self.is_dir:
            return

        self.is_expanded = not self.is_expanded
        self.arrow_label.setText("▼" if self.is_expanded else "▶")
        self.update_icon()

        if self.child_container:
            self.child_container.setVisible(self.is_expanded)


class CustomFileExplorer(QWidget):
    """
    Sarlavhada tezkor tugmalar (New File, New Folder, Refresh) hamda
    moslashtirilgan kontekst menyusiga ega maxsus Fayl Daraxti vidjeti.
    """

    file_clicked = pyqtSignal(str)

    def __init__(self, project_path: str = None, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.icon_provider = ScodeTreeIconProvider()
        self.selected_frame = None
        self.git_status_map = {}

        self._build_ui()

        if project_path:
            self.set_root_path(project_path)

    def _build_ui(self):
        main_vlayout = QVBoxLayout(self)
        main_vlayout.setContentsMargins(0, 0, 0, 0)
        main_vlayout.setSpacing(0)

        # 1. Explorer Sarlavhasi va Tezkor Tugmalar (Header Bar)
        header = QWidget()
        header.setFixedHeight(34)
        header.setStyleSheet("background-color: #252526; border-bottom: 1px solid #2d2d2d;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10, 0, 8, 0)
        h_layout.setSpacing(4)

        lbl_title = QLabel("EXPLORER")
        lbl_title.setStyleSheet("color: #bbbbbb; font-size: 11px; font-weight: bold; font-family: 'Segoe UI', sans-serif;")
        h_layout.addWidget(lbl_title)
        h_layout.addStretch()

        btn_style = """
            QPushButton {
                background-color: transparent;
                color: #cccccc;
                border: none;
                font-size: 13px;
                border-radius: 3px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #37373d;
                color: #ffffff;
            }
        """

        # New File Button
        btn_new_file = QPushButton("+📄")
        btn_new_file.setToolTip("Yangi Fayl Yaratish (New File)")
        btn_new_file.setFixedSize(24, 24)
        btn_new_file.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_new_file.setStyleSheet(btn_style)
        btn_new_file.clicked.connect(lambda: self.create_new_file(self.selected_frame))
        h_layout.addWidget(btn_new_file)

        # New Folder Button
        btn_new_folder = QPushButton("+📁")
        btn_new_folder.setToolTip("Yangi Papka Yaratish (New Folder)")
        btn_new_folder.setFixedSize(24, 24)
        btn_new_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_new_folder.setStyleSheet(btn_style)
        btn_new_folder.clicked.connect(lambda: self.create_new_folder(self.selected_frame))
        h_layout.addWidget(btn_new_folder)

        # Refresh Button
        btn_refresh = QPushButton("🔄")
        btn_refresh.setToolTip("Fayllar Daraxtini Yangilash (Refresh)")
        btn_refresh.setFixedSize(24, 24)
        btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_refresh.setStyleSheet(btn_style)
        btn_refresh.clicked.connect(lambda: self.set_root_path(self.project_path))
        h_layout.addWidget(btn_refresh)

        main_vlayout.addWidget(header)

        # 2. QScrollArea (Daraxt Mazmuni)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #181818;
                border: none;
            }
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                border-radius: 4px;
            }
        """)

        # Asosiy konteyner vidjeti
        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("background-color: #181818;")
        self.container_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.container_widget.customContextMenuRequested.connect(self._on_background_context_menu)

        self.tree_layout = QVBoxLayout(self.container_widget)
        self.tree_layout.setContentsMargins(4, 4, 4, 4)
        self.tree_layout.setSpacing(1)
        self.tree_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.container_widget)
        main_vlayout.addWidget(self.scroll_area)

    def _on_background_context_menu(self, pos):
        """Bo'sh joyga (fon) sichqonchaning o'ng tugmasi bosilganda menyu chiqarish"""
        self.show_context_menu(None, self.container_widget.mapToGlobal(pos))

    def show_context_menu(self, item_frame: FileTreeItemFrame = None, global_pos = None):
        """File Explorer uchun kontekst menyusi"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                font-size: 12px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 5px 24px 5px 12px;
            }
            QMenu::item:selected {
                background-color: #04395e;
                color: #ffffff;
            }
        """)

        # 1. New File (Yangi fayl)
        action_new_file = QAction("New File (Yangi fayl)", self)
        action_new_file.triggered.connect(lambda: self.create_new_file(item_frame))
        menu.addAction(action_new_file)

        # 2. New Folder (Yangi papka)
        action_new_folder = QAction("New Folder (Yangi papka)", self)
        action_new_folder.triggered.connect(lambda: self.create_new_folder(item_frame))
        menu.addAction(action_new_folder)

        menu.addSeparator()

        # Agar biron-bir element (fayl/papka) ustiga bosilgan bo'lsa
        if item_frame:
            action_rename = QAction("Rename (Qayta nomlash)", self)
            action_rename.triggered.connect(lambda: self.rename_item(item_frame))
            menu.addAction(action_rename)

            action_delete = QAction("Delete (O'chirish)", self)
            action_delete.triggered.connect(lambda: self.delete_item(item_frame))
            menu.addAction(action_delete)

            menu.addSeparator()

            action_copy_path = QAction("Copy Path (To'liq yo'lni nusxalash)", self)
            action_copy_path.triggered.connect(lambda: self.copy_path(item_frame, relative=False))
            menu.addAction(action_copy_path)

            action_copy_rel_path = QAction("Copy Relative Path (Nisbiy yo'lni nusxalash)", self)
            action_copy_rel_path.triggered.connect(lambda: self.copy_path(item_frame, relative=True))
            menu.addAction(action_copy_rel_path)

            menu.addSeparator()

        # Refresh tugmasi bo'sh joyda ham ko'rinsin
        action_refresh = QAction("Refresh (Yangilash)", self)
        action_refresh.triggered.connect(lambda: self.set_root_path(self.project_path))
        menu.addAction(action_refresh)

        # Reveal in Explorer
        action_reveal = QAction("Reveal in Explorer (Tizim papkasida ochish)", self)
        action_reveal.triggered.connect(lambda: self.reveal_in_explorer(item_frame))
        menu.addAction(action_reveal)

        if global_pos:
            menu.exec(global_pos)

    def create_new_file(self, item_frame: FileTreeItemFrame = None):
        """Yangi fayl yaratish"""
        if item_frame:
            target_dir = item_frame.full_path if item_frame.is_dir else os.path.dirname(item_frame.full_path)
        else:
            target_dir = self.project_path or "."

        name, ok = QInputDialog.getText(self, "Yangi Fayl", "Fayl nomini kiriting:")
        if ok and name.strip():
            new_file_path = os.path.join(target_dir, name.strip())
            try:
                open(new_file_path, 'a', encoding='utf-8').close()
                self.set_root_path(self.project_path)
                self.file_clicked.emit(new_file_path)
            except Exception as e:
                QMessageBox.critical(self, "Xatolik", f"Fayl yaratishda xatolik: {e}")

    def create_new_folder(self, item_frame: FileTreeItemFrame = None):
        """Yangi papka yaratish"""
        if item_frame:
            target_dir = item_frame.full_path if item_frame.is_dir else os.path.dirname(item_frame.full_path)
        else:
            target_dir = self.project_path or "."

        name, ok = QInputDialog.getText(self, "Yangi Papka", "Papka nomini kiriting:")
        if ok and name.strip():
            new_folder_path = os.path.join(target_dir, name.strip())
            try:
                os.makedirs(new_folder_path, exist_ok=True)
                self.set_root_path(self.project_path)
            except Exception as e:
                QMessageBox.critical(self, "Xatolik", f"Papka yaratishda xatolik: {e}")

    def rename_item(self, item_frame: FileTreeItemFrame):
        """Fayl yoki papka nomini o'zgartirish"""
        if not item_frame:
            return
        old_path = item_frame.full_path
        old_name = os.path.basename(old_path)
        new_name, ok = QInputDialog.getText(self, "Qayta nomlash", "Yangi nomni kiriting:", text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name.strip())
            try:
                os.rename(old_path, new_path)
                self.set_root_path(self.project_path)
            except Exception as e:
                QMessageBox.critical(self, "Xatolik", f"Nomni o'zgartirishda xatolik: {e}")

    def delete_item(self, item_frame: FileTreeItemFrame):
        """Fayl yoki papkani o'chirish"""
        if not item_frame:
            return
        target_path = item_frame.full_path
        name = os.path.basename(target_path)
        reply = QMessageBox.question(
            self,
            "O'chirishni tasdiqlang",
            f"Haqiqatan ham '{name}' faylini/papkasini o'chirmoqchimisiz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)
                self.set_root_path(self.project_path)
            except Exception as e:
                QMessageBox.critical(self, "Xatolik", f"O'chirishda xatolik: {e}")

    def copy_path(self, item_frame: FileTreeItemFrame = None, relative: bool = False):
        """Fayl yo'lini buferga nusxalash"""
        path = item_frame.full_path if item_frame else self.project_path
        if not path:
            return
        if relative and self.project_path:
            path = os.path.relpath(path, self.project_path)
        QApplication.clipboard().setText(path)

    def reveal_in_explorer(self, item_frame: FileTreeItemFrame = None):
        """Tizim fayl brauzerida ochish"""
        target = item_frame.full_path if item_frame else self.project_path
        if not target or not os.path.exists(target):
            return
        try:
            if os.name == 'nt':
                if os.path.isdir(target):
                    os.startfile(target)
                else:
                    subprocess.run(["explorer", "/select,", target])
            else:
                subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", target])
        except Exception:
            pass

    def load_git_statuses(self):
        """Git status ma'lumotlarini olish va fayl ranglari xaritasini tuzish"""
        self.git_status_map.clear()
        if not self.project_path or not os.path.exists(os.path.join(self.project_path, ".git")):
            return

        try:
            res = subprocess.run(
                ["git", "status", "--porcelain", "--ignored"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if len(line) >= 4:
                        st = line[:2].strip()
                        rel_path = line[3:].strip().strip('"')
                        abs_p = os.path.normpath(os.path.join(self.project_path, rel_path))

                        if 'M' in st or 'R' in st:
                            self.git_status_map[abs_p] = '#e2c08d'  # Modifikatsiyalangan (Sariq)
                        elif '?' in st or 'A' in st:
                            self.git_status_map[abs_p] = '#73c991'  # Yangi (Yashil)
                        elif '!' in st:
                            self.git_status_map[abs_p] = '#6c6c6c'  # Ignored (Kulrang)
        except Exception:
            pass

    def set_root_path(self, path: str):
        """Loyiha ildiz papkasini berish va daraxtni qayta hosil qilish"""
        if not path:
            return
        self.project_path = os.path.normpath(path)
        self.load_git_statuses()
        self.clear_tree()

        if not os.path.exists(self.project_path):
            return

        self._populate_directory(self.project_path, self.tree_layout, depth=0)

    def setRootPath(self, path: str):
        """QFileSystemModel interfeys mosligi uchun"""
        self.set_root_path(path)

    def filePath(self, index=None) -> str:
        """Moslik uchun metod"""
        if self.selected_frame:
            return self.selected_frame.full_path
        return self.project_path or ""

    def clear_tree(self):
        """Daraxt layoutini tozalash"""
        while self.tree_layout.count():
            item = self.tree_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.selected_frame = None

    def select_item(self, frame: FileTreeItemFrame):
        """Tanlangan faylni ajratib ko'rsatish (Highlight)"""
        if self.selected_frame and self.selected_frame != frame:
            color = self.git_status_map.get(self.selected_frame.full_path, "#cccccc")
            self.selected_frame.setStyleSheet("""
                QFrame { background-color: transparent; border: none; }
                QFrame:hover { background-color: #2a2d2e; border-radius: 4px; }
            """)
            self.selected_frame.name_label.setStyleSheet(f"color: {color}; font-size: 13px; font-family: 'Segoe UI', sans-serif;")

        self.selected_frame = frame
        self.selected_frame.setStyleSheet("""
            QFrame { background-color: #37373d; border-radius: 4px; }
        """)

    def _populate_directory(self, dir_path: str, parent_layout: QVBoxLayout, depth: int = 0):
        """Pathlib va os yordamida rekursiv ravishda papka va fayllarni hosil qilish"""
        try:
            p = Path(dir_path)
            entries = sorted(list(p.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))

            for entry in entries:
                full_path = str(entry.resolve())
                is_dir = entry.is_dir()

                item_frame = FileTreeItemFrame(full_path, is_dir, depth, explorer=self)
                parent_layout.addWidget(item_frame)

                if is_dir:
                    child_container = QWidget()
                    child_container.setVisible(False)
                    child_layout = QVBoxLayout(child_container)
                    child_layout.setContentsMargins(0, 0, 0, 0)
                    child_layout.setSpacing(1)

                    item_frame.child_container = child_container
                    parent_layout.addWidget(child_container)

                    self._populate_directory(full_path, child_layout, depth=depth + 1)

        except Exception as e:
            pass
