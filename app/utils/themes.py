"""
Scode Editor - Mavzular Tizimi (Theme System)
Ranglar palitralari va QSS stylesheet generatori.
"""

THEMES = {
    "Dark (One Dark Pro)": {
        "bg_dark": "#21252b",
        "bg_lighter": "#282c34",
        "bg_editor": "#282c34",
        "bg_panel": "#21252b",
        "bg_header": "#1b1d23",
        "fg": "#abb2bf",
        "fg_muted": "#5c6370",
        "accent": "#61afef",
        "accent_hover": "#5296ce",
        "selection": "#3e4451",
        "border": "#181a1f",
        "status_bg": "#21252b",
        "status_fg": "#9da5b4",
    },
    "Dark (Dracula)": {
        "bg_dark": "#21222c",
        "bg_lighter": "#282a36",
        "bg_editor": "#282a36",
        "bg_panel": "#21222c",
        "bg_header": "#191a21",
        "fg": "#f8f8f2",
        "fg_muted": "#6272a4",
        "accent": "#bd93f9",
        "accent_hover": "#ff79c6",
        "selection": "#44475a",
        "border": "#191a21",
        "status_bg": "#191a21",
        "status_fg": "#f8f8f2",
    },
    "Dark+ (VS Code)": {
        "bg_dark": "#1e1e1e",
        "bg_lighter": "#252526",
        "bg_editor": "#1e1e1e",
        "bg_panel": "#252526",
        "bg_header": "#333333",
        "fg": "#cccccc",
        "fg_muted": "#858585",
        "accent": "#007acc",
        "accent_hover": "#1177bb",
        "selection": "#264f78",
        "border": "#2d2d2d",
        "status_bg": "#007acc",
        "status_fg": "#ffffff",
    },
    "Light (GitHub)": {
        "bg_dark": "#f6f8fa",
        "bg_lighter": "#ffffff",
        "bg_editor": "#ffffff",
        "bg_panel": "#f6f8fa",
        "bg_header": "#e1e4e8",
        "fg": "#24292e",
        "fg_muted": "#6a737d",
        "accent": "#0366d6",
        "accent_hover": "#005cc5",
        "selection": "#0366d633",
        "border": "#e1e4e8",
        "status_bg": "#0366d6",
        "status_fg": "#ffffff",
    },
}

DEFAULT_THEME = "Dark (One Dark Pro)"


def get_theme_colors(theme_name: str) -> dict:
    """Mavzu ranglar palitrasini olish"""
    return THEMES.get(theme_name, THEMES[DEFAULT_THEME])


def get_stylesheet(theme_name: str) -> str:
    """
    Berilgan mavzu nomi uchun ilovaning barcha vidjetlariga mos keluvchi 
    to'liq QSS stylesheet matnini generatsiya qilish.
    """
    c = get_theme_colors(theme_name)

    return f"""
    /* Asosiy Vidjetlar */
    QMainWindow, QDialog, QWidget {{
        background-color: {c['bg_dark']};
        color: {c['fg']};
        font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    }}

    /* Top Bar va Header panellar */
    QWidget#topBarPanel, QWidget#terminalHeader {{
        background-color: {c['bg_header']};
        border-bottom: 1px solid {c['border']};
    }}

    QLabel#breadcrumbPath {{
        color: {c['fg_muted']};
        font-weight: 500;
    }}

    /* Sarlavhalar va Matnlar */
    QLabel {{
        color: {c['fg']};
    }}

    /* Tugmalar */
    QPushButton {{
        background-color: {c['bg_lighter']};
        color: {c['fg']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 5px 12px;
        font-size: 12px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {c['selection']};
        color: {c['accent']};
        border-color: {c['accent']};
    }}
    QPushButton:pressed {{
        background-color: {c['accent']};
        color: #ffffff;
    }}
    QPushButton:disabled {{
        color: {c['fg_muted']};
        border-color: {c['border']};
    }}

    /* Kirish maydonlari (QLineEdit, QTextEdit, QComboBox) */
    QLineEdit, QTextEdit, QComboBox {{
        background-color: {c['bg_lighter']};
        color: {c['fg']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 6px;
        selection-background-color: {c['selection']};
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border-color: {c['accent']};
    }}

    /* QComboBox Dropdown */
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left: none;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['bg_lighter']};
        color: {c['fg']};
        selection-background-color: {c['selection']};
        border: 1px solid {c['border']};
    }}

    /* QTreeView (Loyihalar Daraxti) */
    QTreeView {{
        background-color: {c['bg_panel']};
        color: {c['fg']};
        border: 1px solid {c['border']};
        outline: 0;
    }}
    QTreeView::item {{
        padding: 4px;
        border-radius: 3px;
    }}
    QTreeView::item:hover {{
        background-color: {c['selection']};
    }}
    QTreeView::item:selected {{
        background-color: {c['selection']};
        color: {c['accent']};
    }}

    /* QTabWidget va QTabBar (Fayl Tablari) */
    QTabWidget::pane {{
        border: 1px solid {c['border']};
        background-color: {c['bg_editor']};
    }}
    QTabBar::tab {{
        background-color: {c['bg_panel']};
        color: {c['fg_muted']};
        border: 1px solid {c['border']};
        border-bottom: none;
        padding: 7px 14px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{
        background-color: {c['bg_editor']};
        color: {c['accent']};
        font-weight: bold;
        border-top: 2px solid {c['accent']};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {c['selection']};
        color: {c['fg']};
    }}

    /* QSplitter */
    QSplitter::handle {{
        background-color: {c['border']};
    }}
    QSplitter::handle:hover {{
        background-color: {c['accent']};
    }}

    /* QMenu va QMenuBar */
    QMenuBar {{
        background-color: {c['bg_dark']};
        color: {c['fg']};
        border-bottom: 1px solid {c['border']};
    }}
    QMenuBar::item:selected {{
        background-color: {c['selection']};
    }}
    QMenu {{
        background-color: {c['bg_panel']};
        color: {c['fg']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px;
        border-radius: 2px;
    }}
    QMenu::item:selected {{
        background-color: {c['accent']};
        color: #ffffff;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background-color: {c['bg_dark']};
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {c['fg_muted']};
        min-height: 20px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {c['accent']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background-color: {c['bg_dark']};
        height: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {c['fg_muted']};
        min-width: 20px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {c['accent']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* Status Bar */
    QStatusBar {{
        background-color: {c['status_bg']};
        color: {c['status_fg']};
    }}
    """
