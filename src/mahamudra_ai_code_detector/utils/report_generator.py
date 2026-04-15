"""Report generation and aggregation of detection signals"""

from typing import List, Dict, Optional
from datetime import datetime
from mahamudra_ai_code_detector.models.detection_models import (
    CommitMetadata,
    DetectionSignal,
    FileAnalysis,
    RepositoryAnalysis,
    Report,
)


class ReportGenerator:
    """Generate comprehensive reports from detection signals"""

    def __init__(self):
        """Initialize report generator"""
        self.high_risk_threshold = 0.7
        self.medium_risk_threshold = 0.4

    def aggregate_file_score(self, file_path: str, signals: List[DetectionSignal]) -> float:
        """
        Aggregate detection signals into a single AI-likelihood score.
        
        Uses weighted average of signal confidences.
        
        Args:
            file_path: Path to the file
            signals: List of DetectionSignal objects
        
        Returns:
            AI-likelihood score (0-1)
        """
        if not signals:
            return 0.0
        
        # Weight different signal types
        weights = {
            "bot_author": 0.25,
            "change_velocity": 0.15,
            "large_commit": 0.15,
            "pr_pattern": 0.15,
            "comment_density": 0.10,
            "style_uniformity": 0.10,
            "repetition": 0.10,
            "similarity": 0.20,
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for signal in signals:
            signal_type = signal.signal_type.value
            weight = weights.get(signal_type, 0.1)
            weighted_sum += signal.confidence * weight
            total_weight += weight
        
        if total_weight > 0:
            return min(1.0, weighted_sum / total_weight)
        
        return 0.0

    def create_file_analysis(self, 
                           file_path: str,
                           signals: List[DetectionSignal],
                           commits: List[CommitMetadata]) -> FileAnalysis:
        """
        Create a FileAnalysis object for a single file.
        
        Args:
            file_path: Path to file
            signals: Detection signals for this file
            commits: Commits that modified this file
        
        Returns:
            FileAnalysis object
        """
        # Detect file language
        language = self._detect_language(file_path)
        
        # Calculate metrics
        total_insertions = sum(c.insertions for c in commits)
        total_deletions = sum(c.deletions for c in commits)
        
        # Get timestamps
        first_commit = min(commits, key=lambda c: c.timestamp) if commits else None
        last_commit = max(commits, key=lambda c: c.timestamp) if commits else None
        
        # Aggregate score
        ai_score = self.aggregate_file_score(file_path, signals)
        
        return FileAnalysis(
            file_path=file_path,
            language=language,
            ai_likelihood_score=ai_score,
            signals=signals,
            commit_count=len(commits),
            lines_added=total_insertions,
            lines_removed=total_deletions,
            first_seen=first_commit.timestamp if first_commit else None,
            last_modified=last_commit.timestamp if last_commit else None,
        )

    def create_repository_analysis(self,
                                  repo_path: str,
                                  repo_name: str,
                                  file_analyses: List[FileAnalysis],
                                  commits: List[CommitMetadata],
                                  bot_authors: Dict[str, List[str]]) -> RepositoryAnalysis:
        """
        Create a RepositoryAnalysis object.
        
        Args:
            repo_path: Path to repository
            repo_name: Repository name
            file_analyses: List of FileAnalysis objects
            commits: All commits in repository
            bot_authors: Dictionary of bot authors found
        
        Returns:
            RepositoryAnalysis object
        """
        # Count flagged files
        flagged_count = sum(1 for f in file_analyses if f.ai_likelihood_score > self.medium_risk_threshold)
        risk_percentage = (flagged_count / len(file_analyses) * 100) if file_analyses else 0.0
        
        # Collect suspicious commits
        suspicious_commits = [c for c in commits if c.is_bot_authored]
        
        # Flatten bot authors list
        all_bot_authors = []
        for tool, shas in bot_authors.items():
            all_bot_authors.append(tool)
        
        return RepositoryAnalysis(
            repo_path=repo_path,
            repo_name=repo_name,
            total_commits=len(commits),
            total_files=len(file_analyses),
            ai_flagged_files=flagged_count,
            ai_risk_percentage=risk_percentage,
            file_analyses=file_analyses,
            suspicious_commits=suspicious_commits,
            bot_authors=all_bot_authors,
        )

    def create_report(self, repo_analysis: RepositoryAnalysis) -> Report:
        """
        Create a comprehensive report from repository analysis.
        
        Args:
            repo_analysis: RepositoryAnalysis object
        
        Returns:
            Report object with findings and recommendations
        """
        # Categorize files by risk level
        high_risk = [f for f in repo_analysis.file_analyses 
                     if f.ai_likelihood_score > self.high_risk_threshold]
        medium_risk = [f for f in repo_analysis.file_analyses 
                       if self.medium_risk_threshold <= f.ai_likelihood_score <= self.high_risk_threshold]
        low_risk = [f for f in repo_analysis.file_analyses 
                    if f.ai_likelihood_score < self.medium_risk_threshold]
        
        # Sort by risk score
        high_risk.sort(key=lambda f: f.ai_likelihood_score, reverse=True)
        medium_risk.sort(key=lambda f: f.ai_likelihood_score, reverse=True)
        low_risk.sort(key=lambda f: f.ai_likelihood_score, reverse=True)
        
        # Generate summary
        summary = self._generate_summary(repo_analysis, high_risk, medium_risk, low_risk)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(repo_analysis, high_risk, medium_risk)
        
        methodology_notes = (
            "This report combines metadata analysis (bot detection, commit velocity), "
            "code-level heuristics (comments, style, repetition), and similarity matching "
            "to estimate AI involvement. Detection is probabilistic and may have false positives. "
            "Human review is recommended for files flagged as high-risk."
        )
        
        return Report(
            repository_analysis=repo_analysis,
            summary=summary,
            high_risk_files=high_risk,
            medium_risk_files=medium_risk,
            low_risk_files=low_risk,
            recommendations=recommendations,
            methodology_notes=methodology_notes,
        )

    def _generate_summary(self, repo_analysis: RepositoryAnalysis,
                         high_risk: List[FileAnalysis],
                         medium_risk: List[FileAnalysis],
                         low_risk: List[FileAnalysis]) -> str:
        """Generate summary text for the report"""
        return (
            f"Repository: {repo_analysis.repo_name}\n"
            f"Total commits analyzed: {repo_analysis.total_commits}\n"
            f"Total files analyzed: {repo_analysis.total_files}\n"
            f"AI-flagged files: {repo_analysis.ai_flagged_files} ({repo_analysis.ai_risk_percentage:.1f}%)\n"
            f"High-risk files: {len(high_risk)}\n"
            f"Medium-risk files: {len(medium_risk)}\n"
            f"Low-risk files: {len(low_risk)}\n"
            f"Bot authors detected: {', '.join(repo_analysis.bot_authors) if repo_analysis.bot_authors else 'None'}"
        )

    def _generate_recommendations(self, repo_analysis: RepositoryAnalysis,
                                 high_risk: List[FileAnalysis],
                                 medium_risk: List[FileAnalysis]) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []
        
        if len(high_risk) > 0:
            recommendations.append(
                f"Review {len(high_risk)} high-risk files for potential AI involvement. "
                "Prioritize code quality and security audits."
            )
        
        if repo_analysis.bot_authors:
            recommendations.append(
                f"Bot authors detected: {', '.join(repo_analysis.bot_authors)}. "
                "Verify these contributions comply with project policies."
            )
        
        if repo_analysis.ai_risk_percentage > 30:
            recommendations.append(
                f"Over 30% of files show AI indicators. Consider implementing "
                "AI contribution guidelines and approval workflows."
            )
        
        if len(repo_analysis.suspicious_commits) > 0:
            recommendations.append(
                f"Found {len(repo_analysis.suspicious_commits)} commits with unusual patterns. "
                "Review commit messages and diff sizes."
            )
        
        recommendations.append(
            "This is an aid for code review, not forensic proof. "
            "Always combine with manual review and team discussion."
        )
        
        return recommendations

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_to_lang = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".cs": "C#",
            ".cpp": "C++",
            ".c": "C",
            ".go": "Go",
            ".rs": "Rust",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
        }
        
        for ext, lang in ext_to_lang.items():
            if file_path.endswith(ext):
                return lang
        
        return "Unknown"
