import os
from pathlib import Path
from PyQt6.QtCore import QFileInfo, QModelIndex, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QFileSystemModel, QStandardItemModel, QStandardItem
from PyQt6.QtSvg import QSvgRenderer

try:
    from PyQt6.QtGui import QAbstractFileIconProvider
except ImportError:
    from PyQt6.QtWidgets import QFileIconProvider as QAbstractFileIconProvider

try:
    from PyQt6.QtWidgets import QFileIconProvider
except ImportError:
    QFileIconProvider = QAbstractFileIconProvider

from app.utils.paths import get_file_icons_dir

DEFAULT_FOLDER_ICONS = {
    "folder.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#dcdcaa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#dcdcaa" fill-opacity="0.15"></path>
</svg>""",
    "folder-open.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#dcdcaa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M6 14l1.45-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.55 6a2 2 0 0 1-1.94 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2v2" fill="#dcdcaa" fill-opacity="0.25"></path>
</svg>""",
    "folder-src.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4ec9b0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#4ec9b0" fill-opacity="0.2"></path>
  <polyline points="9 13 7 15 9 17"></polyline>
  <polyline points="15 13 17 15 15 17"></polyline>
</svg>""",
    "folder-src-open.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4ec9b0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M6 14l1.45-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.55 6a2 2 0 0 1-1.94 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2v2" fill="#4ec9b0" fill-opacity="0.3"></path>
</svg>""",
    "folder-app.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#c586c0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#c586c0" fill-opacity="0.2"></path>
</svg>""",
    "folder-app-open.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#c586c0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M6 14l1.45-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.55 6a2 2 0 0 1-1.94 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2v2" fill="#c586c0" fill-opacity="0.3"></path>
</svg>""",
    "folder-components.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4ec9b0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#4ec9b0" fill-opacity="0.2"></path>
</svg>""",
    "folder-assets.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ce9178" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#ce9178" fill-opacity="0.2"></path>
</svg>""",
    "folder-public.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ce9178" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#ce9178" fill-opacity="0.2"></path>
</svg>""",
    "folder-utils.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#9cdcfe" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#9cdcfe" fill-opacity="0.2"></path>
</svg>""",
    "folder-node_modules.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6a9955" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#6a9955" fill-opacity="0.2"></path>
</svg>""",
    "folder-git.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f44747" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#f44747" fill-opacity="0.2"></path>
</svg>""",
    "folder-vscode.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#007acc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#007acc" fill-opacity="0.2"></path>
</svg>""",
}

DEFAULT_FILE_ICONS = {
    "file.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#cccccc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",
    "file-py.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3572A5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#3572A5" fill-opacity="0.15"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
  <path d="M9 14a1 1 0 1 0 2 0 1 1 0 1 0-2 0" fill="#3572A5"></path>
</svg>""",
    "file-js.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f1e05a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#f1e05a" fill-opacity="0.15"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",
    "file-jsx.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#61dafb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#61dafb" fill-opacity="0.15"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",
    "file-ts.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2b7489" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#2b7489" fill-opacity="0.15"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",
    "file-html.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#e34c26" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#e34c26" fill-opacity="0.15"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",
    "file-css.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#563d7c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#563d7c" fill-opacity="0.15"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",
    "file-json.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#cbd5e1" fill-opacity="0.15"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",
    "file-git.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f44747" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#f44747" fill-opacity="0.15"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",
    "file-readme.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#007acc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#007acc" fill-opacity="0.15"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",
    "file-docker.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0db7ed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#0db7ed" fill-opacity="0.15"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",
    "file-svg.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ff9900" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#ff9900" fill-opacity="0.15"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",
    "file-image.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#b5cea8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#b5cea8" fill-opacity="0.15"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
  <circle cx="8.5" cy="12.5" r="1.5" fill="#b5cea8"></circle>
</svg>""",
    "file-markdown.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4ec9b0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#4ec9b0" fill-opacity="0.15"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",
    "file-text.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#cccccc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",
    "file-requirements.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3572A5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#3572A5" fill-opacity="0.15"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",
}


def load_svg_icon(svg_path: str) -> QIcon:
    """SVG faylini QSvgRenderer orqali 32x32 shaffof QIcon ga o'qish"""
    if not svg_path or not os.path.exists(svg_path):
        return QIcon()

    try:
        renderer = QSvgRenderer(svg_path)
        if renderer.isValid():
            pix = QPixmap(32, 32)
            pix.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pix)
            renderer.render(painter)
            painter.end()
            return QIcon(pix)
    except Exception:
        pass

    return QIcon(svg_path)


class ScodeTreeIconProvider(QAbstractFileIconProvider):
    """
    AppData/Roaming/ScodeEditor/assets/file-icons/ katalogidagi SVG ikonkalar asosida
    fayl va papkalarga mos ikonkalarni tanlovchi provayder sinfi.
    """

    def __init__(self, model=None):
        super().__init__()
        self.model = model
        self._icon_cache = {}
        self.expanded_paths = set()
        self.base_dir = get_file_icons_dir()
        self.ensure_default_file_icons()

    def set_model(self, model):
        self.model = model

    def set_expanded(self, index: QModelIndex, expanded: bool):
        if not self.model or not index.isValid():
            return
        if hasattr(self.model, 'filePath'):
            path = os.path.normpath(self.model.filePath(index))
            if expanded:
                self.expanded_paths.add(path)
            else:
                self.expanded_paths.discard(path)
            if hasattr(self.model, 'dataChanged'):
                self.model.dataChanged.emit(index, index)

    def clear_cache(self):
        self._icon_cache.clear()

    def get_search_dirs(self):
        dirs = [self.base_dir]
        if os.name == 'nt':
            roaming = os.environ.get('APPDATA', '')
            if roaming:
                r_dir = os.path.join(roaming, 'ScodeEditor', 'assets', 'file-icons')
                if r_dir not in dirs:
                    os.makedirs(os.path.join(r_dir, "files"), exist_ok=True)
                    os.makedirs(os.path.join(r_dir, "folders"), exist_ok=True)
                    dirs.append(r_dir)
        return dirs

    def ensure_default_file_icons(self):
        for base in self.get_search_dirs():
            f_dir = os.path.join(base, "files")
            d_dir = os.path.join(base, "folders")
            os.makedirs(f_dir, exist_ok=True)
            os.makedirs(d_dir, exist_ok=True)

            default_folder_path = os.path.join(base, "default-folder.svg")
            if not os.path.exists(default_folder_path):
                try:
                    with open(default_folder_path, "w", encoding="utf-8") as f:
                        f.write(DEFAULT_FOLDER_ICONS["folder.svg"])
                except Exception:
                    pass

            default_file_path = os.path.join(base, "default-file.svg")
            if not os.path.exists(default_file_path):
                try:
                    with open(default_file_path, "w", encoding="utf-8") as f:
                        f.write(DEFAULT_FILE_ICONS["file.svg"])
                except Exception:
                    pass

            for name, content in DEFAULT_FOLDER_ICONS.items():
                p = os.path.join(d_dir, name)
                if not os.path.exists(p):
                    try:
                        with open(p, "w", encoding="utf-8") as f:
                            f.write(content.strip())
                    except Exception:
                        pass

            for name, content in DEFAULT_FILE_ICONS.items():
                p = os.path.join(f_dir, name)
                if not os.path.exists(p):
                    try:
                        with open(p, "w", encoding="utf-8") as f:
                            f.write(content.strip())
                    except Exception:
                        pass

    def icon(self, type_or_info) -> QIcon:
        if isinstance(type_or_info, QFileInfo):
            info = type_or_info
            file_path = os.path.normpath(info.filePath())
            file_name = info.fileName().lower()

            if info.isDir():
                is_open = file_path in self.expanded_paths
                return self._get_folder_icon(file_name, is_open=is_open)
            else:
                ext = info.suffix().lower()
                return self._get_file_icon(file_name, ext)

        return super().icon(type_or_info)

    def _find_icon_in_dirs(self, relative_path: str) -> str:
        for base in self.get_search_dirs():
            target = os.path.join(base, relative_path)
            if os.path.exists(target):
                return target
        return None

    def _get_folder_icon(self, folder_name: str, is_open: bool = False) -> QIcon:
        clean_name = folder_name.lstrip('.').lower()
        cache_key = f"folder:{clean_name}:open={is_open}"
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        possible_paths = []
        if is_open:
            possible_paths.extend([
                os.path.join("folders", f"folder-{clean_name}-open.svg"),
                os.path.join("folders", f"folder-{folder_name.lower()}-open.svg"),
                os.path.join("folders", "folder-open.svg"),
                "default-folder-open.svg"
            ])

        possible_paths.extend([
            os.path.join("folders", f"folder-{clean_name}.svg"),
            os.path.join("folders", f"folder-{folder_name.lower()}.svg"),
            os.path.join("folders", "folder.svg"),
            "default-folder.svg"
        ])

        for rel_p in possible_paths:
            found = self._find_icon_in_dirs(rel_p)
            if found:
                ic = load_svg_icon(found)
                if not ic.isNull():
                    self._icon_cache[cache_key] = ic
                    return ic

        return super().icon(QAbstractFileIconProvider.IconType.Folder)

    def _get_file_icon(self, file_name: str, ext: str) -> QIcon:
        clean_ext = ext.lstrip('.').lower()
        cache_key = f"file:{file_name}:{clean_ext}"
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        EXACT_MAP = {
            "package.json": "file-json.svg",
            ".gitignore": "file-git.svg",
            "requirements.txt": "file-requirements.svg",
            "readme.md": "file-readme.svg",
            "dockerfile": "file-docker.svg",
            "license": "file-text.svg",
            "main.py": "file-py.svg",
        }

        EXT_MAP = {
            "py": "file-py.svg", "js": "file-js.svg", "jsx": "file-jsx.svg",
            "ts": "file-ts.svg", "tsx": "file-jsx.svg", "html": "file-html.svg",
            "css": "file-css.svg", "json": "file-json.svg", "svg": "file-svg.svg",
            "png": "file-image.svg", "jpg": "file-image.svg", "md": "file-markdown.svg",
            "txt": "file-text.svg",
        }

        candidate_rel_paths = []
        if file_name in EXACT_MAP:
            candidate_rel_paths.append(os.path.join("files", EXACT_MAP[file_name]))

        if clean_ext in EXT_MAP:
            candidate_rel_paths.append(os.path.join("files", EXT_MAP[clean_ext]))

        if clean_ext:
            candidate_rel_paths.append(os.path.join("files", f"file-{clean_ext}.svg"))

        candidate_rel_paths.append(os.path.join("files", "file.svg"))
        candidate_rel_paths.append("default-file.svg")

        for rel_p in candidate_rel_paths:
            found = self._find_icon_in_dirs(rel_p)
            if found:
                ic = load_svg_icon(found)
                if not ic.isNull():
                    self._icon_cache[cache_key] = ic
                    return ic

        return super().icon(QAbstractFileIconProvider.IconType.File)


class ScodeFileSystemModel(QFileSystemModel):
    """QFileSystemModel override qilingan sinfi — OS shell keshini aylanib o'tadi"""

    def __init__(self, icon_provider=None, parent=None):
        super().__init__(parent)
        self._provider = icon_provider
        if icon_provider:
            super().setIconProvider(icon_provider)

    def setIconProvider(self, provider):
        self._provider = provider
        if provider:
            provider.set_model(self)
        super().setIconProvider(provider)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DecorationRole and index.isValid() and self._provider:
            info = self.fileInfo(index)
            return self._provider.icon(info)
        return super().data(index, role)


class ScodeStandardFileTreeModel(QStandardItemModel):
    """
    QStandardItemModel ga asoslangan maxsus fayl daraxti tizimi.
    Loyihani rekursiv o'qib, AppData SVG ikonkalarni har bir elementga (QStandardItem)
    to'g'ridan-to'g'ri biriktiradi va yoyilish (expanded/collapsed) holatini boshqaradi.
    """

    def __init__(self, icon_provider=None, parent=None):
        super().__init__(parent)
        self.icon_provider = icon_provider or ScodeTreeIconProvider()
        self.icon_provider.set_model(self)
        self.project_path = ""
        self._path_item_map = {}

    def set_root_path(self, path: str):
        """Loyiha papkasini o'qib, fayllar daraxtini qayta qurish"""
        self.clear()
        self.setHorizontalHeaderLabels(["Loyiha Fayllari"])
        self._path_item_map.clear()

        if not path or not os.path.exists(path):
            return QModelIndex()

        self.project_path = os.path.normpath(path)
        root_item = self.invisibleRootItem()
        self._populate_directory(self.project_path, root_item)
        return self.index(0, 0)

    def setRootPath(self, path: str):
        """QFileSystemModel bilan mos keluvchi interfeys usuli"""
        return self.set_root_path(path)

    def filePath(self, index: QModelIndex) -> str:
        """Berilgan index dan to'liq fayl yo'lini qaytaradi"""
        if not index.isValid():
            return ""
        return index.data(Qt.ItemDataRole.UserRole + 1) or ""

    def isDir(self, index: QModelIndex) -> bool:
        """Berilgan index papka ekanligini qaytaradi"""
        if not index.isValid():
            return False
        return bool(index.data(Qt.ItemDataRole.UserRole + 2))

    def _populate_directory(self, dir_path: str, parent_item: QStandardItem):
        """Pathlib/os yordamida papkani rekursiv tahlil qilish va daraxtga item qo'shish"""
        try:
            p = Path(dir_path)
            entries = sorted(list(p.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))

            for entry in entries:
                full_path = os.path.normpath(str(entry.resolve()))
                is_dir = entry.is_dir()

                item = QStandardItem(entry.name)
                # UserRole larda to'liq yo'l va papka bayrog'ini saqlash
                item.setData(full_path, Qt.ItemDataRole.UserRole + 1)
                item.setData(is_dir, Qt.ItemDataRole.UserRole + 2)

                # AppData dan mos ikonkani aniqlash va item.setIcon berish
                info = QFileInfo(full_path)
                ic = self.icon_provider.icon(info)
                item.setIcon(ic)

                self._path_item_map[full_path] = item
                parent_item.appendRow(item)

                if is_dir:
                    self._populate_directory(full_path, item)
        except Exception:
            pass

    def on_expanded(self, index: QModelIndex):
        """Papka yoyilganda (expanded) folder-name-open.svg ikonkasini biriktirish"""
        item = self.itemFromIndex(index)
        if item and item.data(Qt.ItemDataRole.UserRole + 2):
            path = item.data(Qt.ItemDataRole.UserRole + 1)
            folder_name = os.path.basename(path)
            ic = self.icon_provider._get_folder_icon(folder_name, is_open=True)
            item.setIcon(ic)

    def on_collapsed(self, index: QModelIndex):
        """Papka yopilganda (collapsed) folder-name.svg ikonkasini biriktirish"""
        item = self.itemFromIndex(index)
        if item and item.data(Qt.ItemDataRole.UserRole + 2):
            path = item.data(Qt.ItemDataRole.UserRole + 1)
            folder_name = os.path.basename(path)
            ic = self.icon_provider._get_folder_icon(folder_name, is_open=False)
            item.setIcon(ic)
