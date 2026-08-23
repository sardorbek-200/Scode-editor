import json
import subprocess
from dataclasses import dataclass
from typing import List, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


@dataclass
class LintIssue:
    file: str
    line: int
    column: int
    code: str
    message: str
    severity: str = "error"

    @property
    def start_line(self) -> int:
        return max(0, self.line - 1)

    @property
    def start_column(self) -> int:
        return max(0, self.column - 1)


class LintWorker(QObject):
    """Background lint worker. Uses ruff if available, falls back to flake8."""

    finished = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, file_path: str = ""):
        super().__init__()
        self.file_path = file_path

    def run(self, code: str, file_path: str = ""):
        path = file_path or self.file_path
        try:
            issues = self._lint_code(code, path)
            self.finished.emit(issues)
        except Exception as exc:
            self.failed.emit(str(exc))

    def _lint_code(self, code: str, file_path: str) -> List[LintIssue]:
        issues: List[LintIssue] = []

        for cmd in self._build_commands(file_path):
            try:
                proc = subprocess.run(
                    cmd,
                    input=code,
                    text=True,
                    capture_output=True,
                    timeout=15,
                    check=False,
                )
                if proc.returncode in (0, 1):
                    payload = proc.stdout.strip() or proc.stderr.strip()
                    if not payload:
                        return issues
                    parsed = self._parse_output(payload)
                    if parsed:
                        return parsed
                if proc.stderr.strip():
                    raise RuntimeError(proc.stderr.strip())
            except FileNotFoundError:
                continue
            except Exception:
                continue

        return issues

    def _build_commands(self, file_path: str):
        commands = []
        if file_path:
            commands.append(["ruff", "check", "--output-format=json", "--stdin-filename", file_path, "-"])
            commands.append(["ruff", "check", "--output-format=json", "-"])
        else:
            commands.append(["ruff", "check", "--output-format=json", "-"])

        commands.append(["flake8", "-", "--format=%(row)d:%(col)d:%(code)s:%(text)s"])
        return commands

    def _parse_output(self, payload: str) -> List[LintIssue]:
        issues: List[LintIssue] = []

        try:
            data = json.loads(payload)
            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    location = item.get("location", {})
                    row = int(location.get("row", 1) or 1)
                    col = int(location.get("column", 1) or 1)
                    issue = LintIssue(
                        file=item.get("filename") or "",
                        line=row,
                        column=col,
                        code=str(item.get("code") or "E999"),
                        message=str(item.get("message") or "Lint error"),
                        severity=str(item.get("level") or "error").lower(),
                    )
                    issues.append(issue)
                return issues
        except json.JSONDecodeError:
            pass

        for line in payload.splitlines():
            if not line or ":" not in line:
                continue
            parts = line.split(":", 3)
            if len(parts) < 4:
                continue
            try:
                row = int(parts[0].strip())
                col = int(parts[1].strip())
                code = parts[2].strip()
                message = parts[3].strip()
                issues.append(LintIssue(file="", line=row, column=col, code=code, message=message, severity="error"))
            except Exception:
                continue

        return issues


class LiveLinter(QObject):
    """Debounced, background linting controller for the editor."""

    issuesChanged = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._run_lint)
        self._current_job = None
        self._file_path = ""
        self._code = ""

    def schedule(self, file_path: str, code: str):
        self._file_path = file_path
        self._code = code
        self._timer.start()

    def _run_lint(self):
        if not self._code:
            self.issuesChanged.emit([])
            return

        worker = LintWorker(self._file_path)
        worker.finished.connect(self._on_finished)
        worker.failed.connect(self._on_failed)
        self._current_job = worker
        worker.run(self._code, self._file_path)

    def _on_finished(self, issues):
        self.issuesChanged.emit(issues or [])
        if self._current_job:
            self._current_job.deleteLater()
            self._current_job = None

    def _on_failed(self, _message):
        self.issuesChanged.emit([])
        if self._current_job:
            self._current_job.deleteLater()
            self._current_job = None
