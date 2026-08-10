import os
import json
import hashlib
import shutil

from app.utils.paths import get_app_data_dir, get_projects_dir, get_icons_dir


class ConfigManager:
    """
    Tizim AppData papkasida loyiha sozlamalari va keshlarni saqlovchi menejer.
    """

    def __init__(self):
        self.app_data_dir = get_app_data_dir()
        self.projects_dir = get_projects_dir()
        self.icons_dir = get_icons_dir()

        self.index_file = os.path.join(self.app_data_dir, 'index.json')

    def _get_project_id(self, project_path):
        normalized_path = os.path.normpath(project_path).lower()
        return hashlib.md5(normalized_path.encode('utf-8')).hexdigest()

    def save_custom_icon(self, project_path, source_icon_path):
        """Foydalanuvchi tanlagan ikonkani assets/icons papkasiga nusxalash"""
        if not os.path.exists(source_icon_path):
            return None

        project_id = self._get_project_id(project_path)
        ext = os.path.splitext(source_icon_path)[1]
        dest_filename = f"{project_id}{ext}"
        dest_path = os.path.join(self.icons_dir, dest_filename)

        try:
            shutil.copy2(source_icon_path, dest_path)
            self.save_project_data(project_path, extra_data={"custom_icon": dest_path})
            return dest_path
        except Exception as e:
            print(f"Ikonkani saqlashda xatolik: {e}")
            return None

    def get_project_icon(self, project_path, default_auto_icon=None):
        """Custom ikonka bor bo'lsa uni, aks holda standart SVG ikonkani qaytaradi"""
        data = self.load_project_data(project_path)
        if data and data.get("custom_icon") and os.path.exists(data["custom_icon"]):
            return data["custom_icon"]
        return default_auto_icon

    def save_project_data(self, project_path, extra_data=None):
        if not project_path or not os.path.exists(project_path):
            return

        project_id = self._get_project_id(project_path)
        project_file = os.path.join(self.projects_dir, f"{project_id}.json")

        data = {
            "id": project_id,
            "name": os.path.basename(project_path),
            "path": project_path
        }

        if os.path.exists(project_file):
            try:
                with open(project_file, 'r', encoding='utf-8') as f:
                    data.update(json.load(f))
            except Exception:
                pass

        if extra_data:
            data.update(extra_data)

        try:
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Loyiha faylini saqlashda xatolik: {e}")

        self._update_index(project_path, project_id, data.get("name"))

    def rename_project(self, project_path, new_name):
        """Loyiha nomini yangilash va config hamda index'ga saqlash"""
        if not project_path:
            return
        project_id = self._get_project_id(project_path)

        self.save_project_data(project_path, extra_data={"name": new_name, "custom_name": new_name})

        recent = self.get_recent_projects()
        for p in recent:
            if p.get("path") == project_path or p.get("id") == project_id:
                p["name"] = new_name
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump({"recent_projects": recent}, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Index nomini yangilashda xatolik: {e}")

    def remove_project(self, project_path):
        """Loyihani konfiguratsiya va ro'yxatdan o'chirish (diskdagi fayllar o'chmaydi)"""
        if not project_path:
            return
        project_id = self._get_project_id(project_path)
        project_file = os.path.join(self.projects_dir, f"{project_id}.json")

        if os.path.exists(project_file):
            try:
                os.remove(project_file)
            except Exception as e:
                print(f"Loyiha config faylini o'chirishda xatolik: {e}")

        recent = self.get_recent_projects()
        recent = [p for p in recent if p.get("path") != project_path and p.get("id") != project_id]
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump({"recent_projects": recent}, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Indexdan o'chirishda xatolik: {e}")

    def load_project_data(self, project_path):
        project_id = self._get_project_id(project_path)
        project_file = os.path.join(self.projects_dir, f"{project_id}.json")

        if os.path.exists(project_file):
            try:
                with open(project_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def _update_index(self, project_path, project_id, project_name=None):
        recent = self.get_recent_projects()
        recent = [p for p in recent if p.get("path") != project_path]
        name = project_name or os.path.basename(project_path)
        recent.insert(0, {
            "id": project_id,
            "name": name,
            "path": project_path
        })

        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump({"recent_projects": recent[:10]}, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Index xatolik: {e}")

    def get_recent_projects(self):
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f).get("recent_projects", [])
            except Exception:
                pass
        return []