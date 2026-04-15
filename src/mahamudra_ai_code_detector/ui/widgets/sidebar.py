from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import TYPE_CHECKING, Callable, Optional

from mahamudra_ai_code_detector.ui.constants import FONT, ICONS, get_file_icon

if TYPE_CHECKING:
    from mahamudra_ai_code_detector.ui.app_context import AppContext


class Sidebar:
    """Left sidebar: recent repositories + file tree of current repo."""

    def __init__(
        self,
        parent: tk.Widget,
        ctx: AppContext,
        on_file_selected: Callable[[Path], None],
        on_recent_selected: Callable[[Path], None],
    ):
        self._ctx = ctx
        self._on_file_selected = on_file_selected
        self._on_recent_selected = on_recent_selected

        colors = ctx.colors

        self.panel = tk.Frame(parent, bg=colors["sidebar"], width=300)

        # Recent repos section
        self._build_recent_section()

        # Filter
        self._filter_var = tk.StringVar(value="")
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
        self._build_filter(colors)

        # File tree
        self._build_tree(colors)

        self._root_path: Optional[Path] = None

    # ------------------------------------------------------------------
    # Build helpers
    # ------------------------------------------------------------------

    def _build_recent_section(self) -> None:
        colors = self._ctx.colors

        header = tk.Label(
            self.panel,
            text="RECENT REPOSITORIES",
            bg=colors["sidebar"],
            fg=colors["secondary"],
            font=(FONT, 9, "bold"),
            anchor=tk.W,
            padx=10,
            pady=6,
        )
        header.pack(fill=tk.X)

        self._recent_frame = tk.Frame(self.panel, bg=colors["sidebar"])
        self._recent_frame.pack(fill=tk.X, padx=6)

        tk.Frame(self.panel, bg=colors["border"], height=1).pack(
            fill=tk.X, pady=(6, 0)
        )

    def _build_filter(self, colors: dict) -> None:
        header = tk.Label(
            self.panel,
            text="FILES",
            bg=colors["sidebar"],
            fg=colors["secondary"],
            font=(FONT, 9, "bold"),
            anchor=tk.W,
            padx=10,
            pady=6,
        )
        header.pack(fill=tk.X)

        entry = tk.Entry(
            self.panel,
            textvariable=self._filter_var,
            bg=colors["input_bg"],
            fg=colors["text"],
            insertbackground=colors["text"],
            borderwidth=0,
            font=(FONT, 10),
        )
        entry.pack(fill=tk.X, padx=8, pady=(0, 6), ipady=3)

    def _build_tree(self, colors: dict) -> None:
        tree_frame = tk.Frame(self.panel, bg=colors["sidebar"])
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._tree = ttk.Treeview(
            tree_frame,
            show="tree",
            selectmode="browse",
            yscrollcommand=scrollbar.set,
        )
        self._tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._tree.yview)

        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self._tree.bind("<Double-1>", self._on_tree_double_click)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_folder(self, folder_path: Path) -> None:
        self._root_path = folder_path
        self._tree.delete(*self._tree.get_children())

        root_id = self._tree.insert(
            "",
            "end",
            text=f"{ICONS['folder_open']} {folder_path.name}",
            open=True,
            values=[str(folder_path)],
        )
        self._build_tree_recursive(folder_path, root_id)
        self._apply_filter()

    def update_recent_list(self) -> None:
        colors = self._ctx.colors

        for widget in self._recent_frame.winfo_children():
            widget.destroy()

        if not self._ctx.recent_repos:
            tk.Label(
                self._recent_frame,
                text="(no recent repositories)",
                bg=colors["sidebar"],
                fg=colors["secondary"],
                font=(FONT, 9, "italic"),
                padx=6,
                pady=4,
            ).pack(anchor=tk.W)
            return

        for repo in self._ctx.recent_repos:
            row = tk.Label(
                self._recent_frame,
                text=f"{ICONS['folder']} {repo.name}",
                bg=colors["sidebar"],
                fg=colors["text"],
                font=(FONT, 10),
                anchor=tk.W,
                padx=6,
                pady=3,
                cursor="hand2",
            )
            row.pack(fill=tk.X)

            def on_enter(_e: tk.Event, w: tk.Label = row) -> None:
                w.config(bg=colors["hover"])

            def on_leave(_e: tk.Event, w: tk.Label = row) -> None:
                w.config(bg=colors["sidebar"])

            def on_click(_e: tk.Event, p: Path = repo) -> None:
                self._on_recent_selected(p)

            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)
            row.bind("<Button-1>", on_click)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_tree_recursive(self, path: Path, parent_id: str) -> None:
        try:
            items = sorted(
                path.iterdir(),
                key=lambda x: (not x.is_dir(), x.name.lower()),
            )
        except (PermissionError, OSError):
            return

        for item in items:
            if item.name.startswith(".") or item.name == "__pycache__":
                continue

            if item.is_dir():
                node_id = self._tree.insert(
                    parent_id,
                    "end",
                    text=f"{ICONS['folder']} {item.name}",
                    values=[str(item)],
                )
                self._build_tree_recursive(item, node_id)
            else:
                icon = get_file_icon(item.suffix)
                self._tree.insert(
                    parent_id,
                    "end",
                    text=f"{icon} {item.name}",
                    values=[str(item)],
                )

    def _apply_filter(self) -> None:
        query = self._filter_var.get().strip().lower()
        self._ctx.filter_query = query
        self._filter_recursive("", query)

    def _filter_recursive(self, node_id: str, query: str) -> bool:
        """Show nodes matching query (or any descendant matches). Returns True if kept."""
        children = self._tree.get_children(node_id)
        any_visible = False

        for child in children:
            values = self._tree.item(child, "values")
            text = self._tree.item(child, "text").lower()

            child_matches = not query or query in text
            descendant_visible = self._filter_recursive(child, query)

            if child_matches or descendant_visible:
                self._tree.reattach(child, node_id, "end")
                if descendant_visible:
                    self._tree.item(child, open=True)
                any_visible = True
            else:
                self._tree.detach(child)

        return any_visible

    def _on_tree_select(self, _event: tk.Event) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        values = self._tree.item(selection[0], "values")
        if values:
            path = Path(values[0])
            if path.is_file():
                self._on_file_selected(path)

    def _on_tree_double_click(self, event: tk.Event) -> None:
        item = self._tree.identify("item", event.x, event.y)
        if item:
            is_open = bool(self._tree.item(item, "open"))
            self._tree.item(item, open=not is_open)
