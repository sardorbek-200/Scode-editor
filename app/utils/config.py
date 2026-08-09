import os
import json
import hashlib
import shutil

class ConfigManager:
    def __init__(self):
        local_app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        self.app_data_dir = os.path.join(local_app_data, 'ScodeEditor')
        self.projects_dir = os.path.join(self.app_data_dir, 'projects')
        
        # Yangi: Ikonkalar saqlanadigan papka
        self.icons_dir = os.path.join(self.app_data_dir, 'projects_icon')
        
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.icons_dir, exist_ok=True)
        
        self.index_file = os.path.join(self.app_data_dir, 'index.json')

    def _get_project_id(self, project_path):
        normalized_path = os.path.normpath(project_path).lower()
        return hashlib.md5(normalized_path.encode('utf-8')).hexdigest()

    def save_custom_icon(self, project_path, source_icon_path):
        """Foydalanuvchi tanlagan ikonkani projects_icon papkasiga nusxalash"""
        if not os.path.exists(source_icon_path):
            return None

        project_id = self._get_project_id(project_path)
        ext = os.path.splitext(source_icon_path)[1] # .png, .jpg va h.k.
        dest_filename = f"{project_id}{ext}"
        dest_path = os.path.join(self.icons_dir, dest_filename)

        try:
            shutil.copy2(source_icon_path, dest_path)
            # Loyiha json fayliga custom ikonka yo'lini yozib qo'yamiz
            self.save_project_data(project_path, extra_data={"custom_icon": dest_path})
            return dest_path
        except Exception as e:
            print(f"Ikonkani saqlashda xatolik: {e}")
            return None

    def get_project_icon(self, project_path, default_auto_icon=None):
        """Custom ikonka bor bo'lsa uni, aks holda loyiha ichidagi avto-ikonkani qaytaradi"""
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

        self._update_index(project_path, project_id)

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

    def _update_index(self, project_path, project_id):
        recent = self.get_recent_projects()
        recent = [p for p in recent if p.get("path") != project_path]
        recent.insert(0, {
            "id": project_id,
            "name": os.path.basename(project_path),
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