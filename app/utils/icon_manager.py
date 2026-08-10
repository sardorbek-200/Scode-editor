import os
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize
from app.utils.paths import get_icons_dir

# Vektorli SVG ikonkalar (Inline SVG kodlar - Dark Theme #cccccc va #9cdcfe ranglarida)
SVG_ICONS = {
    "folder.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#cccccc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
</svg>""",

    "file.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#cccccc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
  <polyline points="13 2 13 9 20 9"></polyline>
</svg>""",

    "more-vertical.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#cccccc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="1.5" fill="#cccccc"></circle>
  <circle cx="12" cy="5" r="1.5" fill="#cccccc"></circle>
  <circle cx="12" cy="19" r="1.5" fill="#cccccc"></circle>
</svg>""",

    "edit.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#cccccc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
</svg>""",

    "trash.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f44747" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="3 6 5 6 21 6"></polyline>
  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
</svg>""",

    "arrow-left.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <line x1="19" y1="12" x2="5" y2="12"></line>
  <polyline points="12 19 5 12 12 5"></polyline>
</svg>""",

    "terminal.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#9cdcfe" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="4 17 10 11 4 5"></polyline>
  <line x1="12" y1="19" x2="20" y2="19"></line>
</svg>""",

    "clear.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#cccccc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M20 5H9l-7 7 7 7h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2z"></path>
  <line x1="18" y1="9" x2="12" y2="15"></line>
  <line x1="12" y1="9" x2="18" y2="15"></line>
</svg>""",

    "stop.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f44747" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"></circle>
  <rect x="9" y="9" width="6" height="6" fill="#f44747"></rect>
</svg>""",

    "play.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#23d160" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polygon points="5 3 19 12 5 21 5 3" fill="#23d160"></polygon>
</svg>""",

    "settings.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#cccccc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="3"></circle>
  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
</svg>"""
}


class IconManager:
    """
    Inline SVG ikonkalarini AppData/Local/ScodeEditor/assets/icons papkasida saqlovchi va boshqaruvchi sinf.
    """

    _initialized = False

    @classmethod
    def ensure_icons(cls):
        """Dastur ishga tushganda SVG fayllarni AppData/Local papkasiga yozib qo'yish"""
        if cls._initialized:
            return

        icons_dir = get_icons_dir()
        for filename, svg_content in SVG_ICONS.items():
            file_path = os.path.join(icons_dir, filename)
            if not os.path.exists(file_path):
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(svg_content.strip())
                except Exception as e:
                    print(f"SVG faylini yaratishda xatolik ({filename}): {e}")

        cls._initialized = True

    @classmethod
    def get_icon_path(cls, icon_name: str) -> str:
        """SVG ikonkaning AppData/Local ichidagi to'liq yo'lini qaytaradi"""
        cls.ensure_icons()
        if not icon_name.endswith(".svg"):
            icon_name += ".svg"
        return os.path.join(get_icons_dir(), icon_name)

    @classmethod
    def get_icon(cls, icon_name: str) -> QIcon:
        """SVG ikonkadan QIcon obyekti yaratib qaytaradi"""
        path = cls.get_icon_path(icon_name)
        if os.path.exists(path):
            return QIcon(path)
        return QIcon()

    @classmethod
    def get_pixmap(cls, icon_name: str, width: int = 24, height: int = 24) -> QPixmap:
        """SVG ikonkadan QPixmap obyektini berilgan o'lchamda beradi"""
        path = cls.get_icon_path(icon_name)
        if os.path.exists(path):
            pix = QPixmap(path)
            return pix.scaled(width, height)
        return QPixmap()
