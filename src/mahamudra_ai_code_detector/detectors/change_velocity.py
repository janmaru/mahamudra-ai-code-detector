"""Detector for suspicious commit velocity and change patterns"""

from typing import List, Dict, Optional
from statistics import mean, stdev
from mahamudra_ai_code_detector.models.detection_models import (
    CommitMetadata,
    DetectionSignal,
    DetectionSignalType,
)


class ChangeVelocityDetector:
    """Detect suspiciously large or fast changes indicating AI assistance"""

    def __init__(self, insertion_threshold: int = 500, burst_threshold: int = 5):
        """
        Initialize detector with thresholds.
        
        Args:
            insertion_threshold: Flag commits with more insertions than this
            burst_threshold: Flag when author adds this many large commits in short time
        """
        self.insertion_threshold = insertion_threshold
        self.burst_threshold = burst_threshold

    def detect_large_commit(self, commit: CommitMetadata) -> Optional[DetectionSignal]:
        """
        Check if a single commit is unusually large.
        
        Args:
            commit: CommitMetadata to analyze
        
        Returns:
            DetectionSignal if commit is suspiciously large, None otherwise
        """
        if commit.insertions > self.insertion_threshold:
            # Higher confidence for extremely large commits
            confidence = min(0.9, 0.5 + (commit.insertions / (self.insertion_threshold * 2)))
            
            return DetectionSignal(
                signal_type=DetectionSignalType.LARGE_COMMIT,
                confidence=confidence,
                description=f"Large single commit with {commit.insertions} insertions",
                details={
                    "insertions": commit.insertions,
                    "deletions": commit.deletions,
                    "files_changed": commit.files_changed,
                    "commit_sha": commit.sha,
                    "author": commit.author,
                },
            )
        
        return None

    def detect_burst_activity(self, commits: List[CommitMetadata], author: str) -> Optional[DetectionSignal]:
        """
        Detect burst activity: many large commits from one author in short time.
        
        Args:
            commits: All commits in repository
            author: Author to analyze
        
        Returns:
            DetectionSignal if suspicious burst activity detected
        """
        author_commits = [c for c in commits if c.author == author]
        
        if len(author_commits) < self.burst_threshold:
            return None
        
        # Sort by timestamp
        author_commits.sort(key=lambda c: c.timestamp)
        
        # Find consecutive large commits
        large_commits = [c for c in author_commits if c.insertions > self.insertion_threshold]
        
        if len(large_commits) >= self.burst_threshold:
            # Check if they're in a short time window
            time_diff = (large_commits[-1].timestamp - large_commits[0].timestamp).total_seconds()
            days_span = time_diff / (24 * 3600)
            
            if days_span > 0 and days_span < 7:  # Within a week
                avg_insertions = mean([c.insertions for c in large_commits])
                
                return DetectionSignal(
                    signal_type=DetectionSignalType.CHANGE_VELOCITY,
                    confidence=0.8,
                    description=f"Burst activity: {len(large_commits)} large commits in {days_span:.1f} days",
                    details={
                        "large_commit_count": len(large_commits),
                        "time_span_days": days_span,
                        "average_insertions": avg_insertions,
                        "author": author,
                        "commit_shas": [c.sha for c in large_commits],
                    },
                )
        
        return None

    def analyze_velocity_baseline(self, commits: List[CommitMetadata]) -> Dict[str, float]:
        """
        Calculate repository velocity baseline (median commit size).
        
        Args:
            commits: All commits in repository
        
        Returns:
            Dictionary with baseline statistics
        """
        if not commits:
            return {"median_insertions": 0, "median_deletions": 0, "median_files": 0}
        
        insertions = sorted([c.insertions for c in commits])
        deletions = sorted([c.deletions for c in commits])
        files = sorted([c.files_changed for c in commits])
        
        def median(lst):
            n = len(lst)
            if n == 0:
                return 0
            if n % 2 == 1:
                return lst[n // 2]
            return (lst[n // 2 - 1] + lst[n // 2]) / 2
        
        return {
            "median_insertions": median(insertions),
            "median_deletions": median(deletions),
            "median_files": median(files),
            "mean_insertions": mean(insertions) if insertions else 0,
            "stdev_insertions": stdev(insertions) if len(insertions) > 1 else 0,
        }

    def detect_outlier_commits(self, commits: List[CommitMetadata], std_threshold: float = 2.0) -> List[CommitMetadata]:
        """
        Find commits that are statistical outliers in size.
        
        Args:
            commits: All commits in repository
            std_threshold: Number of standard deviations to use as threshold
        
        Returns:
            List of outlier commits
        """
        if len(commits) < 3:
            return []
        
        insertions = [c.insertions for c in commits]
        mean_val = mean(insertions)
        std_val = stdev(insertions) if len(insertions) > 1 else 0
        
        if std_val == 0:
            return []
        
        threshold = mean_val + (std_threshold * std_val)
        outliers = [c for c in commits if c.insertions > threshold]
        
        return outliers
