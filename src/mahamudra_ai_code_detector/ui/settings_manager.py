from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from mahamudra_ai_code_detector.ui.constants import APP_DIR

if TYPE_CHECKING:
    import tkinter as tk
    from mahamudra_ai_code_detector.ui.app_context import AppContext

# In frozen mode, store settings next to the .exe (writable), not inside the bundle
if getattr(sys, "frozen", False):
    _SETTINGS_DIR = Path(sys.executable).resolve().parent
else:
    _SETTINGS_DIR = APP_DIR

SETTINGS_FILE = _SETTINGS_DIR / "settings.json"

_MAX_RECENT = 10


def load_settings(ctx: AppContext) -> str:
    """Load settings into ctx. Returns window geometry string."""
    if not SETTINGS_FILE.exists():
        return "1400x900"
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return "1400x900"

    ctx.ui_theme = data.get("ui_theme", "dark")

    last_repo = data.get("last_repo")
    if last_repo:
        p = Path(last_repo)
        if p.is_dir() and (p / ".git").exists():
            ctx.scan_dir = p

    ctx.recent_repos = [
        Path(r)
        for r in data.get("recent_repos", [])
        if Path(r).is_dir() and (Path(r) / ".git").exists()
    ]

    return data.get("window_geometry", "1400x900")


def save_settings(ctx: AppContext) -> None:
    data = {
        "window_geometry": ctx.root.geometry(),
        "last_repo": str(ctx.scan_dir) if ctx.scan_dir else None,
        "recent_repos": [str(r) for r in ctx.recent_repos],
        "ui_theme": ctx.ui_theme,
    }
    try:
        SETTINGS_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass


def push_recent_repo(ctx: AppContext, repo: Path) -> None:
    """Add repo to front of recent list, deduplicated, capped at _MAX_RECENT."""
    repo = repo.resolve()
    ctx.recent_repos = [r for r in ctx.recent_repos if r.resolve() != repo]
    ctx.recent_repos.insert(0, repo)
    ctx.recent_repos = ctx.recent_repos[:_MAX_RECENT]


def ensure_on_screen(root: tk.Tk) -> None:
    """If the saved geometry lands off-screen, recenter at (100, 100)."""
    try:
        import ctypes
        import ctypes.wintypes

        user32 = ctypes.windll.user32
        cx = root.winfo_x() + root.winfo_width() // 2
        cy = root.winfo_y() + root.winfo_height() // 2
        monitor = user32.MonitorFromPoint(ctypes.wintypes.POINT(cx, cy), 0)
        if not monitor:
            w = root.winfo_width()
            h = root.winfo_height()
            root.geometry(f"{w}x{h}+100+100")
    except Exception:
        pass
