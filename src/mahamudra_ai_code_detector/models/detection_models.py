"""Core data models for AI code detection using Pydantic"""

from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class DetectionSignalType(str, Enum):
    """Types of detection signals"""
    BOT_AUTHOR = "bot_author"
    CHANGE_VELOCITY = "change_velocity"
    LARGE_COMMIT = "large_commit"
    PR_PATTERN = "pr_pattern"
    COMMENT_DENSITY = "comment_density"
    STYLE_UNIFORMITY = "style_uniformity"
    REPETITION = "repetition"
    SIMILARITY = "similarity"


class CommitMetadata(BaseModel):
    """Information about a single commit"""
    sha: str
    author: str
    author_email: str
    committer: str
    committer_email: str
    timestamp: datetime
    message: str
    files_changed: int
    insertions: int
    deletions: int
    co_authors: List[str] = Field(default_factory=list)
    is_bot_authored: bool = False


class FileChange(BaseModel):
    """Information about a file change in a commit"""
    file_path: str
    insertions: int
    deletions: int
    additions: int
    is_added: bool
    is_removed: bool
    patch: Optional[str] = None


class DetectionSignal(BaseModel):
    """A single detection signal indicating potential AI involvement"""
    signal_type: DetectionSignalType
    confidence: float = Field(ge=0.0, le=1.0)
    description: str
    details: Dict = Field(default_factory=dict)


class FileAnalysis(BaseModel):
    """Analysis results for a single file"""
    file_path: str
    language: Optional[str] = None
    ai_likelihood_score: float = Field(default=0.0, ge=0.0, le=1.0)
    signals: List[DetectionSignal] = Field(default_factory=list)
    commit_count: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    first_seen: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    comments: Dict = Field(default_factory=dict)


class RepositoryAnalysis(BaseModel):
    """Complete analysis of a repository"""
    repo_path: str
    repo_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_commits: int = 0
    total_files: int = 0
    ai_flagged_files: int = 0
    ai_risk_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    file_analyses: List[FileAnalysis] = Field(default_factory=list)
    suspicious_commits: List[CommitMetadata] = Field(default_factory=list)
    bot_authors: List[str] = Field(default_factory=list)
    analysis_notes: str = ""


class Report(BaseModel):
    """Final report with findings and recommendations"""
    repository_analysis: RepositoryAnalysis
    summary: str
    high_risk_files: List[FileAnalysis] = Field(default_factory=list)
    medium_risk_files: List[FileAnalysis] = Field(default_factory=list)
    low_risk_files: List[FileAnalysis] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    methodology_notes: str = ""
