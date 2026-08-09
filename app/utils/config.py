import os
import json
import hashlib

class ConfigManager:
    def __init__(self):
        # 1. Asosiy LocalAppData va Projects papkalarini o'rnatish
        local_app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        self.app_data_dir = os.path.join(local_app_data, 'ScodeEditor')
        self.projects_dir = os.path.join(self.app_data_dir, 'projects')
        
        # Papkalarni yaratamiz
        os.makedirs(self.projects_dir, exist_ok=True)
        
        # Umumiy so'nggi loyihalar indeks fayli
        self.index_file = os.path.join(self.app_data_dir, 'index.json')

    def _get_project_id(self, project_path):
        """Loyiha yo'lidan unikal MD5 ID hosil qilish"""
        normalized_path = os.path.normpath(project_path).lower()
        return hashlib.md5(normalized_path.encode('utf-8')).hexdigest()

    def save_project_data(self, project_path, extra_data=None):
        """Loyihaning alohida <ID>.json fayliga ma'lumot saqlash"""
        if not project_path or not os.path.exists(project_path):
            return

        project_id = self._get_project_id(project_path)
        project_file = os.path.join(self.projects_dir, f"{project_id}.json")

        # Mavjud ma'lumotni o'qish
        data = {
            "id": project_id,
            "name": os.path.basename(project_path),
            "path": project_path,
            "open_files": [],
            "last_opened_at": None
        }

        if os.path.exists(project_file):
            try:
                with open(project_file, 'r', encoding='utf-8') as f:
                    data.update(json.load(f))
            except Exception:
                pass

        # Qo'shimcha ma'lumot bo'lsa yangilash
        if extra_data:
            data.update(extra_data)

        # <ID>.json ga yozish
        try:
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Loyiha faylini saqlashda xatolik: {e}")

        # Index faylini ham yangilab qo'yamiz (so'nggi loyihalar uchun)
        self._update_index(project_path, project_id)

    def load_project_data(self, project_path):
        """Loyihaning <ID>.json faylidan ma'lumotlarni o'qish"""
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
        """Oxirgi kirilgan loyihalar ro'yxatini index.json da saqlab borish"""
        recent = self.get_recent_projects()
        
        # Takrorlanmasligi uchun eskisini olib tashlaymiz
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
            print(f"Index faylini saqlashda xatolik: {e}")

    def get_recent_projects(self):
        """Index.json dan oxirgi loyihalar ro'yxatini olish"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f).get("recent_projects", [])
            except Exception:
                pass
        return []