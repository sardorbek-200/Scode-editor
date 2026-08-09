import os
import subprocess
import sys

from PyQt6.QtCore import QThread, pyqtSignal


class PackageInstallerThread(QThread):
    """Loyiha bog'liqliklarini orqa fonda o'rnatish uchun QThread."""

    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, project_path: str, parent=None):
        super().__init__(parent)
        self.project_path = project_path

    def run(self) -> None:
        try:
            if not self.project_path or not os.path.exists(self.project_path):
                self.finished_signal.emit(False, "Loyiha papkasi topilmadi.")
                return

            command = self._build_command()
            if not command:
                self.finished_signal.emit(False, "Hech qanday o'rnatish fayli topilmadi.")
                return

            self.output_signal.emit(f"Ishga tushirilmoqda: {' '.join(command)}")
            process = subprocess.Popen(
                command,
                cwd=self.project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                shell=False,
            )

            output_lines = []
            while True:
                line = process.stdout.readline()
                if line:
                    text = line.rstrip()
                    if text:
                        self.output_signal.emit(text)
                        output_lines.append(text)
                if process.poll() is not None and not line:
                    break

            exit_code = process.returncode
            if exit_code == 0:
                self.finished_signal.emit(True, "Bog'liqliklar muvaffaqiyatli o'rnatildi.")
            else:
                self.finished_signal.emit(False, f"O'rnatish muvaffaqiyatsiz tugadi (exit code: {exit_code}).")
        except Exception as exc:
            self.finished_signal.emit(False, f"O'rnatish xatosi: {exc}")

    def _build_command(self):
        requirements_path = os.path.join(self.project_path, "requirements.txt")
        if os.path.exists(requirements_path):
            return [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]

        package_json_path = os.path.join(self.project_path, "package.json")
        if os.path.exists(package_json_path):
            npm_command = "npm.cmd" if os.name == "nt" else "npm"
            return [npm_command, "install"]

        return None
