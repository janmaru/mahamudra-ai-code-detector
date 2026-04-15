from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Any, Optional

from mahamudra_ai_code_detector.ui.constants import FONT, ICONS

if TYPE_CHECKING:
    from mahamudra_ai_code_detector.models.detection_models import Report
    from mahamudra_ai_code_detector.ui.app_context import AppContext


class AnalysisPanel:
    """Right panel: summary header + risk distribution + file list.

    Rendering is pure — receives a Report, shows it. No business logic.
    """

    def __init__(self, parent: tk.Widget, ctx: AppContext):
        self._ctx = ctx
        colors = ctx.colors

        self.panel = tk.Frame(parent, bg=colors["bg"])

        # Header
        self._header = tk.Frame(self.panel, bg=colors["panel"], height=60)
        self._header.pack(fill=tk.X)
        self._header.pack_propagate(False)

        self._header_score = tk.Label(
            self._header,
            text="",
            bg=colors["panel"],
            fg=colors["text_bright"],
            font=(FONT, 20, "bold"),
        )
        self._header_score.pack(side=tk.LEFT, padx=16, pady=10)

        self._header_subtitle = tk.Label(
            self._header,
            text="",
            bg=colors["panel"],
            fg=colors["secondary"],
            font=(FONT, 10),
        )
        self._header_subtitle.pack(side=tk.LEFT, pady=10)

        tk.Frame(self.panel, bg=colors["border"], height=1).pack(fill=tk.X)

        # Scrollable body
        self._body_canvas = tk.Canvas(
            self.panel,
            bg=colors["bg"],
            highlightthickness=0,
            borderwidth=0,
        )
        self._body_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._scrollbar = ttk.Scrollbar(
            self.panel, orient=tk.VERTICAL, command=self._body_canvas.yview
        )
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._body_canvas.configure(yscrollcommand=self._scrollbar.set)

        self._body = tk.Frame(self._body_canvas, bg=colors["bg"])
        self._body_window = self._body_canvas.create_window(
            (0, 0), window=self._body, anchor=tk.NW
        )
        self._body.bind(
            "<Configure>",
            lambda _e: self._body_canvas.configure(
                scrollregion=self._body_canvas.bbox("all")
            ),
        )
        self._body_canvas.bind(
            "<Configure>",
            lambda e: self._body_canvas.itemconfigure(self._body_window, width=e.width),
        )

        self._show_empty_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_empty(self) -> None:
        self._clear_body()
        self._header_score.config(text="")
        self._header_subtitle.config(text="Ready")
        self._show_empty_state()

    def show_loading(self, message: str = "Analyzing repository...") -> None:
        self._clear_body()
        self._header_score.config(text="...")
        self._header_subtitle.config(text=message)

        colors = self._ctx.colors
        tk.Label(
            self._body,
            text=message,
            bg=colors["bg"],
            fg=colors["secondary"],
            font=(FONT, 11),
            pady=40,
        ).pack()

    def show_report(self, report: Report) -> None:
        self._clear_body()

        repo = report.repository_analysis
        pct = repo.ai_risk_percentage
        score_color = self._risk_color_for_pct(pct)

        self._header_score.config(text=f"{pct:.1f}%", fg=score_color)
        self._header_subtitle.config(
            text=(
                f"  {repo.repo_name}  "
                f"\u2022  {repo.ai_flagged_files}/{repo.total_files} flagged  "
                f"\u2022  {repo.total_commits} commits"
            )
        )

        self._build_distribution_card(report)
        self._build_bot_authors_card(repo)
        self._build_file_list("HIGH-RISK FILES", report.high_risk_files, "risk_high")
        self._build_file_list(
            "MEDIUM-RISK FILES", report.medium_risk_files[:30], "risk_medium"
        )
        self._build_recommendations(report)

    # ------------------------------------------------------------------
    # Internal — cards
    # ------------------------------------------------------------------

    def _show_empty_state(self) -> None:
        colors = self._ctx.colors
        tk.Label(
            self._body,
            text="Select a repository and run Analyze.",
            bg=colors["bg"],
            fg=colors["secondary"],
            font=(FONT, 11),
            pady=40,
        ).pack()

    def _build_distribution_card(self, report: Report) -> None:
        high = len(report.high_risk_files)
        medium = len(report.medium_risk_files)
        low = len(report.low_risk_files)
        total = max(1, high + medium + low)

        card = self._card("Risk Distribution")

        for label, count, color_key in (
            ("High", high, "risk_high"),
            ("Medium", medium, "risk_medium"),
            ("Low", low, "risk_low"),
        ):
            self._bar_row(card, label, count, total, color_key)

    def _build_bot_authors_card(self, repo: Any) -> None:
        colors = self._ctx.colors
        card = self._card("Bot Authors")

        bots = repo.bot_authors
        if not bots:
            tk.Label(
                card,
                text="No bot authors detected in commit history.",
                bg=colors["panel"],
                fg=colors["secondary"],
                font=(FONT, 10, "italic"),
                padx=12,
                pady=8,
                anchor=tk.W,
                justify=tk.LEFT,
            ).pack(fill=tk.X)
            return

        tk.Label(
            card,
            text=", ".join(bots),
            bg=colors["panel"],
            fg=colors["accent"],
            font=(FONT, 10),
            padx=12,
            pady=8,
            anchor=tk.W,
            justify=tk.LEFT,
        ).pack(fill=tk.X)

    def _build_file_list(self, title: str, files: list, color_key: str) -> None:
        if not files:
            return

        colors = self._ctx.colors
        card = self._card(f"{title}  ({len(files)})")

        for file_analysis in files:
            self._file_row(card, file_analysis, color_key)

    def _file_row(self, parent: tk.Widget, file_analysis: Any, color_key: str) -> None:
        colors = self._ctx.colors

        row = tk.Frame(parent, bg=colors["panel"])
        row.pack(fill=tk.X, padx=12, pady=4)

        score = file_analysis.ai_likelihood_score
        badge = tk.Label(
            row,
            text=f"{score * 100:.0f}%",
            bg=colors[color_key],
            fg="#ffffff",
            font=(FONT, 9, "bold"),
            padx=8,
            pady=2,
            width=5,
        )
        badge.pack(side=tk.LEFT, padx=(0, 8))

        info = tk.Frame(row, bg=colors["panel"])
        info.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(
            info,
            text=file_analysis.file_path,
            bg=colors["panel"],
            fg=colors["text_bright"],
            font=(FONT, 10),
            anchor=tk.W,
        ).pack(fill=tk.X)

        signals_text = ", ".join(
            s.signal_type.value for s in file_analysis.signals
        ) or "—"
        subtitle = (
            f"{file_analysis.language}  \u2022  "
            f"{file_analysis.commit_count} commits  \u2022  "
            f"signals: {signals_text}"
        )
        tk.Label(
            info,
            text=subtitle,
            bg=colors["panel"],
            fg=colors["secondary"],
            font=(FONT, 9),
            anchor=tk.W,
        ).pack(fill=tk.X)

    def _build_recommendations(self, report: Report) -> None:
        colors = self._ctx.colors
        if not report.recommendations:
            return

        card = self._card("Recommendations")
        for rec in report.recommendations:
            tk.Label(
                card,
                text=f"{ICONS['signal']}  {rec}",
                bg=colors["panel"],
                fg=colors["text"],
                font=(FONT, 10),
                anchor=tk.W,
                justify=tk.LEFT,
                wraplength=800,
                padx=12,
                pady=4,
            ).pack(fill=tk.X)

    # ------------------------------------------------------------------
    # Internal — primitives
    # ------------------------------------------------------------------

    def _card(self, title: str) -> tk.Frame:
        colors = self._ctx.colors

        wrapper = tk.Frame(self._body, bg=colors["bg"])
        wrapper.pack(fill=tk.X, padx=16, pady=(12, 0))

        tk.Label(
            wrapper,
            text=title,
            bg=colors["bg"],
            fg=colors["secondary"],
            font=(FONT, 9, "bold"),
            anchor=tk.W,
            padx=4,
            pady=4,
        ).pack(fill=tk.X)

        card = tk.Frame(wrapper, bg=colors["panel"])
        card.pack(fill=tk.X, pady=(0, 4))
        return card

    def _bar_row(
        self,
        parent: tk.Widget,
        label: str,
        count: int,
        total: int,
        color_key: str,
    ) -> None:
        colors = self._ctx.colors

        row = tk.Frame(parent, bg=colors["panel"])
        row.pack(fill=tk.X, padx=12, pady=4)

        tk.Label(
            row,
            text=label,
            bg=colors["panel"],
            fg=colors["text"],
            font=(FONT, 10),
            width=8,
            anchor=tk.W,
        ).pack(side=tk.LEFT)

        bar_container = tk.Frame(row, bg=colors["border"], height=14)
        bar_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 8))

        ratio = count / total if total else 0.0

        bar = tk.Frame(bar_container, bg=colors[color_key], height=14)
        bar.place(relx=0, rely=0, relwidth=ratio, relheight=1)

        tk.Label(
            row,
            text=str(count),
            bg=colors["panel"],
            fg=colors["text"],
            font=(FONT, 10),
            width=5,
            anchor=tk.E,
        ).pack(side=tk.LEFT)

    def _risk_color_for_pct(self, pct: float) -> str:
        colors = self._ctx.colors
        if pct >= 30:
            return colors["risk_high"]
        if pct >= 10:
            return colors["risk_medium"]
        return colors["risk_low"]

    def _clear_body(self) -> None:
        for child in self._body.winfo_children():
            child.destroy()
