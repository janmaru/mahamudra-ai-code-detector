from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from mahamudra_ai_code_detector.detectors.bot_signatures import BotSignatureDetector
from mahamudra_ai_code_detector.detectors.comment_analysis import CommentAnalysisDetector
from mahamudra_ai_code_detector.detectors.repetition import RepetitionDetector
from mahamudra_ai_code_detector.detectors.style_uniformity import StyleUniformityDetector
from mahamudra_ai_code_detector.models.detection_models import Report
from mahamudra_ai_code_detector.utils.git_analyzer import GitAnalyzer
from mahamudra_ai_code_detector.utils.report_generator import ReportGenerator


MAX_FILE_BYTES = 1024 * 1024


@dataclass
class AnalysisProgress:
    current: int
    total: int
    phase: str


ProgressCallback = Callable[[AnalysisProgress], None]


class AnalysisService:
    """Wraps the detection pipeline behind a single run() call.

    Keeps the UI orchestrator free of any knowledge of detectors, git
    internals, or aggregation logic.
    """

    def __init__(
        self,
        bot_detector: Optional[BotSignatureDetector] = None,
        comment_detector: Optional[CommentAnalysisDetector] = None,
        style_detector: Optional[StyleUniformityDetector] = None,
        repetition_detector: Optional[RepetitionDetector] = None,
        report_generator: Optional[ReportGenerator] = None,
    ):
        self._bot = bot_detector or BotSignatureDetector()
        self._comments = comment_detector or CommentAnalysisDetector()
        self._style = style_detector or StyleUniformityDetector()
        self._repetition = repetition_detector or RepetitionDetector()
        self._report_gen = report_generator or ReportGenerator()

    def run(
        self,
        repo_path: Path,
        progress: Optional[ProgressCallback] = None,
    ) -> Report:
        """Run full pipeline for a repository and return a Report.

        Args:
            repo_path: Path to the git repository
            progress: Optional progress callback invoked during per-file analysis

        Returns:
            Report aggregating all detected signals
        """
        git_analyzer = GitAnalyzer(str(repo_path))

        if progress:
            progress(AnalysisProgress(0, 0, "Reading git history"))

        all_commits = git_analyzer.get_all_commits()
        file_list = git_analyzer.get_file_list()
        total = len(file_list)

        file_analyses = []
        for index, file_rel in enumerate(file_list):
            if progress and index % 25 == 0:
                progress(AnalysisProgress(index, total, "Analyzing files"))

            analysis = self._analyze_single_file(repo_path, file_rel, git_analyzer)
            if analysis is not None:
                file_analyses.append(analysis)

        if progress:
            progress(AnalysisProgress(total, total, "Aggregating report"))

        bot_authors = self._bot.get_bot_authors_in_commits(all_commits)
        repo_analysis = self._report_gen.create_repository_analysis(
            str(repo_path),
            repo_path.name,
            file_analyses,
            all_commits,
            bot_authors,
        )
        return self._report_gen.create_report(repo_analysis)

    def _analyze_single_file(
        self,
        repo_path: Path,
        file_rel: str,
        git_analyzer: GitAnalyzer,
    ):
        """Analyze a single file. Returns FileAnalysis or None on skip/error."""
        if not file_rel:
            return None

        full_path = repo_path / file_rel
        try:
            if not full_path.is_file():
                return None
            if full_path.stat().st_size > MAX_FILE_BYTES:
                return None
        except OSError:
            return None

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                code = f.read()
        except (UnicodeDecodeError, IOError, OSError):
            return None

        file_commits = git_analyzer.get_commits_by_path(file_rel)
        if not file_commits:
            return None

        signals = []
        try:
            comment_signal = self._comments.detect_high_comment_density(code)
            if comment_signal:
                signals.append(comment_signal)

            rep_signal = self._repetition.detect_high_line_repetition(code)
            if rep_signal:
                signals.append(rep_signal)

            boilerplate_signal = self._repetition.detect_boilerplate_patterns(code)
            if boilerplate_signal:
                signals.append(boilerplate_signal)
        except Exception:
            # Detectors are best-effort; never let a single file kill the run.
            pass

        try:
            return self._report_gen.create_file_analysis(file_rel, signals, file_commits)
        except Exception:
            return None
