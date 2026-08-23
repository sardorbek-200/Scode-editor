import sys
import inspect
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QWidget,
    QLabel,
    QApplication,
    QMainWindow,
)


class CommandPaletteItemWidget(QWidget):
    """
    Command Palette ichidagi har bir buyruq varianti uchun custom vidjet.
    Chap tarafda buyruq nomi, o'ng tarafda esa u biriktirilgan shortcut (masalan Ctrl + S).
    """

    def __init__(self, title: str, shortcut_text: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        # Buyruq nomi
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #d4d4d4; font-size: 13px; font-weight: 500;")
        layout.addWidget(self.title_label, 1)

        # Klaviatura shortcut nishoni (Badge)
        if shortcut_text:
            self.shortcut_label = QLabel(shortcut_text)
            self.shortcut_label.setStyleSheet("""
                background-color: #333333;
                color: #569cd6;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 2px 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                font-weight: bold;
            """)
            layout.addWidget(self.shortcut_label, 0)


class CommandPaletteDialog(QDialog):
    """
    VS Code uslubidagi chiroyli, tezkor va barqaror Command Palette modal oynasi (Ctrl + Shift + P).
    """

    def __init__(self, commands: list[dict], parent=None):
        super().__init__(parent)
        self.commands = commands  # [{'name': ..., 'title': ..., 'shortcut': ..., 'func': ...}, ...]
        self.filtered_commands = list(commands)

        self.setWindowTitle("Command Palette")
        self.setFixedSize(620, 380)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        self._build_ui()
        self._populate_list()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1f1f1f;
                border: 1px solid #007acc;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 1. Qidiruv input maydoni
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buyruq nomini kiriting (masalan: Saqlash, Prettier, Terminal)...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #252526;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
        """)
        self.search_input.textChanged.connect(self._filter_commands)
        layout.addWidget(self.search_input)

        # 2. Buyruqlar ro'yxati (ListWidget)
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #181818;
                border: 1px solid #2d2d2d;
                border-radius: 6px;
                outline: none;
            }
            QListWidget::item {
                background-color: transparent;
                border-bottom: 1px solid #222222;
            }
            QListWidget::item:selected {
                background-color: #04395e;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
                border-radius: 4px;
            }
        """)
        self.list_widget.itemDoubleClicked.connect(self._on_item_executed)
        layout.addWidget(self.list_widget, 1)

        # Klaviaturani boshqarish
        self.search_input.installEventFilter(self)

    def _populate_list(self):
        self.list_widget.clear()
        for cmd in self.filtered_commands:
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 36))
            widget = CommandPaletteItemWidget(cmd['title'], cmd['shortcut'])
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _filter_commands(self, text: str):
        query = text.strip().lower()
        if not query:
            self.filtered_commands = list(self.commands)
        else:
            self.filtered_commands = [
                cmd for cmd in self.commands
                if query in cmd['title'].lower() or query in cmd['shortcut'].lower() or query in cmd['name'].lower()
            ]
        self._populate_list()

    def _on_item_executed(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self.filtered_commands):
            cmd = self.filtered_commands[row]
            self.accept()
            # Oyna yopilgach tanlangan metodni chaqirish
            cmd['func']()

    def eventFilter(self, obj, event):
        if obj == self.search_input and event.type() == event.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Down:
                cur_row = self.list_widget.currentRow()
                if cur_row < self.list_widget.count() - 1:
                    self.list_widget.setCurrentRow(cur_row + 1)
                return True
            elif key == Qt.Key.Key_Up:
                cur_row = self.list_widget.currentRow()
                if cur_row > 0:
                    self.list_widget.setCurrentRow(cur_row - 1)
                return True
            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._on_item_executed()
                return True
            elif key == Qt.Key.Key_Escape:
                self.reject()
                return True

        return super().eventFilter(obj, event)


class SmartKeyBindingAndPaletteMixin:
    """
    Scode Editor uchun Avtomatik Skanerlash, KeyDown/Shortcut biriktirish va VS Code
    uslubidagi Command Palette (Ctrl + Shift + P) mixin klassi.
    
    QQayta yaratilganda QShortcut to'qnashuvlari bo'lmasligi va har doim fokusda
    ishlashi uchun barqaror (singleton-style) shortcut biriktirish mexanizmi qo'shilgan.
    """

    KNOWN_COMMANDS_MAP = {
        'cmd_save_file': ('Ctrl+S', '💾 Faylni Saqlash (Save File)'),
        'save_current_file': ('Ctrl+S', '💾 Faylni Saqlash (Save File)'),
        'cmd_format_code': ('Ctrl+Shift+I', '✨ Kodni Formatlash (Universal Prettier)'),
        'format_code': ('Ctrl+Shift+I', '✨ Kodni Formatlash (Universal Prettier)'),
        'cmd_quick_open': ('Ctrl+P', '🔍 Tezkor Fayl Ochish (Quick Open)'),
        'open_quick_open_dialog': ('Ctrl+P', '🔍 Tezkor Fayl Ochish (Quick Open)'),
        'cmd_command_palette': ('Ctrl+Shift+P', '⚡ Command Palette (Buyruqlar Ro\'yxati)'),
        'open_command_palette': ('Ctrl+Shift+P', '⚡ Command Palette (Buyruqlar Ro\'yxati)'),
        'cmd_goto_line': ('Ctrl+G', '🎯 Qatorga O\'tish (Go to Line)'),
        'show_goto_line_dialog': ('Ctrl+G', '🎯 Qatorga O\'tish (Go to Line)'),
        'cmd_find_in_file': ('Ctrl+F', '🔎 Matn Qidirish (Find)'),
        'show_find_dialog': ('Ctrl+F', '🔎 Matn Qidirish (Find)'),
        'cmd_replace_in_file': ('Ctrl+H', '🔄 Matnni Almashtirish (Replace)'),
        'show_replace_dialog': ('Ctrl+H', '🔄 Matnni Almashtirish (Replace)'),
        'cmd_select_next_occurrence': ('Ctrl+D', '🔤 So\'zni Tanlash / Multi-Cursor (Select Word)'),
        'select_next_occurrence': ('Ctrl+D', '🔤 So\'zni Tanlash / Multi-Cursor (Select Word)'),
        'cmd_insert_line_below': ('Ctrl+Return', '⤵ Pastdan Qator Ochish (Insert Line Below)'),
        'insert_line_below': ('Ctrl+Return', '⤵ Pastdan Qator Ochish (Insert Line Below)'),
        'cmd_insert_line_above': ('Ctrl+Shift+Return', '⤴ Yuqoridan Qator Ochish (Insert Line Above)'),
        'insert_line_above': ('Ctrl+Shift+Return', '⤴ Yuqoridan Qator Ochish (Insert Line Above)'),
        'cmd_delete_current_line': ('Ctrl+Shift+K', '❌ Qatorni O\'chirish (Delete Line)'),
        'delete_current_line': ('Ctrl+Shift+K', '❌ Qatorni O\'chirish (Delete Line)'),
        'cmd_move_line_up': ('Alt+Up', '⬆ Qatorni Yuqoriga Surish (Move Line Up)'),
        'move_line_up': ('Alt+Up', '⬆ Qatorni Yuqoriga Surish (Move Line Up)'),
        'cmd_move_line_down': ('Alt+Down', '⬇ Qatorni Pastga Surish (Move Line Down)'),
        'move_line_down': ('Alt+Down', '⬇ Qatorni Pastga Surish (Move Line Down)'),
        'cmd_duplicate_line_down': ('Shift+Alt+Down', '📑 Qatorni Nusxalash (Duplicate Line)'),
        'duplicate_line_down': ('Shift+Alt+Down', '📑 Qatorni Nusxalash (Duplicate Line)'),
        'cmd_toggle_line_comment': ('Ctrl+/', '💬 Qatorli Izoh (Line Comment)'),
        'toggle_line_comment': ('Ctrl+/', '💬 Qatorli Izoh (Line Comment)'),
        'cmd_toggle_block_comment': ('Shift+Alt+A', '🗨 Blokli Izoh (Block Comment)'),
        'toggle_block_comment': ('Shift+Alt+A', '🗨 Blokli Izoh (Block Comment)'),
        'cmd_goto_matching_bracket': ('Ctrl+Shift+\\', '🔗 Juft Qavsga O\'tish (Matching Bracket)'),
        'goto_matching_bracket': ('Ctrl+Shift+\\', '🔗 Juft Qavsga O\'tish (Matching Bracket)'),
        'cmd_toggle_split': ('Ctrl+\\', '🔲 Oynani Bo\'lish / Split View'),
        'toggle_split_view': ('Ctrl+\\', '🔲 Oynani Bo\'lish / Split View'),
        'cmd_open_external_terminal': ('Ctrl+Shift+T', '💻 Tashqi Terminalni Ochish (External Terminal)'),
        'open_external_terminal': ('Ctrl+Shift+T', '💻 Tashqi Terminalni Ochish (External Terminal)'),
        'cmd_toggle_sidebar': ('Ctrl+B', '📂 Sidebar Paneli (Toggle Sidebar)'),
        'toggle_sidebar': ('Ctrl+B', '📂 Sidebar Paneli (Toggle Sidebar)'),
        'cmd_close_tab': ('Ctrl+W', '✖ Tabni Yopish (Close Tab)'),
        'close_current_tab': ('Ctrl+W', '✖ Tabni Yopish (Close Tab)'),
        'cmd_next_tab': ('Ctrl+Tab', '▶ Keyingi Tab (Next Tab)'),
        'next_tab': ('Ctrl+Tab', '▶ Keyingi Tab (Next Tab)'),
        'cmd_prev_tab': ('Ctrl+Shift+Tab', '◀ Oldingi Tab (Prev Tab)'),
        'prev_tab': ('Ctrl+Shift+Tab', '◀ Oldingi Tab (Prev Tab)'),
        'cmd_run_active_file': ('Ctrl+F5', '▶ Kodni Ishga Tushirish (Run File)'),
        'run_active_file': ('Ctrl+F5', '▶ Kodni Ishga Tushirish (Run File)'),
        'cmd_open_git': ('Ctrl+Shift+G', '🌿 Git Panelini Ochish (Git Manager)'),
        'open_git_dialog': ('Ctrl+Shift+G', '🌿 Git Panelini Ochish (Git Manager)'),
        'cmd_open_settings': ('Ctrl+,', '⚙ Sozlamalar (Settings)'),
        'open_settings_dialog': ('Ctrl+,', '⚙ Sozlamalar (Settings)'),
        '_handle_back': ('Alt+Left', '⬅ Loyihalarga Qarash (Back to Projects)'),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._registered_commands = []
        self._shortcuts = []

        # Dastlabki bir marta avtomatik skanerlash va shortcut'larni joylash
        self._scan_and_bind_commands()

    def _scan_and_bind_commands(self):
        """
        Metodlarni skanerlaydi hamda har bir shortcutni xavfsiz holatda biriktiradi.
        Oldingi QShortcut obyektlarini to'liq tozalanib, ziddiyat (Ambiguous Shortcut) oldi olinadi.
        """
        # Eski QShortcut obyektlarini xavfsiz tozalash
        if hasattr(self, '_shortcuts') and self._shortcuts:
            for sc in self._shortcuts:
                try:
                    sc.setEnabled(False)
                    sc.setParent(None)
                    sc.deleteLater()
                except Exception:
                    pass
            self._shortcuts.clear()
        else:
            self._shortcuts = []

        self._registered_commands.clear()
        registered_titles = set()

        # Metodlarni skanerlash
        methods = inspect.getmembers(self, predicate=inspect.ismethod)

        for name, method in methods:
            if name.startswith('__') and name.endswith('__'):
                continue

            shortcut_str = ""
            title = ""

            if name in self.KNOWN_COMMANDS_MAP:
                shortcut_str, title = self.KNOWN_COMMANDS_MAP[name]
            else:
                if name.startswith('cmd_'):
                    title = name[4:].replace('_', ' ').title()
                elif hasattr(method, '_command_title'):
                    title = getattr(method, '_command_title')
                    shortcut_str = getattr(method, '_command_shortcut', '')

            if title or shortcut_str:
                if not title:
                    title = name.replace('_', ' ').title()

                if title in registered_titles:
                    continue
                registered_titles.add(title)

                # QShortcut obyektini xavfsiz o'rnatish
                if shortcut_str and isinstance(self, QWidget):
                    try:
                        q_shortcut = QShortcut(QKeySequence(shortcut_str), self)
                        q_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
                        q_shortcut.activated.connect(method)
                        self._shortcuts.append(q_shortcut)
                    except Exception as exc:
                        print(f"Shortcut biriktirishda xatolik ({shortcut_str}): {exc}")
                
                self._registered_commands.append({
                    'name': name,
                    'title': title,
                    'shortcut': shortcut_str,
                    'func': method
                })

        # Ctrl + Shift + P Command Palette shortcut'ini doimiy faol saqlash
        if not any(c['name'] in ('open_command_palette', 'cmd_command_palette') for c in self._registered_commands):
            if isinstance(self, QWidget):
                try:
                    cmd_palette_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
                    cmd_palette_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
                    cmd_palette_shortcut.activated.connect(self.open_command_palette)
                    self._shortcuts.append(cmd_palette_shortcut)
                except Exception:
                    pass
            self._registered_commands.append({
                'name': 'cmd_command_palette',
                'title': "⚡ Command Palette (Buyruqlar Ro'yxati)",
                'shortcut': 'Ctrl+Shift+P',
                'func': self.open_command_palette
            })

    def open_command_palette(self):
        """
        VS Code uslubidagi Command Palette oynasini (Ctrl + Shift + P) ochish.
        """
        # Shortcut'larni qayta yaratmasdan, faqat dinamik ro'yxatni tekshirish
        if not self._registered_commands:
            self._scan_and_bind_commands()

        dialog = CommandPaletteDialog(self._registered_commands, parent=self if isinstance(self, QWidget) else None)
        dialog.exec()

        # Oyna yopilgach, fokusni redaktor oynasiga xavfsiz qaytarish
        if isinstance(self, QWidget):
            try:
                self.setFocus()
            except Exception:
                pass
            if hasattr(self, 'get_current_editor'):
                try:
                    res = self.get_current_editor()
                    editor = res[0] if isinstance(res, tuple) else res
                    if editor and hasattr(editor, 'setFocus') and callable(editor.setFocus):
                        editor.setFocus()
                except Exception:
                    pass

