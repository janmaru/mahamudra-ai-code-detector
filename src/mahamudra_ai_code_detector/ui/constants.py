from __future__ import annotations

import sys
from pathlib import Path

# PyInstaller stores data files in sys._MEIPASS when running as a bundle
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    APP_DIR = Path(__file__).resolve().parent

FONT = "Segoe UI"
FONT_MONO = "Consolas"

DARK_COLORS = {
    "titlebar": "#323233",
    "toolbar": "#252526",
    "bg": "#1e1e1e",
    "panel": "#252526",
    "sidebar": "#252526",
    "border": "#3c3c3c",
    "text": "#cccccc",
    "text_bright": "#d4d4d4",
    "secondary": "#858585",
    "accent": "#007acc",
    "link": "#3794ff",
    "hover": "#2a2d2e",
    "list_active": "#37373d",
    "selection": "#264f78",
    "statusbar": "#007acc",
    "statusbar_text": "#ffffff",
    "input_bg": "#3c3c3c",
    "badge": "#4d4d4d",
    "btn_hover": "#3c3c3c",
    "risk_high": "#f14c4c",
    "risk_medium": "#e5c07b",
    "risk_low": "#4ec9b0",
    "signal": "#c586c0",
}

LIGHT_COLORS = {
    "titlebar": "#f3f3f3",
    "toolbar": "#ffffff",
    "bg": "#ffffff",
    "panel": "#f3f3f3",
    "sidebar": "#f3f3f3",
    "border": "#e5e5e5",
    "text": "#616161",
    "text_bright": "#333333",
    "secondary": "#909090",
    "accent": "#007acc",
    "link": "#005a9e",
    "hover": "#e8e8e8",
    "list_active": "#e2e2e2",
    "selection": "#add6ff",
    "statusbar": "#007acc",
    "statusbar_text": "#ffffff",
    "input_bg": "#ffffff",
    "badge": "#dfdfdf",
    "btn_hover": "#f0f0f0",
    "risk_high": "#d13438",
    "risk_medium": "#c98a1b",
    "risk_low": "#107c41",
    "signal": "#8e44ad",
}

ICONS = {
    ".md": "M\u2193",
    ".txt": "\u2261",
    ".py": "\u03bb",
    ".js": "JS",
    ".ts": "TS",
    ".tsx": "TS",
    ".jsx": "JS",
    ".json": "{}",
    ".yaml": "Y",
    ".yml": "Y",
    ".toml": "T",
    ".ini": "\u2630",
    ".cfg": "\u2630",
    ".java": "J",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".h": "h",
    ".go": "Go",
    ".rs": "Rs",
    ".rb": "Rb",
    ".php": "P",
    ".swift": "Sw",
    ".kt": "Kt",
    ".html": "<>",
    ".css": "#",
    ".sql": "S",
    ".sh": "$",
    ".ps1": "\u226b",
    ".csv": "\u2637",
    ".pdf": "\u25a0",
    ".png": "\u25a3",
    ".jpg": "\u25a3",
    ".jpeg": "\u25a3",
    ".gif": "\u25a3",
    "folder": "\u25b8",
    "folder_open": "\u25be",
    "analyze": "\u25b6",
    "refresh": "\u21bb",
    "theme": "\u25d0",
    "sidebar": "\u25a4",
    "search": "\u2315",
    "browse": "\u25a2",
    "risk_high": "\u25cf",
    "risk_medium": "\u25d0",
    "risk_low": "\u25cb",
    "signal": "\u25c6",
    "check": "\u2713",
    "cross": "\u2717",
}


def get_file_icon(extension: str) -> str:
    """Return the icon glyph for a file extension, or a default marker."""
    return ICONS.get(extension.lower(), "\u25a1")


def get_version() -> str:
    v_file = APP_DIR / "VERSION"
    if v_file.exists():
        return v_file.read_text(encoding="utf-8").strip()
    return "0.0.0"
