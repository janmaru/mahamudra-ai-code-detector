"""Detector for suspicious PR patterns indicating AI contributions"""

from typing import List, Dict, Optional
from mahamudra_ai_code_detector.models.detection_models import (
    CommitMetadata,
    DetectionSignal,
    DetectionSignalType,
)


class PRPatternDetector:
    """Detect PR patterns suggestive of AI-generated code"""

    def __init__(self, min_files_threshold: int = 20, max_interaction_lines: int = 100):
        """
        Initialize detector with PR pattern thresholds.
        
        Args:
            min_files_threshold: Flag PRs that touch many files
            max_interaction_lines: Flag PRs with minimal discussion
        """
        self.min_files_threshold = min_files_threshold
        self.max_interaction_lines = max_interaction_lines

    def detect_one_shot_pr(self, commits: List[CommitMetadata]) -> Optional[DetectionSignal]:
        """
        Detect one-shot PRs: large amount of code added in minimal commits.
        
        This pattern is common in AI-generated code where the tool
        generates a complete feature in a single pass.
        
        Args:
            commits: All commits potentially in one PR branch
        
        Returns:
            DetectionSignal if one-shot PR pattern detected
        """
        if len(commits) == 0:
            return None
        
        # Check if commits are concentrated and large
        if len(commits) <= 3:  # Very few commits
            total_insertions = sum(c.insertions for c in commits)
            total_files = sum(c.files_changed for c in commits)
            
            if total_files >= self.min_files_threshold and total_insertions > 1000:
                return DetectionSignal(
                    signal_type=DetectionSignalType.PR_PATTERN,
                    confidence=0.75,
                    description=f"One-shot PR: {len(commits)} commits, {total_insertions} insertions, {total_files} files",
                    details={
                        "commit_count": len(commits),
                        "total_insertions": total_insertions,
                        "total_files": total_files,
                        "average_insertion_per_commit": total_insertions / len(commits),
                    },
                )
        
        return None

    def detect_no_interaction_pr(self, commit_messages: List[str]) -> Optional[DetectionSignal]:
        """
        Detect PRs with minimal commit messages suggesting lack of iteration.
        
        Args:
            commit_messages: Commit messages in the PR
        
        Returns:
            DetectionSignal if minimal interaction pattern detected
        """
        if not commit_messages:
            return None
        
        total_message_length = sum(len(msg) for msg in commit_messages)
        avg_message_length = total_message_length / len(commit_messages)
        
        # Check for very short, generic messages
        generic_patterns = [
            "update",
            "fix",
            "add",
            "remove",
            "refactor",
            "wip",
            "work in progress",
        ]
        
        generic_count = sum(
            1 for msg in commit_messages
            if any(pattern in msg.lower() for pattern in generic_patterns)
        )
        
        if avg_message_length < self.max_interaction_lines and generic_count >= len(commit_messages) * 0.7:
            return DetectionSignal(
                signal_type=DetectionSignalType.PR_PATTERN,
                confidence=0.6,
                description="Minimal interaction: generic commit messages with little explanation",
                details={
                    "average_message_length": avg_message_length,
                    "total_commits": len(commit_messages),
                    "generic_message_count": generic_count,
                },
            )
        
        return None

    def detect_large_single_commit_pr(self, commits: List[CommitMetadata]) -> Optional[DetectionSignal]:
        """
        Detect PRs where most code is in a single commit.
        
        This is typical of AI generation where the tool creates
        everything at once rather than iterative development.
        
        Args:
            commits: All commits in the PR
        
        Returns:
            DetectionSignal if large-single-commit pattern detected
        """
        if len(commits) < 2:
            return None
        
        total_insertions = sum(c.insertions for c in commits)
        if total_insertions == 0:
            return None
        
        # Find dominant commit
        max_commit = max(commits, key=lambda c: c.insertions)
        dominant_ratio = max_commit.insertions / total_insertions
        
        if dominant_ratio > 0.85 and total_insertions > 500:
            return DetectionSignal(
                signal_type=DetectionSignalType.PR_PATTERN,
                confidence=0.7,
                description=f"Large single-commit PR: {dominant_ratio*100:.0f}% of changes in one commit",
                details={
                    "dominant_commit_insertions": max_commit.insertions,
                    "total_insertions": total_insertions,
                    "dominant_ratio": dominant_ratio,
                    "total_commits": len(commits),
                    "dominant_commit_author": max_commit.author,
                },
            )
        
        return None

    def analyze_pr_structure(self, commits: List[CommitMetadata]) -> Dict:
        """
        Analyze overall PR structure and patterns.
        
        Args:
            commits: All commits in the PR
        
        Returns:
            Dictionary with structural analysis
        """
        if not commits:
            return {}
        
        total_insertions = sum(c.insertions for c in commits)
        total_deletions = sum(c.deletions for c in commits)
        total_files = sum(c.files_changed for c in commits)
        
        return {
            "commit_count": len(commits),
            "total_insertions": total_insertions,
            "total_deletions": total_deletions,
            "total_files_changed": total_files,
            "average_insertions_per_commit": total_insertions / len(commits) if commits else 0,
            "average_files_per_commit": total_files / len(commits) if commits else 0,
            "insertion_to_file_ratio": total_insertions / total_files if total_files > 0 else 0,
            "refactor_ratio": total_deletions / (total_insertions + total_deletions) if (total_insertions + total_deletions) > 0 else 0,
        }
