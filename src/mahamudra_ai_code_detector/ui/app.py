from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from mahamudra_ai_code_detector.ui.app_context import AppContext
from mahamudra_ai_code_detector.ui.constants import (
    APP_DIR,
    DARK_COLORS,
    FONT,
    LIGHT_COLORS,
)
from mahamudra_ai_code_detector.ui.services.analysis_service import (
    AnalysisProgress,
    AnalysisService,
)
from mahamudra_ai_code_detector.ui.settings_manager import (
    ensure_on_screen,
    load_settings,
    push_recent_repo,
    save_settings,
)
from mahamudra_ai_code_detector.ui.widgets.analysis_panel import AnalysisPanel
from mahamudra_ai_code_detector.ui.widgets.sidebar import Sidebar
from mahamudra_ai_code_detector.ui.widgets.status_bar import StatusBar
from mahamudra_ai_code_detector.ui.widgets.toolbar import Toolbar, ToolbarCommands


class AIDetectorApp(tk.Tk):
    """Thin orchestrator. Wires context, service, and widgets. No business logic."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Mahamudra AI Code Detector")

        self._ctx = AppContext(root=self, colors=dict(DARK_COLORS))
        self._service = AnalysisService()

        geo = load_settings(self._ctx)
        self._apply_theme_colors()

        icon_path = APP_DIR / "app_icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except tk.TclError:
                pass

        self.configure(bg=self._ctx.colors["bg"])
        self.geometry(geo)
        self.update_idletasks()
        self.after(50, lambda: ensure_on_screen(self))

        self._ctx.analyze_repo = self._on_analyze
        self._ctx.load_repo = self._on_load_repo
        self._ctx.refresh_all = self._on_refresh
        self._ctx.save_settings = self._save_settings
        self._ctx.set_status = self._set_status
        self._ctx.toggle_sidebar = self._toggle_sidebar
        self._ctx.toggle_theme = self._toggle_theme

        self._apply_ttk_styles()
        self._build_layout()

        if self._ctx.scan_dir and self._ctx.scan_dir.exists():
            self._load_repo_into_ui(self._ctx.scan_dir, push_recent=False)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        commands = ToolbarCommands(
            browse_repo=self._on_browse,
            analyze=self._on_analyze,
            refresh=self._on_refresh,
            toggle_sidebar=self._toggle_sidebar,
            toggle_ui_theme=self._toggle_theme,
            quit=self.destroy,
        )
        self._toolbar = Toolbar(self, self._ctx, commands)

        self._status_bar = StatusBar(self, self._ctx)

        self._main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self._main_paned.pack(fill=tk.BOTH, expand=True)

        self._sidebar = Sidebar(
            self._main_paned,
            self._ctx,
            on_file_selected=self._on_file_selected,
            on_recent_selected=self._on_recent_selected,
        )
        self._sidebar_panel = self._sidebar.panel
        self._main_paned.add(self._sidebar_panel, weight=1)

        self._analysis_panel = AnalysisPanel(self._main_paned, self._ctx)
        self._main_paned.add(self._analysis_panel.panel, weight=3)

        self._sidebar.update_recent_list()

    def _apply_ttk_styles(self) -> None:
        colors = self._ctx.colors
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            background=colors["sidebar"],
            foreground=colors["text"],
            fieldbackground=colors["sidebar"],
            borderwidth=0,
            rowheight=22,
            font=(FONT, 10),
        )
        style.map(
            "Treeview",
            background=[("selected", colors["list_active"])],
            foreground=[("selected", colors["text_bright"])],
        )
        style.configure("TPanedwindow", background=colors["border"])
        style.configure("TFrame", background=colors["sidebar"])
        style.configure(
            "TLabel", background=colors["sidebar"], foreground=colors["text"]
        )
        style.configure(
            "Vertical.TScrollbar",
            background=colors["sidebar"],
            troughcolor=colors["bg"],
            borderwidth=0,
            arrowcolor=colors["text"],
        )

    def _apply_theme_colors(self) -> None:
        palette = DARK_COLORS if self._ctx.ui_theme == "dark" else LIGHT_COLORS
        self._ctx.colors.clear()
        self._ctx.colors.update(palette)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def _on_browse(self) -> None:
        folder = filedialog.askdirectory(title="Select Git Repository")
        if not folder:
            return
        repo = Path(folder)
        if not (repo / ".git").exists():
            messagebox.showerror(
                "Invalid Repository", "Selected folder is not a Git repository."
            )
            return
        self._load_repo_into_ui(repo, push_recent=True)

    def _on_load_repo(self, repo: Path) -> None:
        self._load_repo_into_ui(repo, push_recent=True)

    def _on_recent_selected(self, repo: Path) -> None:
        if not (repo / ".git").exists():
            messagebox.showerror(
                "Unavailable", f"Repository no longer available:\n{repo}"
            )
            self._ctx.recent_repos = [r for r in self._ctx.recent_repos if r != repo]
            self._sidebar.update_recent_list()
            self._save_settings()
            return
        self._load_repo_into_ui(repo, push_recent=True)

    def _on_file_selected(self, path: Path) -> None:
        self._ctx.current_file = path
        self._set_status(f"Selected: {path.name}")

    def _on_refresh(self) -> None:
        if self._ctx.scan_dir:
            self._load_repo_into_ui(self._ctx.scan_dir, push_recent=False)

    def _on_analyze(self) -> None:
        if self._ctx.analysis_running:
            return
        if not self._ctx.scan_dir:
            messagebox.showwarning(
                "No Repository", "Select a repository before running analysis."
            )
            return

        self._ctx.analysis_running = True
        self._analysis_panel.show_loading()
        self._set_status("Analyzing...")

        thread = threading.Thread(target=self._analyze_worker, daemon=True)
        thread.start()

    def _analyze_worker(self) -> None:
        try:
            repo_path = self._ctx.scan_dir
            if repo_path is None:
                return
            report = self._service.run(repo_path, progress=self._on_progress)
            self.after(0, lambda: self._on_analysis_done(report))
        except Exception as exc:
            message = str(exc)
            self.after(0, lambda: self._on_analysis_error(message))

    def _on_progress(self, progress: AnalysisProgress) -> None:
        text = (
            f"{progress.phase}: {progress.current}/{progress.total}"
            if progress.total
            else progress.phase
        )
        self.after(0, lambda t=text: self._set_status(t))

    def _on_analysis_done(self, report) -> None:
        self._ctx.analysis_running = False
        self._ctx.current_report = report
        self._analysis_panel.show_report(report)
        repo = report.repository_analysis
        self._set_status(
            f"Analysis complete — {repo.ai_flagged_files}/{repo.total_files} flagged"
        )

    def _on_analysis_error(self, message: str) -> None:
        self._ctx.analysis_running = False
        self._analysis_panel.show_empty()
        self._set_status(f"Error: {message}")
        messagebox.showerror("Analysis failed", message)

    # ------------------------------------------------------------------
    # Theme / sidebar toggles
    # ------------------------------------------------------------------

    def _toggle_theme(self) -> None:
        self._ctx.ui_theme = "light" if self._ctx.ui_theme == "dark" else "dark"
        self._apply_theme_colors()
        self._save_settings()
        self._rebuild_ui()

    def _toggle_sidebar(self) -> None:
        if self._ctx.left_visible:
            self._main_paned.forget(self._sidebar_panel)
            self._ctx.left_visible = False
        else:
            self._main_paned.insert(0, self._sidebar_panel, weight=1)
            self._ctx.left_visible = True

    def _rebuild_ui(self) -> None:
        """Tear down and rebuild after a theme change. Reuses existing context state."""
        current_report = self._ctx.current_report
        scan_dir = self._ctx.scan_dir

        for child in self.winfo_children():
            child.destroy()

        self.configure(bg=self._ctx.colors["bg"])
        self._apply_ttk_styles()
        self._build_layout()

        if scan_dir and scan_dir.exists():
            self._sidebar.load_folder(scan_dir)
            self._status_bar.set_repo(str(scan_dir))

        if current_report is not None:
            self._analysis_panel.show_report(current_report)
        else:
            self._analysis_panel.show_empty()

    # ------------------------------------------------------------------
    # Misc helpers
    # ------------------------------------------------------------------

    def _load_repo_into_ui(self, repo: Path, push_recent: bool) -> None:
        self._ctx.scan_dir = repo
        self._ctx.current_report = None
        self._analysis_panel.show_empty()
        self._sidebar.load_folder(repo)

        if push_recent:
            push_recent_repo(self._ctx, repo)
            self._sidebar.update_recent_list()
            self._save_settings()

        self._status_bar.set_repo(str(repo))
        self._set_status(f"Repository loaded: {repo.name}")

    def _set_status(self, text: str) -> None:
        self._status_bar.set_status(text)

    def _save_settings(self) -> None:
        save_settings(self._ctx)

    def _on_close(self) -> None:
        self._save_settings()
        self.destroy()


def main() -> None:
    app = AIDetectorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
