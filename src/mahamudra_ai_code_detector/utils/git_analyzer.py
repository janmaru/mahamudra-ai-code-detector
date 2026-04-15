"""Git repository analyzer for extracting commit history and metadata"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from git import Repo as GitRepo
from git.exc import GitCommandError

from mahamudra_ai_code_detector.models.detection_models import (
    CommitMetadata,
    FileChange,
)


class GitAnalyzer:
    """Analyze Git repositories to extract metadata and history"""

    def __init__(self, repo_path: str):
        """
        Initialize Git analyzer for a repository.
        
        Args:
            repo_path: Path to the Git repository
        
        Raises:
            ValueError: If the path is not a valid Git repository
        """
        self.repo_path = Path(repo_path)
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a valid Git repository: {repo_path}")
        
        self.repo = GitRepo(str(self.repo_path))
        self._bot_signatures = self._load_bot_signatures()

    def _load_bot_signatures(self) -> Dict[str, List[str]]:
        """Load patterns that indicate bot/AI tool authorship"""
        return {
            "copilot": [
                "github-copilot",
                "copilot",
            ],
            "claude": [
                "claude-code",
                "claude code",
            ],
            "cursor": [
                "cursor",
            ],
            "chatgpt": [
                "chatgpt",
                "openai",
            ],
        }

    def get_all_commits(self) -> List[CommitMetadata]:
        """
        Extract all commits from repository history.
        
        Returns:
            List of CommitMetadata objects
        """
        commits = []
        try:
            for commit in self.repo.iter_commits():
                commits.append(self._parse_commit(commit))
        except GitCommandError as e:
            print(f"Error reading commits: {e}")
        
        return commits

    def get_commits_by_path(self, file_path: str, max_count: Optional[int] = None) -> List[CommitMetadata]:
        """
        Get commits that modified a specific file.
        
        Args:
            file_path: Path to file relative to repo root
            max_count: Maximum number of commits to return
        
        Returns:
            List of CommitMetadata objects for that file
        """
        commits = []
        try:
            for commit in self.repo.iter_commits(paths=file_path, max_count=max_count):
                commits.append(self._parse_commit(commit))
        except GitCommandError:
            pass
        
        return commits

    def _parse_commit(self, commit) -> CommitMetadata:
        """Parse a GitPython commit object into CommitMetadata"""
        # Extract co-authors from commit message
        co_authors = self._extract_co_authors(commit.message)
        
        # Count file changes
        files_changed = len(commit.stats.files)
        insertions = sum(f["insertions"] for f in commit.stats.files.values())
        deletions = sum(f["deletions"] for f in commit.stats.files.values())
        
        # Check if author is a bot
        is_bot = self._is_bot_author(commit.author.name + " " + commit.author.email)
        
        return CommitMetadata(
            sha=commit.hexsha,
            author=commit.author.name,
            author_email=commit.author.email,
            committer=commit.committer.name,
            committer_email=commit.committer.email,
            timestamp=datetime.fromtimestamp(commit.committed_date),
            message=commit.message,
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
            co_authors=co_authors,
            is_bot_authored=is_bot,
        )

    def _extract_co_authors(self, message: str) -> List[str]:
        """Extract Co-authored-by trailers from commit message"""
        co_authors = []
        pattern = r"Co-authored-by:\s*(.+?)\s*<(.+?)>"
        matches = re.finditer(pattern, message, re.IGNORECASE)
        for match in matches:
            co_authors.append(f"{match.group(1)} <{match.group(2)}>")
        return co_authors

    def _is_bot_author(self, author_info: str) -> bool:
        """Check if author matches known bot signatures"""
        author_lower = author_info.lower()
        for tool, patterns in self._bot_signatures.items():
            for pattern in patterns:
                if pattern in author_lower:
                    return True
        return False

    def get_file_changes(self, commit) -> List[FileChange]:
        """Get detailed file change information for a commit"""
        changes = []
        
        try:
            if commit.parents:
                parent = commit.parents[0]
                diffs = parent.diff(commit)
            else:
                # First commit - compare with empty tree
                diffs = commit.diff(None)
            
            for diff in diffs:
                file_path = diff.b_path or diff.a_path
                
                # Get line counts from stats
                stats = commit.stats.files.get(file_path, {})
                insertions = stats.get("insertions", 0)
                deletions = stats.get("deletions", 0)
                
                changes.append(
                    FileChange(
                        file_path=file_path,
                        insertions=insertions,
                        deletions=deletions,
                        additions=insertions,
                        is_added=(diff.new_file),
                        is_removed=(diff.deleted_file),
                        patch=diff.diff.decode("utf-8", errors="ignore") if diff.diff else None,
                    )
                )
        except GitCommandError:
            pass
        
        return changes

    def get_repo_info(self) -> Dict:
        """Get basic repository information"""
        return {
            "name": self.repo.remotes.origin.url.split("/")[-1].replace(".git", "") if self.repo.remotes else self.repo_path.name,
            "path": str(self.repo_path),
            "default_branch": self.repo.active_branch.name if self.repo.active_branch else "unknown",
            "total_commits": len(list(self.repo.iter_commits())),
        }

    def get_file_list(self) -> List[str]:
        """Get list of all tracked files in the repository"""
        try:
            return self.repo.git.ls_files().split("\n")
        except GitCommandError:
            return []
