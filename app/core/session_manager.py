import os
import json
from PyQt6.QtCore import QPoint, QSize
from PyQt6.QtWidgets import QMainWindow, QWidget, QSplitter
from PyQt6.Qsci import QsciScintilla

from app.utils.paths import get_app_data_dir


def get_roaming_session_file_path() -> str:
    """
    AppData/Roaming/ScodeEditor/session.json yo'lini qaytaradi.
    """
    roaming = os.environ.get("APPDATA")
    if roaming:
        base_dir = os.path.join(roaming, "ScodeEditor")
    else:
        base_dir = get_app_data_dir()

    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "session.json")


def get_local_session_file_path() -> str:
    """
    AppData/Local/ScodeEditor/session.json yo'lini qaytaradi.
    """
    base_dir = get_app_data_dir()
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "session.json")


class SessionManager:
    """
    Kengaytirilgan Sessiya Menejeri (Advanced Session Manager).
    Dastur yopilayotganda barcha ochiq tablar ketma-ketligi, kursor va skroll o'rinlari,
    oyna o'lchamlari hamda panellar holatini AppData/Roaming/ScodeEditor/session.json ga saqlaydi
    va qayta ishga tushganda ularni 100% aniqlikda tezkor qayta tiklaydi.
    """

    def __init__(self, main_window: QMainWindow = None):
        self.main_window = main_window

    def save_session(self, editor_view=None) -> None:
        """
        Dastur yopilayotganda barcha holatlarni JSON formatda saqlab olish.
        """
        try:
            if not editor_view and self.main_window and hasattr(self.main_window, 'editor_view'):
                editor_view = self.main_window.editor_view

            session_data = {
                "project_path": "",
                "open_tabs": [],
                "active_tab_index": 0,
                "split_open_tabs": [],
                "split_active_tab_index": 0,
                "is_split_active": False,
                "window": {
                    "width": 1280,
                    "height": 720,
                    "x": 100,
                    "y": 100,
                    "is_maximized": False,
                },
                "panels": {
                    "explorer_visible": True,
                    "explorer_width": 220,
                    "terminal_visible": False,
                    "terminal_height": 200,
                }
            }

            # 1. Main Window Geometry va Maximized State
            if self.main_window:
                session_data["window"]["width"] = self.main_window.width()
                session_data["window"]["height"] = self.main_window.height()
                session_data["window"]["x"] = self.main_window.x()
                session_data["window"]["y"] = self.main_window.y()
                session_data["window"]["is_maximized"] = self.main_window.isMaximized()

            if editor_view:
                session_data["project_path"] = getattr(editor_view, 'project_path', "") or ""

                # 2. Explorer va Splitter hajmlari
                if hasattr(editor_view, 'top_hsplitter') and editor_view.top_hsplitter:
                    sizes = editor_view.top_hsplitter.sizes()
                    if len(sizes) >= 2:
                        session_data["panels"]["explorer_width"] = sizes[0]
                    if hasattr(editor_view, 'file_explorer'):
                        session_data["panels"]["explorer_visible"] = editor_view.file_explorer.isVisible()

                # 3. Asosiy Tab Paneli barcha fayllari (Code va Image tablar)
                primary_tabs = getattr(editor_view, 'tab_widget', None)
                if primary_tabs:
                    session_data["active_tab_index"] = primary_tabs.currentIndex()
                    for i in range(primary_tabs.count()):
                        container = primary_tabs.widget(i)
                        tab_info = self._extract_tab_info(editor_view, container)
                        if tab_info:
                            session_data["open_tabs"].append(tab_info)

                # 4. Ikkinchi Pane (Split View) barcha tablari
                secondary_tabs = getattr(editor_view, 'right_tab_widget', None)
                if secondary_tabs and secondary_tabs.isVisible():
                    session_data["is_split_active"] = True
                    session_data["split_active_tab_index"] = secondary_tabs.currentIndex()
                    for i in range(secondary_tabs.count()):
                        container = secondary_tabs.widget(i)
                        tab_info = self._extract_tab_info(editor_view, container)
                        if tab_info:
                            session_data["split_open_tabs"].append(tab_info)

            # Roaming va Local fayllarga bir vaqtda saqlash
            roaming_path = get_roaming_session_file_path()
            local_path = get_local_session_file_path()

            for target_path in (roaming_path, local_path):
                try:
                    with open(target_path, "w", encoding="utf-8") as f:
                        json.dump(session_data, f, indent=4, ensure_ascii=False)
                except Exception as e:
                    print(f"Session save to {target_path} failed: {e}")

        except Exception as e:
            print(f"Advanced Session Manager saqlashda xatolik: {e}")

    def _extract_tab_info(self, editor_view, container) -> dict:
        """Konteyner vidjetidan fayl yo'li, kursor pozitsiyasi va skroll o'rinlarini ajratish."""
        if not container:
            return None

        editor = editor_view._extract_editor(container) if hasattr(editor_view, '_extract_editor') else None
        file_path = getattr(editor, 'file_path', None) if editor else getattr(container, 'file_path', None)

        if not file_path or not os.path.exists(file_path):
            return None

        norm_path = os.path.normpath(file_path)
        ext = os.path.splitext(norm_path)[1].lower()
        is_image = ext in ('.png', '.jpg', '.jpeg', '.svg', '.ico', '.bmp', '.webp', '.gif')

        tab_data = {
            "file_path": norm_path,
            "type": "image" if is_image else "code",
            "cursor_line": 0,
            "cursor_col": 0,
            "first_visible_line": 0,
            "h_scroll": 0,
        }

        if editor and isinstance(editor, QsciScintilla):
            line, col = editor.getCursorPosition()
            first_line = editor.firstVisibleLine()
            hbar = editor.horizontalScrollBar()
            h_val = hbar.value() if hbar is not None else 0

            tab_data["cursor_line"] = line
            tab_data["cursor_col"] = col
            tab_data["first_visible_line"] = first_line
            tab_data["h_scroll"] = h_val

        return tab_data

    def restore_session(self, editor_view=None) -> bool:
        """
        Dastur qayta ishga tushganda session.json faylidan oyna o'lchami, ochiq tablar, kursor va skrollni tiklash.
        """
        try:
            roaming_path = get_roaming_session_file_path()
            local_path = get_local_session_file_path()

            session_file = roaming_path if os.path.exists(roaming_path) else local_path
            if not os.path.exists(session_file):
                return False

            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            if not session_data:
                return False

            # 1. Window Geometry & Maximized state
            win_data = session_data.get("window", {})
            if self.main_window and win_data:
                if win_data.get("is_maximized", False):
                    self.main_window.showMaximized()
                else:
                    w = win_data.get("width", 1280)
                    h = win_data.get("height", 720)
                    x = win_data.get("x", 100)
                    y = win_data.get("y", 100)
                    self.main_window.resize(QSize(w, h))
                    self.main_window.move(QPoint(x, y))

            if not editor_view and self.main_window and hasattr(self.main_window, 'editor_view'):
                editor_view = self.main_window.editor_view

            if not editor_view:
                return True

            # 2. Panel holatlari
            panels = session_data.get("panels", {})
            if hasattr(editor_view, 'top_hsplitter') and editor_view.top_hsplitter:
                exp_w = panels.get("explorer_width", 220)
                total = sum(editor_view.top_hsplitter.sizes()) or 1000
                editor_view.top_hsplitter.setSizes([exp_w, max(200, total - exp_w)])

            # 3. Asosiy Tablar va Ularning Kursor/Skroll Joylashuvi
            open_tabs = session_data.get("open_tabs", [])
            active_idx = session_data.get("active_tab_index", 0)

            for tab_info in open_tabs:
                fp = tab_info.get("file_path") if isinstance(tab_info, dict) else tab_info
                if fp and os.path.exists(fp) and hasattr(editor_view, 'open_file'):
                    editor_view.open_file(fp, in_split=False)
                    if isinstance(tab_info, dict):
                        self._apply_cursor_and_scroll(editor_view, editor_view.tab_widget, fp, tab_info)

            tab_widget = getattr(editor_view, 'tab_widget', None)
            if tab_widget and 0 <= active_idx < tab_widget.count():
                tab_widget.setCurrentIndex(active_idx)

            # 4. Split View Tablari hamda ularning holati
            is_split_active = session_data.get("is_split_active", False)
            split_open_tabs = session_data.get("split_open_tabs", [])
            split_active_idx = session_data.get("split_active_tab_index", 0)

            if is_split_active and split_open_tabs:
                for tab_info in split_open_tabs:
                    fp = tab_info.get("file_path") if isinstance(tab_info, dict) else tab_info
                    if fp and os.path.exists(fp) and hasattr(editor_view, 'open_file'):
                        editor_view.open_file(fp, in_split=True)
                        if isinstance(tab_info, dict):
                            self._apply_cursor_and_scroll(editor_view, editor_view.right_tab_widget, fp, tab_info)

                right_tab_widget = getattr(editor_view, 'right_tab_widget', None)
                if right_tab_widget and 0 <= split_active_idx < right_tab_widget.count():
                    right_tab_widget.setCurrentIndex(split_active_idx)

            return True
        except Exception as e:
            print(f"Session restoration error: {e}")
            return False

    def _apply_cursor_and_scroll(self, editor_view, tab_widget, file_path: str, tab_info: dict):
        """Tiklanayotgan tab uchun kursor pozitsiyasi va skroll o'rnini o'rnatish."""
        if not tab_widget:
            return

        for idx in range(tab_widget.count()):
            container = tab_widget.widget(idx)
            editor = editor_view._extract_editor(container) if hasattr(editor_view, '_extract_editor') else None
            ed_path = getattr(editor, 'file_path', None) if editor else getattr(container, 'file_path', None)

            if ed_path and os.path.normcase(os.path.normpath(ed_path)) == os.path.normcase(os.path.normpath(file_path)):
                if editor and isinstance(editor, QsciScintilla):
                    line = max(0, tab_info.get("cursor_line", 0))
                    col = max(0, tab_info.get("cursor_col", 0))
                    first_line = max(0, tab_info.get("first_visible_line", 0))
                    h_val = max(0, tab_info.get("h_scroll", 0))

                    editor.setCursorPosition(line, col)
                    editor.setFirstVisibleLine(first_line)
                    hbar = editor.horizontalScrollBar()
                    if hbar is not None and h_val > 0:
                        hbar.setValue(h_val)
                break
