import os
import re
import subprocess

class ProjectInspector:
    @staticmethod
    def inspect(project_path):
        return {
            "path": project_path,
            "name": os.path.basename(project_path),
            "git_branch": ProjectInspector.get_git_branch(project_path),
            "venv_path": ProjectInspector.get_venv(project_path),
            "version": ProjectInspector.get_version(project_path),
            "icon": ProjectInspector.get_icon(project_path)
        }

    @staticmethod
    def get_git_branch(path):
        """Git repository va joriy branch'ni aniqlash"""
        git_head = os.path.join(path, ".git", "HEAD")
        if os.path.exists(git_head):
            try:
                with open(git_head, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content.startswith("ref: refs/heads/"):
                        return content.replace("ref: refs/heads/", "")
            except Exception:
                pass
        return None

    @staticmethod
    def get_venv(path):
        """Virtualenv bor-yo'qligini aniqlash (venv, .venv, env)"""
        candidates = ["venv", ".venv", "env"]
        for c in candidates:
            venv_python = os.path.join(path, c, "Scripts", "python.exe")  # Windows uchun
            if os.path.exists(venv_python):
                return venv_python
        return None

    @staticmethod
    def get_version(path):
        """Loyiha versiyasini setup.py, pyproject.toml yoki package.json'dan qidirish"""
        # 1. pyproject.toml
        pyproject = os.path.join(path, "pyproject.toml")
        if os.path.exists(pyproject):
            try:
                with open(pyproject, "r", encoding="utf-8") as f:
                    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', f.read())
                    if match:
                        return match.group(1)
            except Exception:
                pass

        # 2. setup.py
        setup_py = os.path.join(path, "setup.py")
        if os.path.exists(setup_py):
            try:
                with open(setup_py, "r", encoding="utf-8") as f:
                    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', f.read())
                    if match:
                        return match.group(1)
            except Exception:
                pass

        return "0.1.0" # Defolt versiya

    @staticmethod
    def get_icon(path):
        """Loyiha ichida favicon.ico, icon.png yoki logo.png borligini tekshirish"""
        for img in ["icon.png", "logo.png", "favicon.ico", "assets/icon.png"]:
            full_path = os.path.join(path, img)
            if os.path.exists(full_path):
                return full_path
        return None