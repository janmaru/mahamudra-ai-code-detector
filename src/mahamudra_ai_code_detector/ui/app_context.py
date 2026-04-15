from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    import tkinter as tk


@dataclass
class AppContext:
    root: tk.Tk
    colors: dict[str, str]

    # Repository state
    scan_dir: Optional[Path] = None
    current_file: Optional[Path] = None
    recent_repos: list[Path] = field(default_factory=list)

    # Analysis state
    current_report: Optional[Any] = None  # Report from report_generator
    analysis_running: bool = False

    # UI state
    ui_theme: str = "dark"
    left_visible: bool = True
    filter_query: str = ""

    # Callbacks (set by orchestrator)
    analyze_repo: Optional[Callable[[], None]] = None
    load_repo: Optional[Callable[[Path], None]] = None
    refresh_all: Optional[Callable[[], None]] = None
    save_settings: Optional[Callable[[], None]] = None
    show_toast: Optional[Callable[..., None]] = None
    update_recent_list: Optional[Callable[[], None]] = None
    clear_results: Optional[Callable[[], None]] = None
    set_status: Optional[Callable[[str], None]] = None
    toggle_sidebar: Optional[Callable[[], None]] = None
    toggle_theme: Optional[Callable[[], None]] = None
