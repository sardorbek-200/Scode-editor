# 🚀 Scode Editor

![Version](https://img.shields.io/badge/version-v0.3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?logo=qt)
![QScintilla](https://img.shields.io/badge/Core-QScintilla-orange)
![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)

> **Scode Editor** — Python va PyQt6 platformalarida yaratilgan yengil, tezkor, zamonaviy va professional kod redaktori (IDE).

---

## 📸 Skrinshotlar

![Scode Editor Preview](assets/icon.png)
*(Loyiha interfeysi: QScintilla Redaktori, Fayllar Daraxti va Integratsiyalashgan Terminal)*

---

## 🌟 Asosiy Imkoniyatlar (Features)

- **🎨 QScintilla Redaktor Dvigateli**:
  - Syntax Highlighting (`.py`, `.js`, `.jsx`, `.html`, `.css`, `.json` fayllari uchun tayyor lekserlar).
  - Code Folding (Kodni `[+]` / `[-]` orqali yig'ish va yozish).
  - Qator raqamlari (Line Numbers) va avtomatik Tab tashlash (Auto-Indentation).
  - Dark Theme `#1e1e1e` foni va oq kvadratlarsiz margin uslubi.

- **⚡ Auto Save (Avtomatik saqlash)**:
  - Kod tahrirlangandan so'ng 1.5 soniya `QTimer` kutilib, fayl diskka avtomatik va xavfsiz saqlanadi.
  - Status barda `(Auto-saved)` va `(Tahrirlanmoqda...)` holatlari real-vaqt rejimida ko'rinadi.

- **💻 Integrated Terminal (Integratsiyalashgan Konsol)**:
  - ANSI Escape rang kodlarini (`\x1b[32m`, `\x1b[31m`) avtomatik parsing qilib HTML / RichText shaklida ko'rsatish.
  - Klaviaturadagi **↑ (Tepaga)** va **↓ (Pastga)** yo'nalish tugmalari orqali buyruqlar tarixini (Command History) almashish.
  - Loyiha papkasida buyruqlarni bajarish (`python main.py`, `npm start`, `git status`).

- **📁 File Explorer Context Menu**:
  - Sichqonchaning o'ng tugmasi orqali yangi fayl va papka yaratish.
  - Mavjud fayl hamda papkalarni bir chertish bilan qaytadan nomlash hamda xavfsiz o'chirish.

- **💾 AppData/Local Asset va Kesh Boshqaruvi**:
  - Barcha sozlamalar va SVG/PNG assetlar platformaga mos holda `%LOCALAPPDATA%/ScodeEditor/` papkasida saqlanadi.
  - Window va Taskbar ikonkalari avtomatik ravishda AppUserModelID bilan biriktiriladi.

- **🎨 Modern Dark UI**:
  - VS Code uslubidagi zamonaviy to'q tema va ixcham interfeys.

---

## 🛠️ Texnologik Stack

- **Dasturlash tili**: Python 3.10+
- **GUI Framework**: PyQt6
- **Editor Engine**: PyQt6-QScintilla
- **Process Management**: QProcess (Asinxron Shell boshqaruvi)
- **Asset / Vector Icons**: PyQt6.QtSvg & QIcon

---

## 📁 Loyiha Strukturasi (Project Structure)

```text
scode/
├── app/
│   ├── ui/
│   │   ├── editor_scintilla.py  # QScintilla redaktor dvigateli va lekserlar
│   │   ├── editor_view.py       # Asosiy redaktor oynasi va fayllar daraxti
│   │   ├── project_card.py      # Loyiha kartalari va kontekst menyular
│   │   ├── projects_view.py     # So'nggi loyihalar ro'yxati va papka ochish
│   │   ├── terminal_panel.py    # ANSI rangli terminal va buyruqlar tarixi
│   │   └── login_window.py      # Autentifikatsiya oynasi
│   └── utils/
│       ├── config.py            # AppData/Local sozlamalarini boshqarish
│       ├── icon_manager.py      # Inline SVG ikonkalar va kesh
│       ├── paths.py             # Cross-platform LocalAppData yo'llari
│       └── project_inspector.py # Loyihalarni tahlil qilish
├── assets/
│   ├── icon.png                 # Ilova ikonkasi
│   └── icons/                   # Vektorli SVG ikonkalar
├── main.py                      # Dasturni ishga tushirish (Entry Point)
├── requirements.txt             # Kerakli Python kutubxonalari
└── README.md                    # Hujjatlashtirish
```

---

## 📥 O'rnatish va Ishga Tushirish (Installation & Usage)

### 1. Repozitoriyani klonlash
```bash
git clone https://github.com/sardorbek-200/scode-editor.git
cd scode-editor
```

### 2. Virtual muhit yaratish va faollashtirish (ixtiyoriy)
```bash
# Windows uchun
python -m venv venv
venv\Scripts\activate

# Linux / macOS uchun
python3 -m venv venv
source venv/bin/activate
```

### 3. Bog'liqliklarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. Dasturni ishga tushirish
```bash
python main.py
```

---

## 👨‍💻 Muallif va Bog'lanish

- **Muallif / Dasturchi**: Sardor ([@sstudiohub](https://github.com/sstudiohub))
- **Rasmiy Veb-Sayt**: [sstudio.uz](https://sstudio.uz)
- **Loyiha Sahifasi**: [Scode Editor](https://sstudio.uz/scode)

---

## 📜 Litsenziya

Ushbu loyiha [MIT License](LICENSE) litsenziyasi bo'yicha tarqatiladi.