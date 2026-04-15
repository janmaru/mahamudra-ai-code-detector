from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from mahamudra_ai_code_detector.ui.constants import FONT

if TYPE_CHECKING:
    from mahamudra_ai_code_detector.ui.app_context import AppContext


class StatusBar:
    """Bottom status bar: free-form text + optional repo path."""

    def __init__(self, parent: tk.Widget, ctx: AppContext):
        self._ctx = ctx
        colors = ctx.colors

        self.frame = tk.Frame(parent, bg=colors["statusbar"], height=22)
        self.frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.frame.pack_propagate(False)

        self._text_var = tk.StringVar(value="Ready")
        self._repo_var = tk.StringVar(value="")

        tk.Label(
            self.frame,
            textvariable=self._text_var,
            bg=colors["statusbar"],
            fg=colors["statusbar_text"],
            font=(FONT, 9),
            anchor=tk.W,
            padx=10,
        ).pack(side=tk.LEFT)

        tk.Label(
            self.frame,
            textvariable=self._repo_var,
            bg=colors["statusbar"],
            fg=colors["statusbar_text"],
            font=(FONT, 9),
            anchor=tk.E,
            padx=10,
        ).pack(side=tk.RIGHT)

    def set_status(self, text: str) -> None:
        self._text_var.set(text)

    def set_repo(self, repo_path: str) -> None:
        self._repo_var.set(repo_path)
