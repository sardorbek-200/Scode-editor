import os
import re
import html
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
)
from PyQt6.QtGui import QCursor, QTextCursor
from PyQt6.QtCore import Qt, QProcess, QSize

from app.utils.icon_manager import IconManager


class CommandLineEdit(QLineEdit):
    """
    Buyruqlar tarixini (History) ↑ va ↓ yo'nalish tugmalari orqali boshqaruvchi QLineEdit.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []
        self.history_index = -1

    def add_to_history(self, cmd: str):
        if cmd and (not self.history or self.history[-1] != cmd):
            self.history.append(cmd)
        self.history_index = len(self.history)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            if self.history and self.history_index > 0:
                self.history_index -= 1
                self.setText(self.history[self.history_index])
            return
        elif event.key() == Qt.Key.Key_Down:
            if self.history and self.history_index < len(self.history) - 1:
                self.history_index += 1
                self.setText(self.history[self.history_index])
            elif self.history_index >= len(self.history) - 1:
                self.history_index = len(self.history)
                self.clear()
            return
        super().keyPressEvent(event)


class TerminalPanel(QWidget):
    """
    Professional Integratsiyalashgan Terminal Paneli.
    ANSI Ranglar, Avto-skroll, Buyruqlar tarixi (History) va UTF-8 QProcess boshqaruvi bilan.
    """

    def __init__(self, parent=None, project_path=None):
        super().__init__(parent)
        self.project_path = project_path or os.getcwd()
        self.process = None

        self._build_ui()
        self._init_process()

    def _build_ui(self):
        self.setMinimumHeight(120)
        self.setStyleSheet("""
            QWidget {
                background-color: #181818;
                color: #cccccc;
            }
            QWidget#terminalHeader {
                background-color: #252526;
                border-top: 1px solid #2d2d2d;
                border-bottom: 1px solid #2d2d2d;
            }
            QLabel#terminalTitle {
                color: #cccccc;
                font-weight: bold;
                font-size: 11px;
            }
            QLabel#terminalPath {
                color: #777777;
                font-size: 11px;
            }
            QTextEdit {
                background-color: #181818;
                color: #cccccc;
                border: none;
                font-family: "Cascadia Code", "Fira Code", Consolas, "Courier New", monospace;
                font-size: 10pt;
                padding: 6px;
            }
            QLineEdit {
                background-color: #181818;
                color: #ffffff;
                border: none;
                border-top: 1px solid #2d2d2d;
                padding: 6px 8px;
                font-family: "Cascadia Code", "Fira Code", Consolas, "Courier New", monospace;
                font-size: 10pt;
            }
            QPushButton {
                background-color: transparent;
                color: #cccccc;
                border: none;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2a2d2e;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #37373d;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Yuqori ixcham sarlavha paneli
        header_widget = QWidget()
        header_widget.setObjectName("terminalHeader")
        top_layout = QHBoxLayout(header_widget)
        top_layout.setContentsMargins(8, 4, 8, 4)
        top_layout.setSpacing(8)

        # Terminal SVG ikonkasi
        terminal_icon_label = QLabel()
        terminal_icon_label.setPixmap(IconManager.get_pixmap("terminal", 16, 16))
        top_layout.addWidget(terminal_icon_label)

        self.title_label = QLabel("TERMINAL")
        self.title_label.setObjectName("terminalTitle")
        top_layout.addWidget(self.title_label)

        self.path_label = QLabel(f"[{self.project_path}]")
        self.path_label.setObjectName("terminalPath")
        top_layout.addWidget(self.path_label, 1)

        # SVG Tozalash va To'xtatish tugmalari (flat icon button)
        clear_btn = QPushButton(" Tozalash")
        clear_btn.setIcon(IconManager.get_icon("clear"))
        clear_btn.setIconSize(QSize(14, 14))
        clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        clear_btn.clicked.connect(self.clear_output)
        top_layout.addWidget(clear_btn)

        kill_btn = QPushButton(" To'xtatish")
        kill_btn.setIcon(IconManager.get_icon("stop"))
        kill_btn.setIconSize(QSize(14, 14))
        kill_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        kill_btn.clicked.connect(self.stop_process)
        top_layout.addWidget(kill_btn)

        layout.addWidget(header_widget)

        # 2. Chiqish oynasi (QTextEdit) va Input maydoni (CommandLineEdit)
        console_container = QVBoxLayout()
        console_container.setSpacing(0)
        console_container.setContentsMargins(0, 0, 0, 0)

        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.output_area.setPlaceholderText("Buyruq loglari va konsol chiqishi bu yerda ko'rinadi...")
        console_container.addWidget(self.output_area, 1)

        # Buyruq kiritish input box ($ prompti bilan)
        input_container = QHBoxLayout()
        input_container.setSpacing(0)
        input_container.setContentsMargins(0, 0, 0, 0)

        prompt_label = QLabel(" $ ")
        prompt_label.setStyleSheet("""
            background-color: #181818;
            color: #23d160;
            font-family: "Cascadia Code", "Fira Code", Consolas, "Courier New", monospace;
            font-size: 10pt;
            font-weight: bold;
            border-top: 1px solid #2d2d2d;
            padding-left: 6px;
        """)
        input_container.addWidget(prompt_label)

        self.input_line = CommandLineEdit(self)
        self.input_line.setPlaceholderText("Buyruq kiriting (masalan: python main.py, dir, npm start)... (Tarix uchun ↑ / ↓)")
        self.input_line.returnPressed.connect(self.run_command)
        input_container.addWidget(self.input_line, 1)

        console_container.addLayout(input_container)

        layout.addLayout(console_container, 1)

    def _init_process(self):
        """QProcess jarayonini sozlash"""
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._handle_finished)

    def set_project_path(self, path: str):
        if path and os.path.exists(path):
            self.project_path = path
            self.path_label.setText(f"[{self.project_path}]")

    def _append_html_and_scroll(self, html_text: str):
        """Matnni HTML formatida qo'shish va avtomatik ravishda eng pastga skroll qilish"""
        self.output_area.append(html_text)
        self.output_area.moveCursor(QTextCursor.MoveOperation.End)
        self.output_area.ensureCursorVisible()

    @staticmethod
    def ansi_to_html(text: str) -> str:
        """ANSI escape rang kodlarini HTML / RichText formatiga o'tkazish"""
        if not text:
            return ""

        escaped = html.escape(text)

        ansi_colors = {
            '30': '#000000', '31': '#f44747', '32': '#23d160', '33': '#e5c07b',
            '34': '#569cd6', '35': '#c586c0', '36': '#4ec9b0', '37': '#cccccc',
            '90': '#777777', '91': '#f48771', '92': '#4ec9b0', '93': '#f5d76e',
            '94': '#569cd6', '95': '#c586c0', '96': '#4ec9b0', '97': '#ffffff'
        }

        def _replace_ansi(match):
            codes = match.group(1).split(';')
            styles = []
            for code in codes:
                if code == '0' or code == '':
                    return '</span>'
                elif code in ansi_colors:
                    styles.append(f'color: {ansi_colors[code]}')
                elif code == '1':
                    styles.append('font-weight: bold')
                elif code == '4':
                    styles.append('text-decoration: underline')
            if styles:
                style_str = "; ".join(styles)
                return f'<span style="{style_str}">'
            return ''

        # Barcha rang bo'lmagan boshqaruv belgilarni olib tashlash (\x1b[K, \x1b[2J va h.k.)
        cleaned = re.sub(r'\x1b\[[0-9;]*[a-zA-D-z]', '', escaped)
        # SGR rang kodlarini HTML span teglari bilan almashtirish
        result = re.sub(r'\x1b\[([0-9;]*)m', _replace_ansi, cleaned)
        return result

    def execute_command(self, cmd: str):
        """Tashqi vidjetdan buyruq yuborilganda bajarish (▶ Run tugmasi)"""
        if not cmd:
            return
        self.input_line.setText(cmd)
        self.run_command()

    def run_command(self):
        """Enter bosilganda buyruqni bajarish va tarixga saqlash"""
        cmd = self.input_line.text().strip()
        if not cmd:
            return

        # Tarixga saqlash va inputni tozalash
        self.input_line.add_to_history(cmd)
        self.input_line.clear()

        if cmd.lower() in ["cls", "clear"]:
            self.clear_output()
            return

        # Buyruqni terminal oynasida ko'k/sariq rangda chiqarish ($ npm i)
        cmd_html = f"<span style='color: #4ec9b0; font-weight: bold;'>$ {html.escape(cmd)}</span>"
        self._append_html_and_scroll(cmd_html)

        if self.process.state() != QProcess.ProcessState.NotRunning:
            self._append_html_and_scroll("<span style='color: #e5c07b;'>Boshqa jarayon bajarilmoqda. Uni to'xtatish uchun 'To'xtatish' tugmasini bosing.</span>")
            return

        self.process.setWorkingDirectory(self.project_path)

        # Standart Shell orqali buyruqni berish
        if os.name == 'nt':
            self.process.start("cmd.exe", ["/c", cmd])
        else:
            self.process.start("sh", ["-c", cmd])

    def _handle_stdout(self):
        data = self.process.readAllStandardOutput().data()
        text = self._decode_output(data)
        if text.strip():
            formatted_html = self.ansi_to_html(text.rstrip("\r\n"))
            self._append_html_and_scroll(formatted_html)

    def _handle_stderr(self):
        data = self.process.readAllStandardError().data()
        text = self._decode_output(data)
        if text.strip():
            formatted = self.ansi_to_html(text.rstrip("\r\n"))
            err_html = f"<span style='color: #f48771;'>{formatted}</span>"
            self._append_html_and_scroll(err_html)

    def _handle_finished(self, exit_code, exit_status):
        self._append_html_and_scroll(f"<span style='color: #6a9955;'><i>[Jarayon yakunlandi (Exit code: {exit_code})]</i></span>")

    def _decode_output(self, data: bytes) -> str:
        if not data:
            return ""
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            try:
                return data.decode("cp866", errors="ignore")
            except Exception:
                return data.decode("latin-1", errors="replace")

    def clear_output(self):
        self.output_area.clear()

    def stop_process(self):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self._append_html_and_scroll("<span style='color: #f44747;'><b>⛔ Jarayon majburiy to'xtatildi!</b></span>")
