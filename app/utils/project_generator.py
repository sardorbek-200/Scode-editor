import json
import os
from typing import Dict, List


class ProjectGenerator:
    """Bo'sh papkaga professional shablon loyihalar yaratadi."""

    @staticmethod
    def _sanitize_name(name: str) -> str:
        cleaned = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in name.strip())
        cleaned = cleaned.strip("-_.")
        return cleaned or "scodetemplate"

    @staticmethod
    def _ensure_directories(base_path: str, directories: List[str]) -> None:
        for directory in directories:
            os.makedirs(os.path.join(base_path, directory), exist_ok=True)

    @staticmethod
    def _write_file_if_missing(path: str, content: str) -> None:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(content)

    @staticmethod
    def _write_json_if_missing(path: str, payload: Dict) -> None:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.write("\n")

    @staticmethod
    def create_project(project_path: str, template: str, app_name: str = "My App") -> Dict[str, str]:
        template_key = template.lower()
        if template_key == "pyqt6":
            return ProjectGenerator.create_pyqt6_app(project_path, app_name)
        if template_key == "express":
            return ProjectGenerator.create_express_app(project_path, app_name)
        if template_key == "react":
            return ProjectGenerator.create_react_app(project_path, app_name)
        raise ValueError(f"Unsupported template: {template}")

    @staticmethod
    def create_pyqt6_app(project_path: str, app_name: str = "MyPyQtApp") -> Dict[str, str]:
        """PyQt6 desktop ilova uchun to'liq va zamonaviy starter yaratadi."""
        project_path = os.path.abspath(project_path)

        directories = [
            "app",
            "app/ui",
            "app/core",
            "app/utils",
            "assets",
            "assets/icons",
        ]
        ProjectGenerator._ensure_directories(project_path, directories)

        files = {
            "main.py": f'''import sys
from PyQt6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("{app_name}")
    app.setOrganizationName("Scode")

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
''',
            "app/__init__.py": '"""PyQt6 application package."""\n',
            "app/ui/__init__.py": '"""UI package for the PyQt6 app."""\n',
            "app/core/__init__.py": '"""Core application logic."""\n',
            "app/utils/__init__.py": '"""Utility helpers for the application."""\n',
            "app/ui/main_window.py": '''from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Scode PyQt6 Starter")
        self.resize(960, 640)
        self.setMinimumSize(760, 520)
        self._apply_styles()
        self._build_ui()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background-color: #0f172a;
                color: #f8fafc;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QLabel#titleLabel {
                font-size: 28px;
                font-weight: 700;
            }
            QLabel#subtitleLabel {
                font-size: 14px;
                color: #94a3b8;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                background-color: #2563eb;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton#secondaryButton {
                background-color: #334155;
            }
            QPushButton#secondaryButton:hover {
                background-color: #475569;
            }
            """
        )

    def _build_ui(self) -> None:
        container = QWidget(self)
        container.setObjectName("mainContainer")
        self.setCentralWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)

        title = QLabel("Welcome to your new desktop app")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)

        subtitle = QLabel("This starter uses a clean structure with separate UI, core, and utility layers.")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        button_row = QHBoxLayout()
        button_row.setSpacing(12)

        primary_button = QPushButton("Continue")
        primary_button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_row.addWidget(primary_button)

        secondary_button = QPushButton("Open settings")
        secondary_button.setObjectName("secondaryButton")
        secondary_button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_row.addWidget(secondary_button)

        button_row.addStretch()
        layout.addLayout(button_row)

        layout.addStretch()
        self.statusBar().showMessage("Ready")
''',
            "requirements.txt": """PyQt6>=6.5.0
PyQt6-Qt6>=6.5.0
requests>=2.31.0
pillow>=10.0.0
""",
            ".gitignore": """__pycache__/
*.py[cod]
*.pyo
*.pyd
*.egg-info/
.venv/
venv/
.env
.env.local
.pytest_cache/
.mypy_cache/
.pyre/
.idea/
.vscode/
.DS_Store
build/
dist/
""",
            "README.md": f"""# {app_name}

{app_name} is a PyQt6 desktop starter generated by Scode.

## Features
- Clean modular structure
- Dark theme UI
- Ready for further app development

## Run
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
python main.py
```

## Structure
- app/ui/ - user interface components
- app/core/ - application logic
- app/utils/ - reusable helpers
- assets/ - images and icons
""",
        }

        for relative_path, content in files.items():
            full_path = os.path.join(project_path, relative_path)
            ProjectGenerator._write_file_if_missing(full_path, content)

        return {"project_path": project_path, "template": "pyqt6", "app_name": app_name}

    @staticmethod
    def create_express_app(project_path: str, app_name: str = "express-app") -> Dict[str, str]:
        """Express.js REST API loyihasi uchun to'liq backend shablon yaratadi."""
        project_path = os.path.abspath(project_path)
        package_name = ProjectGenerator._sanitize_name(app_name).lower().replace(" ", "-")

        directories = [
            "src",
            "src/controllers",
            "src/routes",
            "src/middlewares",
            "src/config",
        ]
        ProjectGenerator._ensure_directories(project_path, directories)

        package_payload = {
            "name": package_name,
            "version": "1.0.0",
            "description": f"{app_name} Express REST API",
            "main": "src/index.js",
            "scripts": {
                "start": "node src/index.js",
                "dev": "nodemon src/index.js",
            },
            "dependencies": {
                "cors": "^2.8.5",
                "dotenv": "^16.3.1",
                "express": "^4.21.2",
                "helmet": "^7.0.1",
                "morgan": "^1.10.0",
            },
            "devDependencies": {
                "nodemon": "^3.1.0",
            },
        }
        ProjectGenerator._write_json_if_missing(os.path.join(project_path, "package.json"), package_payload)

        ProjectGenerator._write_file_if_missing(
            os.path.join(project_path, "src", "index.js"),
            """const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const helmet = require('helmet');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
const port = process.env.PORT || 5000;
const nodeEnv = process.env.NODE_ENV || 'development';

const apiRoutes = require('./routes/api');

app.use(helmet());
app.use(cors());
app.use(morgan(nodeEnv === 'production' ? 'combined' : 'dev'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

app.get('/', (req, res) => {
  res.json({
    service: 'Scode Express API',
    status: 'ok',
    environment: nodeEnv,
  });
});

app.use('/api', apiRoutes);

app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(err.statusCode || 500).json({
    error: err.message || 'Internal server error',
  });
});

app.listen(port, () => {
  console.log(`Server listening on http://localhost:${port}`);
});
""",
        )

        ProjectGenerator._write_file_if_missing(
            os.path.join(project_path, "src", "controllers", "healthController.js"),
            """function getHealthStatus(req, res) {
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  });
}

module.exports = { getHealthStatus };
""",
        )

        ProjectGenerator._write_file_if_missing(
            os.path.join(project_path, "src", "routes", "api.js"),
            """const express = require('express');
const { getHealthStatus } = require('../controllers/healthController');

const router = express.Router();

router.get('/health', getHealthStatus);
router.get('/v1', (req, res) => {
  res.json({
    message: 'API v1 is ready',
    endpoints: ['/api/health'],
  });
});

module.exports = router;
""",
        )

        ProjectGenerator._write_file_if_missing(os.path.join(project_path, ".env"), """PORT=5000
NODE_ENV=development
""")

        ProjectGenerator._write_file_if_missing(os.path.join(project_path, ".env.example"), """PORT=5000
NODE_ENV=development
""")

        ProjectGenerator._write_file_if_missing(
            os.path.join(project_path, ".gitignore"),
            """node_modules/
.env
.env.local
logs/
*.log
.DS_Store
coverage/
.vscode/
""",
        )

        ProjectGenerator._write_file_if_missing(
            os.path.join(project_path, "README.md"),
            f"""# {app_name}

A production-ready Express.js REST API starter.

## Installation
```bash
npm install
```

## Run
```bash
npm run dev
```

## Endpoints
- GET /api/health
- GET /api/v1
""",
        )

        return {"project_path": project_path, "template": "express", "app_name": app_name}

    @staticmethod
    def create_react_app(project_path: str, app_name: str = "react-app") -> Dict[str, str]:
        """React + Vite frontend loyihasi uchun zamonaviy starter yaratadi."""
        project_path = os.path.abspath(project_path)
        package_name = ProjectGenerator._sanitize_name(app_name).lower().replace(" ", "-")

        directories = [
            "src",
            "src/components",
            "src/assets",
            "public",
        ]
        ProjectGenerator._ensure_directories(project_path, directories)

        package_payload = {
            "name": package_name,
            "private": True,
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview",
            },
            "dependencies": {
                "lucide-react": "^0.468.0",
                "react": "^18.3.1",
                "react-dom": "^18.3.1",
            },
            "devDependencies": {
                "@vitejs/plugin-react": "^4.3.1",
                "vite": "^5.4.10",
            },
        }
        ProjectGenerator._write_json_if_missing(os.path.join(project_path, "package.json"), package_payload)

        ProjectGenerator._write_file_if_missing(
            os.path.join(project_path, "vite.config.js"),
            """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',
  },
});
""",
        )

        ProjectGenerator._write_file_if_missing(
            os.path.join(project_path, "index.html"),
            """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="Scode React + Vite starter app" />
    <title>Scode Starter</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""",
        )

        ProjectGenerator._write_file_if_missing(
            os.path.join(project_path, "src", "main.jsx"),
            """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
""",
        )

        ProjectGenerator._write_file_if_missing(
            os.path.join(project_path, "src", "App.jsx"),
            """import { Sparkles, Rocket, ShieldCheck } from 'lucide-react';

const features = [
  {
    title: 'Fast setup',
    description: 'Start building immediately with a modern Vite scaffold.',
    icon: Rocket,
  },
  {
    title: 'Modern UI',
    description: 'A polished dark theme with clean spacing and strong contrast.',
    icon: Sparkles,
  },
  {
    title: 'Production ready',
    description: 'Structured for growth and easy collaboration.',
    icon: ShieldCheck,
  },
];

export default function App() {
  return (
    <main className="app-shell">
      <section className="hero-card">
        <p className="eyebrow">Scode React + Vite</p>
        <h1>Build your next idea with confidence.</h1>
        <p className="hero-copy">
          This starter includes a modern layout, reusable components, and a clean development setup.
        </p>
        <div className="feature-grid">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <article className="feature-card" key={feature.title}>
                <Icon size={20} />
                <h2>{feature.title}</h2>
                <p>{feature.description}</p>
              </article>
            );
          })}
        </div>
      </section>
    </main>
  );
}
""",
        )

        ProjectGenerator._write_file_if_missing(
            os.path.join(project_path, "src", "index.css"),
            """:root {
  color-scheme: dark;
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  line-height: 1.5;
  font-weight: 400;
  color: #f8fafc;
  background-color: #020617;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
  background: linear-gradient(135deg, #020617 0%, #111827 100%);
}

#root {
  min-height: 100vh;
}

.app-shell {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
}

.hero-card {
  width: min(960px, 100%);
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 24px;
  padding: 32px;
  box-shadow: 0 20px 60px rgba(2, 6, 23, 0.35);
}

.eyebrow {
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: #60a5fa;
  font-size: 0.85rem;
}

h1 {
  margin: 0 0 12px;
  font-size: clamp(2rem, 3vw, 3rem);
}

.hero-copy {
  margin: 0 0 24px;
  color: #cbd5e1;
  font-size: 1rem;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.feature-card {
  background: rgba(30, 41, 59, 0.9);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(148, 163, 184, 0.15);
}

.feature-card h2 {
  margin: 12px 0 8px;
  font-size: 1.05rem;
}

.feature-card p {
  margin: 0;
  color: #cbd5e1;
  font-size: 0.95rem;
}
""",
        )

        ProjectGenerator._write_file_if_missing(
            os.path.join(project_path, ".gitignore"),
            """node_modules/
dist/
.env
.env.local
.vscode/
.DS_Store
coverage/
""",
        )

        ProjectGenerator._write_file_if_missing(
            os.path.join(project_path, "README.md"),
            f"""# {app_name}

A modern React + Vite frontend starter.

## Install
```bash
npm install
```

## Run
```bash
npm run dev
```

## Scripts
- npm run dev - start the dev server
- npm run build - build for production
""",
        )

        return {"project_path": project_path, "template": "react", "app_name": app_name}
