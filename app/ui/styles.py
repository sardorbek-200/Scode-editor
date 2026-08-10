"""
Scode Editor — VS Code Dark+ Professional QSS Design System
"""

VS_CODE_DARK_QSS = """
/* ===================================================================
   Scode Editor — VS Code Dark+ Professional Theme
   =================================================================== */

/* Global Defaults */
QWidget {
    background-color: #1e1e1e;
    color: #cccccc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 12px;
    selection-background-color: #264f78;
    selection-color: #ffffff;
}

QMainWindow, QDialog {
    background-color: #1e1e1e;
}

/* Top Header & Toolbar Panels */
QWidget#topBarPanel, QWidget#headerPanel {
    background-color: #252526;
    border-bottom: 1px solid #2d2d2d;
}

/* Splitter Styling */
QSplitter::handle {
    background-color: #2d2d2d;
}
QSplitter::handle:horizontal {
    width: 1px;
}
QSplitter::handle:vertical {
    height: 1px;
}
QSplitter::handle:hover {
    background-color: #007acc;
}

/* Labels */
QLabel {
    background-color: transparent;
    color: #cccccc;
    font-size: 12px;
}
QLabel#headerTitle {
    color: #ffffff;
    font-size: 15px;
    font-weight: 600;
}
QLabel#subText, QLabel#breadcrumbPath {
    color: #969696;
    font-size: 11px;
}

/* Input Fields (QLineEdit, QTextEdit, QPlainTextEdit) */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #1c1c1c;
    color: #cccccc;
    border: 1px solid #2d2d2d;
    border-radius: 2px;
    padding: 5px 8px;
    font-size: 12px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #007acc;
    background-color: #1e1e1e;
}

/* Code & Terminal Monospace Inputs */
QLineEdit#terminalInput, QTextEdit#terminalOutput {
    font-family: "Cascadia Code", "Fira Code", Consolas, "Courier New", monospace;
    font-size: 12px;
}

/* Standard Buttons */
QPushButton {
    background-color: #0e639c;
    color: #ffffff;
    border: 1px solid transparent;
    border-radius: 2px;
    padding: 5px 14px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #1177bb;
}
QPushButton:pressed {
    background-color: #094771;
}
QPushButton:disabled {
    background-color: #333333;
    color: #666666;
}

/* Secondary / Subtle Buttons */
QPushButton#secondaryBtn {
    background-color: #3c3c3c;
    color: #cccccc;
}
QPushButton#secondaryBtn:hover {
    background-color: #4a4a4a;
    color: #ffffff;
}

/* Flat Icon Buttons (Terminal & Toolbar Actions) */
QPushButton.flat-icon-btn, QPushButton#iconBtn {
    background-color: transparent;
    color: #cccccc;
    border: none;
    border-radius: 3px;
    padding: 4px 8px;
    font-size: 11px;
}
QPushButton.flat-icon-btn:hover, QPushButton#iconBtn:hover {
    background-color: #2a2d2e;
    color: #ffffff;
}
QPushButton.flat-icon-btn:pressed, QPushButton#iconBtn:pressed {
    background-color: #37373d;
}

/* QTabWidget & QTabBar Minimalist VS Code Tabs */
QTabWidget {
    background-color: #1e1e1e;
    border: none;
}
QTabWidget::pane {
    border: none;
    top: 0px;
    background-color: #1e1e1e;
}
QTabBar {
    background-color: #252526;
    border-bottom: 1px solid #2d2d2d;
    qproperty-drawBase: 0;
}
QTabBar::tab {
    background-color: #2d2d2d;
    color: #969696;
    height: 32px;
    padding: 0 12px;
    border: none;
    border-right: 1px solid #252526;
    min-width: 90px;
    font-size: 12px;
}
QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #ffffff;
    border-top: 2px solid #007acc;
}
QTabBar::tab:hover:!selected {
    background-color: #2a2d2e;
    color: #cccccc;
}

/* QTabBar Close Button (X Tugmasi) */
QTabBar::close-button {
    image: none;
    subcontrol-position: right;
    margin-right: 4px;
}
QTabBar::close-button:hover {
    background-color: #e81123;
    border-radius: 2px;
}

/* Tree View (File Explorer) */
QTreeView {
    background-color: #181818;
    color: #cccccc;
    border: none;
    outline: 0;
    font-size: 12px;
}
QTreeView::item {
    height: 24px;
    padding: 2px 4px;
    border: none;
}
QTreeView::item:hover {
    background-color: #2a2d2e;
    color: #ffffff;
}
QTreeView::item:selected {
    background-color: #37373d;
    color: #ffffff;
}
QTreeView::item:selected:!active {
    background-color: #2d2d2d;
    color: #cccccc;
}

/* Menus & Popups */
QMenu {
    background-color: #252526;
    color: #cccccc;
    border: 1px solid #2d2d2d;
    padding: 4px;
    border-radius: 4px;
}
QMenu::item {
    padding: 6px 20px 6px 12px;
    border-radius: 2px;
    font-size: 12px;
}
QMenu::item:selected {
    background-color: #04395e;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background-color: #2d2d2d;
    margin: 4px 8px;
}

/* ScrollBars (VS Code Minimalist Dark) */
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background-color: #424242;
    min-height: 20px;
    border-radius: 3px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background-color: #4f4f4f;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 10px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background-color: #424242;
    min-width: 20px;
    border-radius: 3px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #4f4f4f;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}

/* Tooltips */
QToolTip {
    background-color: #252526;
    color: #cccccc;
    border: 1px solid #2d2d2d;
    padding: 4px 8px;
    border-radius: 3px;
    font-size: 11px;
}

/* Status Bar */
QStatusBar {
    background-color: #007acc;
    color: #ffffff;
    font-size: 11px;
}

/* Search Panel */
QWidget#searchPanel {
    background-color: #252526;
    border-bottom: 1px solid #2d2d2d;
}
"""


def get_app_stylesheet() -> str:
    """Retorna o stylesheet QSS completo no tema VS Code Dark+."""
    return VS_CODE_DARK_QSS
