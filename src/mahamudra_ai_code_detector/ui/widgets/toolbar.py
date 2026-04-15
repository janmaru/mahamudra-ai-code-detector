from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from mahamudra_ai_code_detector.ui.constants import FONT, ICONS, get_version

if TYPE_CHECKING:
    from mahamudra_ai_code_detector.ui.app_context import AppContext


@dataclass
class ToolbarCommands:
    browse_repo: Callable[[], None]
    analyze: Callable[[], None]
    refresh: Callable[[], None]
    toggle_sidebar: Callable[[], None]
    toggle_ui_theme: Callable[[], None]
    quit: Callable[[], None]


class Toolbar:
    """Custom titlebar + main toolbar row. Mirrors md_viewer pattern."""

    def __init__(self, parent: tk.Tk, ctx: AppContext, commands: ToolbarCommands):
        self._ctx = ctx
        self._commands = commands
        colors = ctx.colors

        # Custom titlebar (single row with app name and version)
        self.titlebar = tk.Frame(parent, bg=colors["titlebar"], height=28)
        self.titlebar.pack(side=tk.TOP, fill=tk.X)
        self.titlebar.pack_propagate(False)

        tk.Label(
            self.titlebar,
            text=f"  Mahamudra AI Code Detector  {get_version()}",
            bg=colors["titlebar"],
            fg=colors["text"],
            font=(FONT, 9),
        ).pack(side=tk.LEFT)

        # Main toolbar row
        self.frame = tk.Frame(parent, bg=colors["toolbar"], height=40)
        self.frame.pack(side=tk.TOP, fill=tk.X)
        self.frame.pack_propagate(False)

        # Left: primary actions
        self.toggle_sidebar_btn = self._make_button(
            self.frame, ICONS["sidebar"], commands.toggle_sidebar, accent=True
        )
        self.toggle_sidebar_btn.pack(side=tk.LEFT, padx=(6, 2), pady=4)

        self._make_button(
            self.frame, f"{ICONS['browse']} Browse", commands.browse_repo
        ).pack(side=tk.LEFT, padx=2, pady=4)

        self._make_button(
            self.frame,
            f"{ICONS['analyze']} Analyze",
            commands.analyze,
            accent=True,
        ).pack(side=tk.LEFT, padx=2, pady=4)

        self._make_button(
            self.frame, f"{ICONS['refresh']} Refresh", commands.refresh
        ).pack(side=tk.LEFT, padx=2, pady=4)

        # Right: utility actions
        self._make_button(
            self.frame, ICONS["theme"], commands.toggle_ui_theme
        ).pack(side=tk.RIGHT, padx=(2, 6), pady=4)

        # Separator under toolbar
        self.separator = tk.Frame(parent, bg=colors["border"], height=1)
        self.separator.pack(side=tk.TOP, fill=tk.X)

    def _make_button(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable[[], None],
        accent: bool = False,
    ) -> tk.Label:
        colors = self._ctx.colors
        fg = colors["accent"] if accent else colors["text"]

        btn = tk.Label(
            parent,
            text=text,
            bg=colors["toolbar"],
            fg=fg,
            font=(FONT, 10),
            padx=10,
            pady=4,
            cursor="hand2",
        )

        def on_enter(_event: tk.Event) -> None:
            btn.config(bg=colors["btn_hover"])

        def on_leave(_event: tk.Event) -> None:
            btn.config(bg=colors["toolbar"])

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", lambda _e: command())
        return btn
