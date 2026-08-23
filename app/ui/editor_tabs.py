import os
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QSplitter,
    QPushButton,
    QMenu,
    QTabBar,
    QSizePolicy,
)
from PyQt6.QtGui import QAction, QIcon, QCursor


class EditorTabWidget(QTabWidget):
    """
    Tepadagi tugmalar (Split Vertical / Split Horizontal) va context menu
    funksionalligiga ega bo'lgan moslashtirilgan QTabWidget.
    """

    split_requested = pyqtSignal(str)  # 'vertical' yoki 'horizontal'
    split_tab_requested = pyqtSignal(int, str)  # (tab_index, 'right' yoki 'down')
    close_split_requested = pyqtSignal()
    close_tab_requested_signal = pyqtSignal(int)

    def __init__(self, is_secondary: bool = False, parent=None):
        super().__init__(parent)
        self.is_secondary = is_secondary
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabBar().setMovable(True)
        self.setMinimumWidth(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Context Menu ni yoqish
        self.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self._show_context_menu)
        self.tabCloseRequested.connect(self._handle_tab_close)

        # Yuqori o'ng burchak tugmalarini yaratish (Faqat asosiy tab bo'lsa)
        if not is_secondary:
            self._setup_corner_buttons()

    def _setup_corner_buttons(self):
        """Yuqori o'ng burchakka Split Vertical va Split Horizontal tugmalarini qo'shish"""
        corner_widget = QWidget()
        layout = QHBoxLayout(corner_widget)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(2)

        btn_split_vert = QPushButton(" 🗁 ")
        btn_split_vert.setToolTip("Split Vertical (Yonma-yon bo'lish)")
        btn_split_vert.setFixedSize(24, 22)
        btn_split_vert.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_split_vert.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #cccccc;
                border: none;
                font-size: 13px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2d2d2d;
                color: #ffffff;
            }
        """)
        btn_split_vert.clicked.connect(lambda: self.split_requested.emit("vertical"))
        layout.addWidget(btn_split_vert)

        btn_split_horiz = QPushButton(" 🗇 ")
        btn_split_horiz.setToolTip("Split Horizontal (Ustma-ust bo'lish)")
        btn_split_horiz.setFixedSize(24, 22)
        btn_split_horiz.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_split_horiz.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #cccccc;
                border: none;
                font-size: 13px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2d2d2d;
                color: #ffffff;
            }
        """)
        btn_split_horiz.clicked.connect(lambda: self.split_requested.emit("horizontal"))
        layout.addWidget(btn_split_horiz)

        self.setCornerWidget(corner_widget, Qt.Corner.TopRightCorner)

    def _handle_tab_close(self, index: int):
        self.close_tab_requested_signal.emit(index)

    def _show_context_menu(self, pos):
        """Sichqonchaning o'ng tugmasi bosilganda context menu chiqarish"""
        tab_bar = self.tabBar()
        tab_index = tab_bar.tabAt(pos)
        if tab_index < 0:
            return

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

        action_split_right = QAction("Split Right (O'ng tarafga bo'lish)", self)
        action_split_right.triggered.connect(lambda: self.split_tab_requested.emit(tab_index, "right"))
        menu.addAction(action_split_right)

        action_split_down = QAction("Split Down (Pastga bo'lish)", self)
        action_split_down.triggered.connect(lambda: self.split_tab_requested.emit(tab_index, "down"))
        menu.addAction(action_split_down)

        menu.addSeparator()

        action_close_split = QAction("Close Split (Bo'lingan oynani yopish)", self)
        action_close_split.triggered.connect(lambda: self.close_split_requested.emit())
        menu.addAction(action_close_split)

        menu.addSeparator()

        action_close_tab = QAction("Close Tab (Tabni yopish)", self)
        action_close_tab.triggered.connect(lambda: self._handle_tab_close(tab_index))
        menu.addAction(action_close_tab)

        action_close_others = QAction("Close Other Tabs (Boshqa tablarni yopish)", self)
        action_close_others.triggered.connect(lambda: self._close_other_tabs(tab_index))
        menu.addAction(action_close_others)

        menu.exec(tab_bar.mapToGlobal(pos))

    def _close_other_tabs(self, keep_index: int):
        for i in reversed(range(self.count())):
            if i != keep_index:
                self._handle_tab_close(i)


class EditorTabsManager(QWidget):
    """
    Split View (Yonma-yon va Ustma-ust oynalarni bo'lish) va mustaqil QTabWidget'larni
    boshqaruvchi asosiy konteyner vidjeti.
    """

    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # QSplitter orqali oynalarni bo'lish
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(2)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #2b2b2b;
            }
            QSplitter::handle:hover {
                background-color: #007acc;
            }
        """)

        # Birinchi (Asosiy) Tab Paneli
        self.primary_tabs = EditorTabWidget(is_secondary=False, parent=self)
        self.primary_tabs.split_requested.connect(self.split_view)
        self.primary_tabs.split_tab_requested.connect(self.split_tab)
        self.primary_tabs.close_split_requested.connect(self.close_split)
        self.primary_tabs.close_tab_requested_signal.connect(self._on_primary_tab_close)

        # Ikkinchi (Split) Tab Paneli
        self.secondary_tabs = EditorTabWidget(is_secondary=True, parent=self)
        self.secondary_tabs.setVisible(False)
        self.secondary_tabs.split_tab_requested.connect(self.split_tab)
        self.secondary_tabs.close_split_requested.connect(self.close_split)
        self.secondary_tabs.close_tab_requested_signal.connect(self._on_secondary_tab_close)

        self.splitter.addWidget(self.primary_tabs)
        self.splitter.addWidget(self.secondary_tabs)

        self.layout.addWidget(self.splitter)

    def split_view(self, mode: str = "vertical"):
        """Oynani yonma-yon (vertical) yoki ustma-ust (horizontal) bo'lish"""
        if mode == "vertical":
            self.splitter.setOrientation(Qt.Orientation.Horizontal)
        else:
            self.splitter.setOrientation(Qt.Orientation.Vertical)

        if not self.secondary_tabs.isVisible():
            self.secondary_tabs.setVisible(True)
            self.secondary_tabs.show()
            # Split nisbatini 50/50 qilish
            total = sum(self.splitter.sizes()) or 1000
            self.splitter.setSizes([total // 2, total // 2])

    def split_tab(self, tab_index: int, direction: str = "right"):
        """Ko'rsatilgan tabni ikkinchi oynaga o'tkazish yoki nusxalash"""
        source_tabs = self.primary_tabs
        if direction in ("right", "vertical"):
            self.split_view("vertical")
        else:
            self.split_view("horizontal")

        if tab_index < 0 or tab_index >= source_tabs.count():
            return

        widget = source_tabs.widget(tab_index)
        title = source_tabs.tabText(tab_index)
        tooltip = source_tabs.tabToolTip(tab_index)

        # Tabni ikkinchi pane'ga ko'chirish
        source_tabs.removeTab(tab_index)
        new_idx = self.secondary_tabs.addTab(widget, title)
        self.secondary_tabs.setTabToolTip(new_idx, tooltip)
        self.secondary_tabs.setCurrentIndex(new_idx)

    def close_split(self):
        """Bo'lingan ikkinchi oynani yopish va barcha tablarni asosiy panelga qaytarish"""
        if not self.secondary_tabs.isVisible():
            return

        while self.secondary_tabs.count() > 0:
            widget = self.secondary_tabs.widget(0)
            title = self.secondary_tabs.tabText(0)
            tooltip = self.secondary_tabs.tabToolTip(0)
            self.secondary_tabs.removeTab(0)

            new_idx = self.primary_tabs.addTab(widget, title)
            self.primary_tabs.setTabToolTip(new_idx, tooltip)

        self.secondary_tabs.setVisible(False)

    def _on_primary_tab_close(self, index: int):
        widget = self.primary_tabs.widget(index)
        self.primary_tabs.removeTab(index)
        if widget:
            widget.deleteLater()

    def _on_secondary_tab_close(self, index: int):
        widget = self.secondary_tabs.widget(index)
        self.secondary_tabs.removeTab(index)
        if widget:
            widget.deleteLater()

        # Agar ikkinchi pane-da hech qanday tab qolmasa, splitni avtomatik yopish
        if self.secondary_tabs.count() == 0:
            self.close_split()
