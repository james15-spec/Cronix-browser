#!/usr/bin/env python3
"""
cronix.py — Cronix Browser by Croftonix
Requires: PyQt6, PyQt6-WebEngine, cryptography
  pip install PyQt6 PyQt6-Qt6 PyQt6-WebEngine cryptography
"""

import sys, json, os, re
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import (
    QUrl, Qt, QSize, pyqtSignal, QTimer, QPoint, QObject,
    QThread, QRunnable, QThreadPool,
)
from PyQt6.QtGui import (
    QKeySequence, QShortcut, QFont, QIcon, QPixmap, QImage, QPainter,
    QColor, QAction,
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit, QPushButton,
    QProgressBar, QStatusBar, QWidget, QHBoxLayout, QVBoxLayout,
    QDialog, QLabel, QComboBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,
    QFrame, QSizePolicy, QButtonGroup, QRadioButton,
    QGridLayout, QMenu, QToolButton, QAbstractItemView, QTabBar,
    QSpinBox, QCheckBox, QScrollArea, QSplitter, QTextEdit,
    QListWidget, QListWidgetItem, QInputDialog,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineProfile, QWebEngineSettings,
    QWebEngineDownloadRequest,
)

try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

VERSION = "1.3.0"
WEBSITE = "https://github.com/james15-spec/Cronix-browser"

# ── Config paths ──────────────────────────────────────────────────────────────
CONFIG_DIR     = Path.home() / ".config" / "cronix"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE  = CONFIG_DIR / "settings.json"
PASSWORDS_FILE = CONFIG_DIR / "passwords.json"
HISTORY_FILE   = CONFIG_DIR / "history.json"
SESSION_FILE   = CONFIG_DIR / "session.json"
KEY_FILE       = CONFIG_DIR / ".key"
DOWNLOADS_DIR  = Path.home() / "Downloads"

NEWTAB_PAGE = "https://cronix.wuaze.com"
SEARCH_ENGINES = {
    "Google": NEWTAB_PAGE,
}
SEARCH_QUERY_URLS = {
    "Google": "https://www.google.com/search?q={}",
}
DEFAULT_SETTINGS = {
    "search_engine": "Google",  # only Google supported
    "theme":         "dark",
    "accent":        "#89b4fa",
    "profile_path":  str(CONFIG_DIR / "profile"),
    "font_size":     16,
    "startup":       "newtab",   # newtab | session | url
    "startup_url":   "",
    "downloads_dir": str(DOWNLOADS_DIR),
}
ACCENTS = {
    "Blue":   "#89b4fa",
    "Mauve":  "#cba6f7",
    "Green":  "#a6e3a1",
    "Peach":  "#fab387",
    "Red":    "#f38ba8",
    "Yellow": "#f9e2af",
    "Teal":   "#94e2d5",
}

# ── Palette ───────────────────────────────────────────────────────────────────
def palette(theme: str, accent: str) -> dict:
    if theme == "dark":
        return dict(bg="#1e1e2e", surface="#313244", border="#45475a",
                    text="#cdd6f4", subtext="#a6adc8", muted="#6c7086",
                    accent=accent, acc_text="#1e1e2e",
                    tab_bg="#181825", tab_active="#1e1e2e")
    return dict(bg="#eff1f5", surface="#dce0e8", border="#bcc0cc",
                text="#4c4f69", subtext="#5c5f77", muted="#9ca0b0",
                accent=accent, acc_text="#ffffff",
                tab_bg="#ccd0da", tab_active="#eff1f5")

# ── Settings ──────────────────────────────────────────────────────────────────
class Settings:
    def __init__(self):
        self._data = dict(DEFAULT_SETTINGS)
        if SETTINGS_FILE.exists():
            try: self._data.update(json.loads(SETTINGS_FILE.read_text()))
            except Exception: pass
    def save(self):
        SETTINGS_FILE.write_text(json.dumps(self._data, indent=2))
    def get(self, key):
        return self._data.get(key, DEFAULT_SETTINGS.get(key))
    def set(self, key, value):
        self._data[key] = value; self.save()

# ── History ───────────────────────────────────────────────────────────────────
class HistoryManager:
    MAX = 5000
    def __init__(self):
        self._entries = []
        self._load()

    def _load(self):
        if HISTORY_FILE.exists():
            try: self._entries = json.loads(HISTORY_FILE.read_text())
            except Exception: self._entries = []

    def _save(self):
        HISTORY_FILE.write_text(json.dumps(self._entries[-self.MAX:], indent=2))

    def add(self, url: str, title: str):
        if not url or url.startswith("file://"):
            return
        self._entries.append({
            "url":   url,
            "title": title or url,
            "ts":    datetime.now().isoformat(timespec="seconds"),
        })
        self._save()

    def all_entries(self): return list(reversed(self._entries))
    def clear(self): self._entries = []; self._save()
    def search(self, q: str):
        q = q.lower()
        return [e for e in reversed(self._entries)
                if q in e["url"].lower() or q in e["title"].lower()]

# ── Password manager ──────────────────────────────────────────────────────────
class PasswordManager:
    def __init__(self):
        self._key    = self._load_or_create_key()
        self._fernet = Fernet(self._key) if HAS_CRYPTO else None
        self._entries: list = []
        self._load()

    def _load_or_create_key(self) -> bytes:
        if KEY_FILE.exists(): return KEY_FILE.read_bytes()
        key = Fernet.generate_key() if HAS_CRYPTO else b""
        if HAS_CRYPTO:
            KEY_FILE.write_bytes(key); KEY_FILE.chmod(0o600)
        return key

    def _load(self):
        if PASSWORDS_FILE.exists():
            try: self._entries = json.loads(PASSWORDS_FILE.read_text())
            except Exception: self._entries = []

    def _save(self):
        PASSWORDS_FILE.write_text(json.dumps(self._entries, indent=2))

    def _encrypt(self, t: str) -> str:
        return self._fernet.encrypt(t.encode()).decode() if self._fernet else t
    def _decrypt(self, t: str) -> str:
        if self._fernet:
            try: return self._fernet.decrypt(t.encode()).decode()
            except: return "••••••"
        return t

    def add(self, site, username, password):
        self._entries.append({"site": site, "username": username,
                               "password": self._encrypt(password),
                               "added": datetime.now().isoformat(timespec="seconds")})
        self._save()

    def delete(self, index: int):
        if 0 <= index < len(self._entries):
            self._entries.pop(index); self._save()

    def all_entries(self): return self._entries
    def get_password(self, i: int) -> str:
        return self._decrypt(self._entries[i]["password"])

    def import_csv(self, path: str) -> int:
        import csv; count = 0
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                site = row.get("url") or row.get("origin_url") or row.get("name","")
                user = row.get("username") or row.get("login","")
                pwd  = row.get("password","")
                if site or user:
                    self.add(site, user, pwd); count += 1
        return count

# ── Stylesheet ────────────────────────────────────────────────────────────────
def make_stylesheet(p: dict) -> str:
    return f"""
    QMainWindow, QDialog, QWidget {{
        background:{p['bg']}; color:{p['text']};
        font-family:'Segoe UI','Inter',sans-serif;
    }}
    QToolBar {{
        background:{p['bg']}; border-bottom:1px solid {p['border']};
        padding:4px 6px; spacing:4px;
    }}
    QPushButton {{
        background:{p['surface']}; color:{p['text']}; border:none;
        border-radius:6px; padding:5px 10px; font-size:14px; min-width:32px;
    }}
    QPushButton:hover   {{ background:{p['border']}; }}
    QPushButton:pressed {{ background:{p['muted']}; }}
    QPushButton:disabled {{ color:{p['muted']}; }}
    QPushButton#accent_btn {{
        background:{p['accent']}; color:{p['acc_text']}; font-weight:bold;
    }}
    QPushButton#danger_btn {{ background:#f38ba8; color:#1e1e2e; }}
    QPushButton#muted_btn  {{ background:transparent; color:{p['muted']}; border:1px solid {p['border']}; }}
    QToolButton {{
        background:{p['surface']}; color:{p['text']}; border:none;
        border-radius:6px; padding:5px 8px; font-size:16px; font-weight:bold;
    }}
    QToolButton:hover {{ background:{p['border']}; }}
    QToolButton:checked {{ background:{p['accent']}; color:{p['acc_text']}; }}
    QToolButton::menu-indicator {{ image:none; }}
    QLineEdit {{
        background:{p['surface']}; color:{p['text']};
        border:1px solid {p['border']}; border-radius:6px;
        padding:5px 10px; font-size:13px;
        selection-background-color:{p['accent']};
    }}
    QLineEdit:focus {{ border-color:{p['accent']}; }}
    QSpinBox {{
        background:{p['surface']}; color:{p['text']};
        border:1px solid {p['border']}; border-radius:6px; padding:4px 8px;
    }}
    QComboBox {{
        background:{p['surface']}; color:{p['text']};
        border:1px solid {p['border']}; border-radius:6px;
        padding:5px 10px; font-size:13px; min-width:120px;
    }}
    QComboBox:hover {{ border-color:{p['accent']}; }}
    QComboBox QAbstractItemView {{
        background:{p['surface']}; color:{p['text']};
        selection-background-color:{p['accent']};
        selection-color:{p['acc_text']}; border:1px solid {p['border']};
    }}
    QTabWidget#settings_tabs::pane {{
        border:1px solid {p['border']}; border-radius:6px; background:{p['bg']};
    }}
    QTabWidget#settings_tabs > QTabBar::tab {{
        background:{p['surface']}; color:{p['subtext']};
        padding:8px 16px; border-top-left-radius:6px;
        border-top-right-radius:6px; margin-right:2px;
    }}
    QTabWidget#settings_tabs > QTabBar::tab:selected {{
        background:{p['bg']}; color:{p['accent']};
        border-bottom:2px solid {p['accent']};
    }}
    QTabWidget#browser_tabs::pane {{ border:none; background:{p['bg']}; }}
    QTabWidget#browser_tabs > QTabBar {{ background:{p['tab_bg']}; }}
    QTabWidget#browser_tabs > QTabBar::tab {{
        background:{p['tab_bg']}; color:{p['subtext']};
        padding:5px 12px; min-width:100px; max-width:200px;
        border-top-left-radius:6px; border-top-right-radius:6px;
        margin-right:2px; margin-top:3px;
    }}
    QTabWidget#browser_tabs > QTabBar::tab:selected {{
        background:{p['tab_active']}; color:{p['text']};
        border-top:2px solid {p['accent']}; margin-top:1px;
    }}
    QTabWidget#browser_tabs > QTabBar::tab:hover:!selected {{
        background:{p['surface']};
    }}
    QTableWidget {{
        background:{p['surface']}; color:{p['text']};
        gridline-color:{p['border']}; border:1px solid {p['border']}; border-radius:6px;
    }}
    QTableWidget::item:selected {{ background:{p['accent']}; color:{p['acc_text']}; }}
    QHeaderView::section {{
        background:{p['bg']}; color:{p['subtext']}; border:none;
        border-bottom:1px solid {p['border']}; padding:6px 10px;
        font-size:12px; font-weight:bold; letter-spacing:0.05em;
    }}
    QListWidget {{
        background:{p['surface']}; color:{p['text']};
        border:1px solid {p['border']}; border-radius:6px;
    }}
    QListWidget::item {{ padding:6px 10px; border-radius:4px; }}
    QListWidget::item:selected {{ background:{p['accent']}; color:{p['acc_text']}; }}
    QListWidget::item:hover:!selected {{ background:{p['border']}; }}
    QScrollArea {{ border:none; background:transparent; }}
    QScrollBar:vertical {{
        background:{p['surface']}; width:8px; border-radius:4px;
    }}
    QScrollBar::handle:vertical {{
        background:{p['border']}; border-radius:4px; min-height:20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0px; }}
    QScrollBar:horizontal {{
        background:{p['surface']}; height:8px; border-radius:4px;
    }}
    QScrollBar::handle:horizontal {{
        background:{p['border']}; border-radius:4px; min-width:20px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0px; }}
    QLabel#section_title {{
        font-size:12px; font-weight:bold; color:{p['subtext']};
        letter-spacing:0.08em; padding:8px 0 4px 0;
    }}
    QLabel#setting_label {{ font-size:14px; color:{p['text']}; }}
    QFrame#card {{
        background:{p['surface']}; border:1px solid {p['border']};
        border-radius:10px; padding:4px;
    }}
    QRadioButton {{ color:{p['text']}; spacing:8px; font-size:13px; }}
    QRadioButton::indicator {{
        width:16px; height:16px; border-radius:8px;
        border:2px solid {p['border']}; background:{p['surface']};
    }}
    QRadioButton::indicator:checked {{
        background:{p['accent']}; border-color:{p['accent']};
    }}
    QCheckBox {{ color:{p['text']}; spacing:8px; font-size:13px; }}
    QCheckBox::indicator {{
        width:16px; height:16px; border-radius:4px;
        border:2px solid {p['border']}; background:{p['surface']};
    }}
    QCheckBox::indicator:checked {{
        background:{p['accent']}; border-color:{p['accent']};
    }}
    QStatusBar {{ background:{p['bg']}; color:{p['muted']}; font-size:11px; }}
    QProgressBar        {{ background:{p['bg']}; border:none; }}
    QProgressBar::chunk {{ background:{p['accent']}; }}
    QMenu {{
        background:{p['surface']}; color:{p['text']};
        border:1px solid {p['border']}; border-radius:8px; padding:4px;
    }}
    QMenu::item {{ padding:7px 20px; border-radius:5px; }}
    QMenu::item:selected {{ background:{p['accent']}; color:{p['acc_text']}; }}
    QMenu::separator {{ height:1px; background:{p['border']}; margin:4px 12px; }}
    QTextEdit {{
        background:{p['surface']}; color:{p['text']};
        border:1px solid {p['border']}; border-radius:6px;
    }}
    """

# ── Tab spinner ───────────────────────────────────────────────────────────────
SPINNER_FRAMES = ["◐", "◓", "◑", "◒"]


# ── Splash screen ─────────────────────────────────────────────────────────────
class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.SplashScreen |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(420, 300)
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center().x() - 210, screen.center().y() - 150)

        card = QFrame(self)
        card.setFixedSize(420, 300)
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #0f1117, stop:1 #1a2040);
                border-radius: 18px;
                border: 1px solid #2060c0;
            }
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(30, 30, 30, 24)
        card_lay.setSpacing(10)
        card_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon_label = QLabel()
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for icon_path in ["/usr/share/pixmaps/cronix.png",
                           "/usr/share/cronix/cronix_icon.png"]:
            if os.path.exists(icon_path):
                pix = QPixmap(icon_path).scaled(
                    100, 100,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                self._icon_label.setPixmap(pix)
                break
        card_lay.addWidget(self._icon_label)

        name_lbl = QLabel("Cronix")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(
            "color:#cdd6f4;font-size:28px;font-weight:bold;"
            "font-family:'Segoe UI',Inter,sans-serif;background:transparent;border:none;")
        card_lay.addWidget(name_lbl)

        tag_lbl = QLabel("by Croftonix")
        tag_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag_lbl.setStyleSheet(
            "color:#4a6a9a;font-size:13px;letter-spacing:0.15em;"
            "font-family:'Segoe UI',Inter,sans-serif;background:transparent;border:none;")
        card_lay.addWidget(tag_lbl)

        card_lay.addSpacing(8)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100); self._bar.setValue(0)
        self._bar.setTextVisible(False); self._bar.setFixedHeight(3)
        self._bar.setStyleSheet("""
            QProgressBar{background:#1a2a4a;border:none;border-radius:2px;}
            QProgressBar::chunk{background:#2979d4;border-radius:2px;}
        """)
        card_lay.addWidget(self._bar)

        ver_lbl = QLabel(f"v{VERSION}")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_lbl.setStyleSheet(
            "color:#2a3a5a;font-size:11px;letter-spacing:0.1em;"
            "background:transparent;border:none;")
        card_lay.addWidget(ver_lbl)

        self._opacity = 0.0
        self.setWindowOpacity(0.0)
        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(20)
        self._fade_timer.timeout.connect(self._fade_in)
        self._fade_timer.start()

        self._prog_val = 0
        self._prog_timer = QTimer(self)
        self._prog_timer.setInterval(12)
        self._prog_timer.timeout.connect(self._tick_progress)
        self._prog_timer.start()

    def _fade_in(self):
        self._opacity = min(1.0, self._opacity + 0.06)
        self.setWindowOpacity(self._opacity)
        if self._opacity >= 1.0: self._fade_timer.stop()

    def _tick_progress(self):
        self._prog_val = min(100, self._prog_val + 1)
        self._bar.setValue(self._prog_val)
        if self._prog_val >= 100: self._prog_timer.stop()


# ── About dialog ──────────────────────────────────────────────────────────────
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Cronix")
        self.setFixedSize(420, 460)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 32, 32, 28)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for icon_path in ["/usr/share/pixmaps/cronix.png",
                           "/usr/share/cronix/cronix_icon.png"]:
            if os.path.exists(icon_path):
                pix = QPixmap(icon_path).scaled(
                    96, 96,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                icon_lbl.setPixmap(pix)
                break
        lay.addWidget(icon_lbl)
        lay.addSpacing(16)

        name = QLabel("Cronix")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("font-size:26px;font-weight:bold;")
        lay.addWidget(name)

        ver = QLabel(f"Version {VERSION}")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet("font-size:13px;color:#6c7086;margin-bottom:4px;")
        lay.addWidget(ver)

        tag = QLabel("Your browser. Your data. Your rules.")
        tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag.setStyleSheet("font-size:13px;font-style:italic;color:#89b4fa;margin-bottom:20px;")
        lay.addWidget(tag)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:#313244;margin:0 0 16px 0;")
        lay.addWidget(line)
        lay.addSpacing(4)

        desc = QLabel(
            "A lightweight, privacy-respecting desktop browser\n"
            "built with PyQt6 and QtWebEngine.\n\n"
            "Tabbed browsing  \u00b7  Password manager  \u00b7  History\n"
            "Downloads  \u00b7  Cookie manager  \u00b7  Session restore\n"
            "Find in page  \u00b7  Zoom  \u00b7  Mute tabs  \u00b7  Screenshot"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size:12px;color:#a6adc8;line-height:1.6;")
        desc.setWordWrap(True)
        lay.addWidget(desc)
        lay.addSpacing(20)

        by = QLabel("Built by <b>Croftonix</b>")
        by.setAlignment(Qt.AlignmentFlag.AlignCenter)
        by.setStyleSheet("font-size:12px;color:#6c7086;")
        lay.addWidget(by)
        lay.addSpacing(6)

        link = QLabel('<a href="' + WEBSITE + '" style="color:#89b4fa;">' + WEBSITE + '</a>')
        link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link.setOpenExternalLinks(True)
        link.setStyleSheet("font-size:12px;")
        lay.addWidget(link)
        lay.addSpacing(20)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("accent_btn")
        close_btn.setFixedWidth(120)
        close_btn.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch(); btn_row.addWidget(close_btn); btn_row.addStretch()
        lay.addLayout(btn_row)


# ── History dialog ────────────────────────────────────────────────────────────
class HistoryDialog(QDialog):
    navigate_requested = pyqtSignal(str)

    def __init__(self, history: HistoryManager, parent=None):
        super().__init__(parent)
        self.history = history
        self.setWindowTitle("History")
        self.resize(700, 500)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16); lay.setSpacing(10)

        # Search bar
        row = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search history…")
        self.search_bar.textChanged.connect(self._refresh)
        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("danger_btn")
        clear_btn.clicked.connect(self._clear_all)
        row.addWidget(self.search_bar); row.addWidget(clear_btn)
        lay.addLayout(row)

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self._open_item)
        lay.addWidget(self.list)

        self._refresh()

    def _refresh(self):
        q = self.search_bar.text().strip()
        entries = self.history.search(q) if q else self.history.all_entries()
        self.list.clear()
        for e in entries[:500]:
            item = QListWidgetItem(f"{e['ts']}  —  {e['title']}\n{e['url']}")
            item.setData(Qt.ItemDataRole.UserRole, e["url"])
            self.list.addItem(item)

    def _open_item(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            self.navigate_requested.emit(url)
            self.accept()

    def _clear_all(self):
        if QMessageBox.question(self, "Clear History", "Clear all browsing history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.history.clear(); self._refresh()

# ── Downloads manager dialog ──────────────────────────────────────────────────
class DownloadsDialog(QDialog):
    def __init__(self, downloads: list, parent=None):
        super().__init__(parent)
        self.downloads = downloads
        self.setWindowTitle("Downloads")
        self.resize(700, 420)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16); lay.setSpacing(10)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File", "Size", "Status", "Path"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        lay.addWidget(self.table)

        row = QHBoxLayout()
        open_btn = QPushButton("Open Folder")
        open_btn.clicked.connect(self._open_folder)
        clear_btn = QPushButton("Clear Finished")
        clear_btn.clicked.connect(self._clear_finished)
        row.addStretch(); row.addWidget(clear_btn); row.addWidget(open_btn)
        lay.addLayout(row)

        self._refresh()

    def _refresh(self):
        self.table.setRowCount(len(self.downloads))
        for i, d in enumerate(self.downloads):
            name   = d.get("name", "")
            total  = d.get("total", 0)
            recv   = d.get("received", 0)
            status = d.get("status", "")
            path   = d.get("path", "")
            size_str = f"{recv/1e6:.1f} / {total/1e6:.1f} MB" if total else f"{recv/1e6:.1f} MB"
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(size_str))
            self.table.setItem(i, 2, QTableWidgetItem(status))
            self.table.setItem(i, 3, QTableWidgetItem(path))

    def _open_folder(self):
        import subprocess
        dl_dir = str(Path.home() / "Downloads")
        subprocess.Popen(["xdg-open", dl_dir])

    def _clear_finished(self):
        self.downloads[:] = [d for d in self.downloads
                              if d.get("status") not in ("Complete", "Cancelled")]
        self._refresh()

# ── Cookie manager dialog ─────────────────────────────────────────────────────
class CookieDialog(QDialog):
    def __init__(self, profile: QWebEngineProfile, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.setWindowTitle("Cookie Manager")
        self.resize(640, 420)
        self._cookies = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16,16,16,16); lay.setSpacing(10)

        info = QLabel("Cookies are managed by the browser profile. You can clear all cookies below.")
        info.setWordWrap(True)
        info.setStyleSheet("color:#888; font-size:12px;")
        lay.addWidget(info)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Domain", "Name", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table)

        row = QHBoxLayout()
        del_btn = QPushButton("Delete Selected")
        del_btn.setObjectName("danger_btn")
        del_btn.clicked.connect(self._delete_selected)
        clear_btn = QPushButton("Clear All Cookies")
        clear_btn.setObjectName("danger_btn")
        clear_btn.clicked.connect(self._clear_all)
        row.addStretch(); row.addWidget(del_btn); row.addWidget(clear_btn)
        lay.addLayout(row)

        # Load cookies via cookie store
        store = self.profile.cookieStore()
        store.cookieAdded.connect(self._on_cookie_added)
        store.loadAllCookies()

    def _on_cookie_added(self, cookie):
        domain = cookie.domain()
        name   = bytes(cookie.name()).decode("utf-8", errors="replace")
        value  = bytes(cookie.value()).decode("utf-8", errors="replace")[:80]
        self._cookies.append((domain, name, value))
        r = self.table.rowCount()
        self.table.setRowCount(r + 1)
        self.table.setItem(r, 0, QTableWidgetItem(domain))
        self.table.setItem(r, 1, QTableWidgetItem(name))
        self.table.setItem(r, 2, QTableWidgetItem(value))

    def _delete_selected(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)
            if r < len(self._cookies):
                self._cookies.pop(r)

    def _clear_all(self):
        if QMessageBox.question(self, "Clear Cookies", "Delete all cookies?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.profile.cookieStore().deleteAllCookies()
            self._cookies.clear()
            self.table.setRowCount(0)

# ── Settings dialog ───────────────────────────────────────────────────────────
class SettingsDialog(QDialog):
    settings_changed = pyqtSignal()

    def __init__(self, settings: Settings, pw_manager: PasswordManager, parent=None):
        super().__init__(parent)
        self.settings   = settings
        self.pw_manager = pw_manager
        self.setWindowTitle("Settings")
        self.setMinimumSize(700, 580)
        self.resize(740, 620)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("settings_tabs")
        self.tabs.addTab(self._build_general_tab(),    "⚙  General")
        self.tabs.addTab(self._build_appearance_tab(), "🎨  Appearance")
        self.tabs.addTab(self._build_passwords_tab(),  "🔑  Passwords")
        layout.addWidget(self.tabs)

    # ── General ───────────────────────────────────────────────────────────────
    def _build_general_tab(self):
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(24,20,24,20); outer.setSpacing(8)

        # Startup
        outer.addWidget(self._section("ON STARTUP"))
        card2 = self._card()
        g2 = QVBoxLayout(card2); g2.setContentsMargins(16,12,16,12); g2.setSpacing(8)
        self.startup_grp = QButtonGroup(self)
        cur_startup = self.settings.get("startup")
        for val, label in [("newtab","Open new tab"), ("session","Restore last session"), ("url","Open specific URL")]:
            rb = QRadioButton(label)
            rb.setChecked(cur_startup == val)
            rb.toggled.connect(lambda c, v=val: self.settings.set("startup", v) if c else None)
            self.startup_grp.addButton(rb)
            g2.addWidget(rb)
        self.startup_url_edit = QLineEdit()
        self.startup_url_edit.setPlaceholderText("https://example.com")
        self.startup_url_edit.setText(self.settings.get("startup_url"))
        self.startup_url_edit.textChanged.connect(lambda t: self.settings.set("startup_url", t))
        g2.addWidget(self.startup_url_edit)
        outer.addWidget(card2)

        # Font size
        outer.addWidget(self._section("CONTENT"))
        card3 = self._card()
        g3 = QGridLayout(card3); g3.setContentsMargins(16,12,16,12); g3.setSpacing(10)
        g3.addWidget(self._label("Default font size"), 0, 0)
        self.font_spin = QSpinBox()
        self.font_spin.setRange(10, 32); self.font_spin.setSuffix(" px")
        self.font_spin.setValue(self.settings.get("font_size"))
        self.font_spin.valueChanged.connect(
            lambda v: (self.settings.set("font_size", v), self.settings_changed.emit()))
        g3.addWidget(self.font_spin, 0, 1, alignment=Qt.AlignmentFlag.AlignRight)
        outer.addWidget(card3)

        # Downloads dir
        outer.addWidget(self._section("DOWNLOADS"))
        card4 = self._card()
        g4 = QHBoxLayout(card4); g4.setContentsMargins(16,12,16,12); g4.setSpacing(8)
        self.dl_label = QLabel(self.settings.get("downloads_dir"))
        self.dl_label.setStyleSheet("font-size:12px; color:#888;")
        g4.addWidget(self.dl_label, 1)
        dl_btn = QPushButton("Change…")
        dl_btn.clicked.connect(self._change_dl_dir)
        g4.addWidget(dl_btn)
        outer.addWidget(card4)

        # Browsing data
        outer.addWidget(self._section("BROWSING DATA"))
        card5 = self._card()
        g5 = QHBoxLayout(card5); g5.setContentsMargins(16,12,16,12); g5.setSpacing(8)
        clr = QPushButton("Clear Cookies & Cache…")
        clr.setObjectName("danger_btn"); clr.clicked.connect(self._clear_data)
        g5.addWidget(clr); g5.addStretch()
        outer.addWidget(card5)

        outer.addStretch()
        return w

    # ── Appearance ────────────────────────────────────────────────────────────
    def _build_appearance_tab(self):
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(24,20,24,20); outer.setSpacing(6)
        outer.addWidget(self._section("THEME"))
        card = self._card()
        hbox = QHBoxLayout(card); hbox.setContentsMargins(16,12,16,12); hbox.setSpacing(16)
        self.radio_dark  = QRadioButton("🌙  Dark")
        self.radio_light = QRadioButton("☀️  Light")
        grp = QButtonGroup(self)
        grp.addButton(self.radio_dark); grp.addButton(self.radio_light)
        cur = self.settings.get("theme")
        self.radio_dark.setChecked(cur=="dark"); self.radio_light.setChecked(cur=="light")
        self.radio_dark.toggled.connect(
            lambda c: (self.settings.set("theme","dark"),  self.settings_changed.emit()) if c else None)
        self.radio_light.toggled.connect(
            lambda c: (self.settings.set("theme","light"), self.settings_changed.emit()) if c else None)
        hbox.addWidget(self.radio_dark); hbox.addWidget(self.radio_light); hbox.addStretch()
        outer.addWidget(card)

        outer.addSpacing(10)
        outer.addWidget(self._section("ACCENT COLOUR"))
        card2 = self._card()
        flow = QHBoxLayout(card2); flow.setContentsMargins(16,12,16,12); flow.setSpacing(8)
        cur_acc = self.settings.get("accent")
        self._acc_grp = QButtonGroup(self)
        for name, hv in ACCENTS.items():
            btn = QPushButton(); btn.setFixedSize(36,36)
            btn.setToolTip(name); btn.setCheckable(True); btn.setChecked(hv==cur_acc)
            btn.setStyleSheet(f"""
                QPushButton {{background:{hv};border-radius:18px;border:3px solid transparent;}}
                QPushButton:checked {{border:3px solid white;}}
                QPushButton:hover   {{border:3px solid rgba(255,255,255,0.5);}}
            """)
            btn.clicked.connect(lambda _, h=hv: (self.settings.set("accent",h), self.settings_changed.emit()))
            self._acc_grp.addButton(btn); flow.addWidget(btn)
        flow.addStretch()
        outer.addWidget(card2)
        outer.addStretch()
        return w

    # ── Passwords ─────────────────────────────────────────────────────────────
    def _build_passwords_tab(self):
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(24,20,24,20); outer.setSpacing(10)
        row = QHBoxLayout(); row.setSpacing(8)
        imp = QPushButton("⬆  Import CSV"); imp.setObjectName("accent_btn")
        imp.clicked.connect(self._import_csv); row.addWidget(imp)
        add = QPushButton("＋  Add Entry"); add.clicked.connect(self._add_pw); row.addWidget(add)
        dl  = QPushButton("🗑  Delete"); dl.setObjectName("danger_btn")
        dl.clicked.connect(self._del_pw); row.addWidget(dl)
        row.addStretch()
        rev = QPushButton("👁  Reveal"); rev.setCheckable(True)
        rev.toggled.connect(self._toggle_reveal); row.addWidget(rev)
        outer.addLayout(row)
        if not HAS_CRYPTO:
            warn = QLabel("⚠  'cryptography' not installed — passwords stored in plain text.")
            warn.setWordWrap(True)
            warn.setStyleSheet("color:#f9e2af;font-size:12px;background:#45351a;border-radius:6px;padding:6px;")
            outer.addWidget(warn)
        self.pw_table = QTableWidget()
        self.pw_table.setColumnCount(4)
        self.pw_table.setHorizontalHeaderLabels(["Site","Username","Password","Added"])
        self.pw_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.pw_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.pw_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.pw_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.pw_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.pw_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.pw_table.verticalHeader().setVisible(False)
        self.pw_table.setAlternatingRowColors(True)
        self._reveal = False
        self._refresh_pw_table()
        outer.addWidget(self.pw_table)
        return w

    # helpers
    def _section(self, t):
        l = QLabel(t); l.setObjectName("section_title"); return l
    def _label(self, t):
        l = QLabel(t); l.setObjectName("setting_label"); return l
    def _card(self):
        f = QFrame(); f.setObjectName("card"); return f

    def _change_dl_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Downloads Folder",
                                             self.settings.get("downloads_dir"))
        if d:
            self.settings.set("downloads_dir", d)
            self.dl_label.setText(d)

    def _clear_data(self):
        if QMessageBox.question(self, "Clear Data", "Clear cookies and cache?",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            p = QWebEngineProfile.defaultProfile()
            p.clearHttpCache(); p.cookieStore().deleteAllCookies()
            QMessageBox.information(self, "Done", "Cleared.")

    def _refresh_pw_table(self):
        entries = self.pw_manager.all_entries()
        self.pw_table.setRowCount(len(entries))
        for i, e in enumerate(entries):
            pwd = self.pw_manager.get_password(i) if self._reveal else "••••••••"
            self.pw_table.setItem(i,0,QTableWidgetItem(e.get("site","")))
            self.pw_table.setItem(i,1,QTableWidgetItem(e.get("username","")))
            self.pw_table.setItem(i,2,QTableWidgetItem(pwd))
            self.pw_table.setItem(i,3,QTableWidgetItem(e.get("added","")))

    def _toggle_reveal(self, c): self._reveal = c; self._refresh_pw_table()

    def _import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self,"Import CSV",str(Path.home()),"CSV (*.csv);;All (*)")
        if not path: return
        try:
            n = self.pw_manager.import_csv(path)
            self._refresh_pw_table()
            QMessageBox.information(self,"Done",f"Imported {n} password(s).")
        except Exception as e:
            QMessageBox.critical(self,"Failed",str(e))

    def _add_pw(self):
        dlg = AddPasswordDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            s,u,p = dlg.values()
            if s or u: self.pw_manager.add(s,u,p); self._refresh_pw_table()

    def _del_pw(self):
        rows = sorted({i.row() for i in self.pw_table.selectedIndexes()}, reverse=True)
        if not rows: return
        if QMessageBox.question(self,"Delete",f"Delete {len(rows)} entr{'y' if len(rows)==1 else 'ies'}?",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            for r in rows: self.pw_manager.delete(r)
            self._refresh_pw_table()


class AddPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Password"); self.setFixedSize(360,220)
        lay = QVBoxLayout(self); lay.setSpacing(10); lay.setContentsMargins(20,20,20,20)
        self.site = QLineEdit(); self.site.setPlaceholderText("Site / URL")
        self.user = QLineEdit(); self.user.setPlaceholderText("Username / email")
        self.pwd  = QLineEdit(); self.pwd.setPlaceholderText("Password")
        self.pwd.setEchoMode(QLineEdit.EchoMode.Password)
        for w in (self.site, self.user, self.pwd): lay.addWidget(w)
        btns = QHBoxLayout()
        ok = QPushButton("Save"); ok.setObjectName("accent_btn")
        cnl = QPushButton("Cancel")
        ok.clicked.connect(self.accept); cnl.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(cnl); btns.addWidget(ok); lay.addLayout(btns)
    def values(self): return self.site.text().strip(), self.user.text().strip(), self.pwd.text()


# ── Find bar ──────────────────────────────────────────────────────────────────
class FindBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8,4,8,4); lay.setSpacing(6)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Find in page…")
        self.input.setFixedWidth(240)
        self.input.textChanged.connect(self._find)
        self.input.returnPressed.connect(self._find_next)

        self.lbl = QLabel("")
        self.lbl.setStyleSheet("font-size:11px; color:#888; min-width:60px;")

        prev_btn = QPushButton("▲"); prev_btn.setFixedWidth(30)
        next_btn = QPushButton("▼"); next_btn.setFixedWidth(30)
        close_btn = QPushButton("✕"); close_btn.setFixedWidth(30)
        prev_btn.clicked.connect(self._find_prev)
        next_btn.clicked.connect(self._find_next)
        close_btn.clicked.connect(self.hide_bar)

        lay.addWidget(QLabel("Find:")); lay.addWidget(self.input)
        lay.addWidget(self.lbl)
        lay.addWidget(prev_btn); lay.addWidget(next_btn)
        lay.addWidget(close_btn); lay.addStretch()

        self._page = None

    def set_page(self, page):
        self._page = page

    def show_bar(self):
        self.setVisible(True)
        self.input.setFocus()
        self.input.selectAll()

    def hide_bar(self):
        self.setVisible(False)
        if self._page:
            self._page.findText("")

    def _find(self, text=""):
        if self._page:
            self._page.findText(text or self.input.text())

    def _find_next(self):
        if self._page:
            self._page.findText(self.input.text())

    def _find_prev(self):
        if self._page:
            self._page.findText(self.input.text(),
                QWebEnginePage.FindFlag.FindBackward)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.hide_bar()
        else:
            super().keyPressEvent(e)


# ── Browser tab ───────────────────────────────────────────────────────────────
class BrowserTab(QWidget):
    title_changed  = pyqtSignal(str)
    url_changed    = pyqtSignal(QUrl)
    load_progress  = pyqtSignal(int)
    load_started   = pyqtSignal()
    load_finished  = pyqtSignal(bool)
    link_hovered   = pyqtSignal(str)
    favicon_changed = pyqtSignal(QIcon)

    def __init__(self, profile: QWebEngineProfile, url: QUrl = None,
                 font_size: int = 16, parent=None):
        super().__init__(parent)
        self._muted = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        self.webview = QWebEngineView()
        page = QWebEnginePage(profile, self.webview)
        self.webview.setPage(page)

        # Font size
        settings = self.webview.settings()
        settings.setFontSize(QWebEngineSettings.FontSize.DefaultFontSize, font_size)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        # Find bar
        self.find_bar = FindBar(self)
        self.find_bar.set_page(page)

        lay.addWidget(self.find_bar)
        lay.addWidget(self.webview)

        self.webview.titleChanged.connect(self.title_changed)
        self.webview.urlChanged.connect(self.url_changed)
        self.webview.loadProgress.connect(self.load_progress)
        self.webview.loadStarted.connect(self.load_started)
        self.webview.loadFinished.connect(self.load_finished)
        self.webview.page().linkHovered.connect(self.link_hovered)
        self.webview.iconChanged.connect(self.favicon_changed)

        if url:
            self.webview.setUrl(url)

    def navigate(self, url: QUrl): self.webview.setUrl(url)
    def back(self):    self.webview.back()
    def forward(self): self.webview.forward()
    def reload(self):  self.webview.reload()
    def reload_bypass(self):
        self.webview.page().triggerAction(QWebEnginePage.WebAction.ReloadAndBypassCache)
    def can_go_back(self):    return self.webview.page().history().canGoBack()
    def can_go_forward(self): return self.webview.page().history().canGoForward()
    def current_url(self):    return self.webview.url()
    def current_title(self):  return self.webview.title()
    def zoom_in(self):        self.webview.setZoomFactor(min(self.webview.zoomFactor()+0.1, 5.0))
    def zoom_out(self):       self.webview.setZoomFactor(max(self.webview.zoomFactor()-0.1, 0.25))
    def zoom_reset(self):     self.webview.setZoomFactor(1.0)

    def toggle_mute(self):
        self._muted = not self._muted
        self.webview.page().setAudioMuted(self._muted)
        return self._muted

    def is_muted(self): return self._muted

    def screenshot(self) -> QPixmap:
        size = self.webview.contentsRect().size()
        pixmap = QPixmap(size)
        self.webview.render(pixmap)
        return pixmap


# ── Main window ───────────────────────────────────────────────────────────────
class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings    = Settings()
        self.pw_manager  = PasswordManager()
        self.history     = HistoryManager()
        self._downloads: list = []
        self._spinner_frame = 0
        self.setWindowTitle("Cronix")
        self.resize(1280, 800)

        # Persistent profile
        profile_path = self.settings.get("profile_path")
        self._profile = QWebEngineProfile("cronix", self)
        self._profile.setPersistentStoragePath(profile_path)
        self._profile.setCachePath(str(Path(profile_path) / "cache"))
        self._profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self._profile.setHttpUserAgent(
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/136.0.0.0 Safari/537.36"
        )
        self._profile.setHttpAcceptLanguage("en-GB,en;q=0.9,en-US;q=0.8")
        self._profile.downloadRequested.connect(self._on_download_requested)

        # Spinner timer
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(150)
        self._spinner_timer.timeout.connect(self._tick_spinner)
        self._loading_tabs: set = set()

        # ── Toolbar ───────────────────────────────────────────────────────────
        self.toolbar = QToolBar("Navigation")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        self.btn_back    = QPushButton("◀")
        self.btn_forward = QPushButton("▶")
        self.btn_refresh = QPushButton("⟳")
        self.btn_home    = QPushButton("⌂")
        self.btn_new_tab = QPushButton("＋")

        for btn, tip in [
            (self.btn_back,    "Back (Alt+Left)"),
            (self.btn_forward, "Forward (Alt+Right)"),
            (self.btn_refresh, "Refresh (F5)"),
            (self.btn_home,    "Home"),
            (self.btn_new_tab, "New Tab (Ctrl+T)"),
        ]:
            btn.setToolTip(tip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.toolbar.addWidget(btn)

        # URL bar
        nav = QWidget()
        nav.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        nav_lay = QHBoxLayout(nav)
        nav_lay.setContentsMargins(4,0,4,0); nav_lay.setSpacing(4)
        self.url_bar = QLineEdit()
        self.url_bar.setClearButtonEnabled(True)
        self.btn_go = QPushButton("Go")
        self.btn_go.setObjectName("accent_btn")
        self.btn_go.setCursor(Qt.CursorShape.PointingHandCursor)
        nav_lay.addWidget(self.url_bar); nav_lay.addWidget(self.btn_go)
        self.toolbar.addWidget(nav)

        # Mute button
        self.btn_mute = QToolButton()
        self.btn_mute.setText("🔊")
        self.btn_mute.setToolTip("Mute/unmute tab (Ctrl+M)")
        self.btn_mute.setCheckable(True)
        self.btn_mute.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mute.clicked.connect(self._toggle_mute)
        self.toolbar.addWidget(self.btn_mute)

        # ⋮ menu
        self.btn_menu = QToolButton()
        self.btn_menu.setText("⋮")
        self.btn_menu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        dot_menu = QMenu(self)
        dot_menu.addAction("⚙  Settings",        self._open_settings)
        dot_menu.addAction("🔑  Passwords",       self._open_passwords_tab)
        dot_menu.addSeparator()
        dot_menu.addAction("🕐  History",         self._open_history)
        dot_menu.addAction("⬇  Downloads",        self._open_downloads)
        dot_menu.addAction("🍪  Cookies",         self._open_cookies)
        dot_menu.addSeparator()
        dot_menu.addAction("📷  Screenshot",      self._take_screenshot)
        dot_menu.addSeparator()
        dot_menu.addAction("🔍  Find in Page",    self._show_find)
        dot_menu.addAction("🔎  Zoom In",         self._zoom_in)
        dot_menu.addAction("🔍  Zoom Out",        self._zoom_out)
        dot_menu.addAction("⊙  Reset Zoom",       self._zoom_reset)
        dot_menu.addSeparator()
        dot_menu.addAction("🗂  New Tab",         self._new_tab)
        dot_menu.addAction("✕  Close Tab",        self._close_current_tab)
        dot_menu.addSeparator()
        dot_menu.addAction("🔄  Reload",          self._refresh)
        dot_menu.addAction("🏠  Home",            self._go_home)
        dot_menu.addSeparator()
        dot_menu.addAction("ℹ  About Cronix",     self._open_about)
        self.btn_menu.setMenu(dot_menu)
        self.toolbar.addWidget(self.btn_menu)

        # ── Tab widget ────────────────────────────────────────────────────────
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("browser_tabs")
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_switched)

        # ── Progress + central ────────────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setMaximumHeight(3)
        self.progress.setTextVisible(False)

        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0,0,0,0); vbox.setSpacing(0)
        vbox.addWidget(self.progress)
        vbox.addWidget(self.tab_widget)
        self.setCentralWidget(container)

        # ── Status bar ────────────────────────────────────────────────────────
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._zoom_label = QLabel("100%")
        self._zoom_label.setStyleSheet("padding: 0 8px; font-size:11px;")
        self.status.addPermanentWidget(self._zoom_label)
        self._dl_label = QLabel("")
        self._dl_label.setStyleSheet("padding: 0 8px; font-size:11px; color:#a6e3a1;")
        self.status.addPermanentWidget(self._dl_label)

        # ── Connections ───────────────────────────────────────────────────────
        self.btn_back.clicked.connect(lambda: self._current_tab().back())
        self.btn_forward.clicked.connect(lambda: self._current_tab().forward())
        self.btn_refresh.clicked.connect(self._refresh)
        self.btn_home.clicked.connect(self._go_home)
        self.btn_go.clicked.connect(self._navigate)
        self.btn_new_tab.clicked.connect(self._new_tab)
        self.url_bar.returnPressed.connect(self._navigate)

        # ── Shortcuts ─────────────────────────────────────────────────────────
        QShortcut(QKeySequence("F5"),               self, self._refresh)
        QShortcut(QKeySequence("Ctrl+R"),           self, self._refresh)
        QShortcut(QKeySequence("Alt+Left"),         self, lambda: self._current_tab().back())
        QShortcut(QKeySequence("Alt+Right"),        self, lambda: self._current_tab().forward())
        QShortcut(QKeySequence("Ctrl+L"),           self, self._focus_url_bar)
        QShortcut(QKeySequence("Ctrl+,"),           self, self._open_settings)
        QShortcut(QKeySequence("Ctrl+T"),           self, self._new_tab)
        QShortcut(QKeySequence("Ctrl+W"),           self, self._close_current_tab)
        QShortcut(QKeySequence("Ctrl+Tab"),         self, self._next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"),   self, self._prev_tab)
        QShortcut(QKeySequence("Ctrl+F"),           self, self._show_find)
        QShortcut(QKeySequence("Ctrl+M"),           self, self._toggle_mute)
        QShortcut(QKeySequence("Ctrl+Plus"),        self, self._zoom_in)
        QShortcut(QKeySequence("Ctrl+Equal"),       self, self._zoom_in)
        QShortcut(QKeySequence("Ctrl+Minus"),       self, self._zoom_out)
        QShortcut(QKeySequence("Ctrl+0"),           self, self._zoom_reset)
        QShortcut(QKeySequence("Ctrl+S"),           self, self._take_screenshot)
        QShortcut(QKeySequence("Ctrl+H"),           self, self._open_history)
        QShortcut(QKeySequence("Ctrl+J"),           self, self._open_downloads)
        for i in range(1, 9):
            QShortcut(QKeySequence(f"Ctrl+{i}"), self,
                      lambda _, n=i-1: self.tab_widget.setCurrentIndex(n))
        QShortcut(QKeySequence("Escape"), self, self._on_escape)

        # ── Apply theme & open startup ────────────────────────────────────────
        self._apply_theme()
        self._open_startup()

    # ── Startup ───────────────────────────────────────────────────────────────
    def _open_startup(self):
        mode = self.settings.get("startup")
        if mode == "session":
            urls = self._load_session()
            if urls:
                for url in urls:
                    self._new_tab(url=QUrl(url))
                return
        if mode == "url":
            u = self.settings.get("startup_url")
            if u:
                self._new_tab(url=QUrl(u)); return
        self._new_tab(url=QUrl(self._home_url()))

    def _save_session(self):
        urls = []
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            u = tab.current_url().toString()
            if u and not u.startswith("file://"):
                urls.append(u)
        SESSION_FILE.write_text(json.dumps(urls))

    def _load_session(self) -> list:
        if SESSION_FILE.exists():
            try: return json.loads(SESSION_FILE.read_text())
            except: pass
        return []

    def closeEvent(self, e):
        self._save_session()
        super().closeEvent(e)

    # ── Tab management ────────────────────────────────────────────────────────
    def _new_tab(self, *, url: QUrl = None):
        if url is None:
            url = QUrl(self._home_url())
        font_size = self.settings.get("font_size")
        tab = BrowserTab(self._profile, url, font_size, self)
        idx = self.tab_widget.addTab(tab, "New Tab")
        self.tab_widget.setCurrentIndex(idx)

        tab.title_changed.connect(lambda t: self._on_tab_title_changed(t, tab))
        tab.url_changed.connect(lambda u: self._on_active_tab_url_changed(u, tab))
        tab.load_started.connect(lambda: self._on_tab_load_started(tab))
        tab.load_progress.connect(lambda v: self._on_active_tab_load_progress(v, tab))
        tab.load_finished.connect(lambda ok: self._on_tab_load_finished(ok, tab))
        tab.link_hovered.connect(lambda u: self._on_active_tab_link_hovered(u, tab))
        tab.favicon_changed.connect(lambda icon: self._on_favicon_changed(icon, tab))
        return tab

    def _close_tab(self, index: int):
        if self.tab_widget.count() == 1:
            self._new_tab()
        self.tab_widget.removeTab(index)

    def _close_current_tab(self):
        self._close_tab(self.tab_widget.currentIndex())

    def _next_tab(self):
        n = self.tab_widget.count()
        self.tab_widget.setCurrentIndex((self.tab_widget.currentIndex()+1) % n)

    def _prev_tab(self):
        n = self.tab_widget.count()
        self.tab_widget.setCurrentIndex((self.tab_widget.currentIndex()-1) % n)

    def _current_tab(self) -> BrowserTab:
        return self.tab_widget.currentWidget()

    # ── Spinner ───────────────────────────────────────────────────────────────
    def _on_tab_load_started(self, tab: BrowserTab):
        self._loading_tabs.add(id(tab))
        if not self._spinner_timer.isActive():
            self._spinner_timer.start()
        if tab is self._current_tab():
            self.progress.setValue(0)

    def _on_tab_load_finished(self, ok: bool, tab: BrowserTab):
        self._loading_tabs.discard(id(tab))
        if not self._loading_tabs:
            self._spinner_timer.stop()
        # Restore favicon
        idx = self.tab_widget.indexOf(tab)
        if idx != -1:
            icon = tab.webview.icon()
            if not icon.isNull():
                self.tab_widget.setTabIcon(idx, icon)
        if tab is self._current_tab():
            self.progress.setValue(0)
            self._update_nav_buttons(tab)
        # Record history
        url = tab.current_url().toString()
        title = tab.current_title()
        self.history.add(url, title)

    def _tick_spinner(self):
        self._spinner_frame = (self._spinner_frame + 1) % len(SPINNER_FRAMES)
        frame = SPINNER_FRAMES[self._spinner_frame]
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if id(tab) in self._loading_tabs:
                text = self.tab_widget.tabText(i)
                # Replace spinner char or prepend
                if text and text[0] in SPINNER_FRAMES:
                    text = frame + text[1:]
                else:
                    text = frame + " " + text[:20]
                self.tab_widget.setTabText(i, text)
                self.tab_widget.setTabIcon(i, QIcon())

    def _on_favicon_changed(self, icon: QIcon, tab: BrowserTab):
        idx = self.tab_widget.indexOf(tab)
        if idx == -1: return
        if id(tab) not in self._loading_tabs and not icon.isNull():
            self.tab_widget.setTabIcon(idx, icon)

    # ── Tab signal handlers ───────────────────────────────────────────────────
    def _on_tab_title_changed(self, title: str, tab: BrowserTab):
        idx = self.tab_widget.indexOf(tab)
        if idx == -1: return
        if id(tab) not in self._loading_tabs:
            label = (title[:20]+"…") if len(title) > 22 else (title or "New Tab")
            mute_mark = " 🔇" if tab.is_muted() else ""
            self.tab_widget.setTabText(idx, label + mute_mark)
            self.tab_widget.setTabToolTip(idx, title)
        if tab is self._current_tab():
            self.setWindowTitle(f"{title} — Cronix")

    def _on_active_tab_url_changed(self, url: QUrl, tab: BrowserTab):
        if tab is not self._current_tab(): return
        self.url_bar.setText(self._display_url(url))
        self._update_nav_buttons(tab)

    def _on_active_tab_load_progress(self, value: int, tab: BrowserTab):
        if tab is not self._current_tab(): return
        self.progress.setValue(value)

    def _on_active_tab_link_hovered(self, url: str, tab: BrowserTab):
        if tab is not self._current_tab(): return
        if url: self.status.showMessage(url, 3000)
        else:   self.status.clearMessage()

    def _on_tab_switched(self, index: int):
        tab = self.tab_widget.widget(index)
        if tab:
            self.url_bar.setText(self._display_url(tab.current_url()))
            self._update_nav_buttons(tab)
            title = tab.current_title() or "Cronix"
            self.setWindowTitle(f"{title} — Cronix")
            self.btn_mute.setChecked(tab.is_muted())
            self.btn_mute.setText("🔇" if tab.is_muted() else "🔊")
            zoom = int(tab.webview.zoomFactor() * 100)
            self._zoom_label.setText(f"{zoom}%")
            # Update find bar page
            tab.find_bar.set_page(tab.webview.page())

    # ── Downloads ─────────────────────────────────────────────────────────────
    def _on_download_requested(self, download: QWebEngineDownloadRequest):
        dl_dir = self.settings.get("downloads_dir")
        suggested = download.suggestedFileName()
        dest = os.path.join(dl_dir, suggested)
        download.setDownloadDirectory(dl_dir)
        download.setDownloadFileName(suggested)

        record = {"name": suggested, "path": dest,
                  "total": 0, "received": 0, "status": "Downloading"}
        self._downloads.append(record)
        self._dl_label.setText(f"⬇ {suggested[:30]}")

        download.receivedBytesChanged.connect(
            lambda: record.update({"received": download.receivedBytes(),
                                   "total": download.totalBytes()}))
        download.isFinishedChanged.connect(lambda: self._on_download_finished(download, record))
        download.accept()

    def _on_download_finished(self, download, record):
        state = download.state()
        if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            record["status"] = "Complete"
            self.status.showMessage(f"Downloaded: {record['name']}", 4000)
        else:
            record["status"] = "Cancelled"
        self._dl_label.setText("")

    # ── Navigation ────────────────────────────────────────────────────────────
    def _display_url(self, url: QUrl) -> str:
        s = url.toString().rstrip("/")
        home = self._home_url().rstrip("/")
        if s == home or s == home + "/index.html" or not s or s == "about:blank":
            return ""
        return url.toString()

    def _resolve_url(self, raw: str) -> str:
        if "://" not in raw:
            if " " in raw or "." not in raw:
                engine = self.settings.get("search_engine")
                tmpl = SEARCH_QUERY_URLS.get(engine, SEARCH_QUERY_URLS["Google"])
                return tmpl.format(raw.replace(" ", "+"))
            return "https://" + raw
        return raw

    def _navigate(self):
        raw = self.url_bar.text().strip()
        if not raw: return
        self._current_tab().navigate(QUrl(self._resolve_url(raw)))

    def _refresh(self):
        mods = QApplication.keyboardModifiers()
        if mods & Qt.KeyboardModifier.ShiftModifier:
            self._current_tab().reload_bypass()
        else:
            self._current_tab().reload()

    def _go_home(self):
        self._current_tab().navigate(QUrl(self._home_url()))

    def _focus_url_bar(self):
        self.url_bar.setFocus(); self.url_bar.selectAll()

    def _update_nav_buttons(self, tab: BrowserTab = None):
        tab = tab or self._current_tab()
        if tab:
            self.btn_back.setEnabled(tab.can_go_back())
            self.btn_forward.setEnabled(tab.can_go_forward())

    def _home_url(self) -> str:
        return SEARCH_ENGINES.get(self.settings.get("search_engine"), NEWTAB_PAGE)

    def _on_escape(self):
        tab = self._current_tab()
        if tab and tab.find_bar.isVisible():
            tab.find_bar.hide_bar()
        else:
            tab.webview.setFocus()

    # ── Features ──────────────────────────────────────────────────────────────
    def _show_find(self):
        tab = self._current_tab()
        if tab:
            tab.find_bar.show_bar()

    def _toggle_mute(self):
        tab = self._current_tab()
        if tab:
            muted = tab.toggle_mute()
            self.btn_mute.setChecked(muted)
            self.btn_mute.setText("🔇" if muted else "🔊")
            # Update tab label
            self._on_tab_title_changed(tab.current_title(), tab)

    def _zoom_in(self):
        tab = self._current_tab()
        if tab:
            tab.zoom_in()
            self._zoom_label.setText(f"{int(tab.webview.zoomFactor()*100)}%")

    def _zoom_out(self):
        tab = self._current_tab()
        if tab:
            tab.zoom_out()
            self._zoom_label.setText(f"{int(tab.webview.zoomFactor()*100)}%")

    def _zoom_reset(self):
        tab = self._current_tab()
        if tab:
            tab.zoom_reset()
            self._zoom_label.setText("100%")

    def _take_screenshot(self):
        tab = self._current_tab()
        if not tab: return
        pixmap = tab.screenshot()
        # Copy to clipboard
        QApplication.clipboard().setPixmap(pixmap)
        # Also offer to save
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Screenshot",
            str(Path.home() / f"cronix_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"),
            "PNG (*.png);;JPEG (*.jpg)"
        )
        if path:
            pixmap.save(path)
            self.status.showMessage(f"Screenshot saved to {path}", 4000)
        else:
            self.status.showMessage("Screenshot copied to clipboard", 3000)

    # ── Dialogs ───────────────────────────────────────────────────────────────
    def _open_history(self):
        dlg = HistoryDialog(self.history, self)
        dlg.navigate_requested.connect(
            lambda u: self._current_tab().navigate(QUrl(u)))
        dlg.exec()

    def _open_downloads(self):
        dlg = DownloadsDialog(self._downloads, self)
        dlg.exec()

    def _open_cookies(self):
        dlg = CookieDialog(self._profile, self)
        dlg.exec()

    def _open_settings(self):
        dlg = SettingsDialog(self.settings, self.pw_manager, self)
        dlg.settings_changed.connect(self._apply_theme)
        dlg.exec()

    def _open_passwords_tab(self):
        dlg = SettingsDialog(self.settings, self.pw_manager, self)
        dlg.settings_changed.connect(self._apply_theme)
        dlg.tabs.setCurrentIndex(2)
        dlg.exec()

    def _open_about(self):
        AboutDialog(self).exec()

    # ── Theme ─────────────────────────────────────────────────────────────────
    def _apply_theme(self):
        p = palette(self.settings.get("theme"), self.settings.get("accent"))
        QApplication.instance().setStyleSheet(make_stylesheet(p))
        engine = self.settings.get("search_engine")
        self.url_bar.setPlaceholderText("Search Google or type URL")
        # Apply font size to existing tabs
        font_size = self.settings.get("font_size")
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, BrowserTab):
                tab.webview.settings().setFontSize(
                    QWebEngineSettings.FontSize.DefaultFontSize, font_size)


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Cronix")
    app.setDesktopFileName("cronix")
    app.setFont(QFont("Segoe UI", 10))

    from PyQt6.QtGui import QIcon
    for icon_path in [
        "/usr/share/pixmaps/cronix.png",
        "/usr/share/icons/hicolor/256x256/apps/cronix.png",
        "/usr/share/cronix/cronix_icon.png",
    ]:
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            break

    splash = SplashScreen()
    splash.show()
    app.processEvents()

    w = BrowserWindow()

    def _launch():
        splash.close()
        w.show()

    QTimer.singleShot(1500, _launch)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
