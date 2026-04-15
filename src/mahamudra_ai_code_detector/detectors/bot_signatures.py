"""Detector for AI tool and bot signatures in commit metadata"""

import yaml
from pathlib import Path
from typing import List, Dict, Optional
from mahamudra_ai_code_detector.models.detection_models import (
    CommitMetadata,
    DetectionSignal,
    DetectionSignalType,
)


class BotSignatureDetector:
    """Detect commits authored by known AI tools and bots"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize detector with bot signature rules.
        
        Args:
            config_path: Path to YAML config file with bot patterns. If None, use defaults.
        """
        if config_path and Path(config_path).exists():
            self.rules = self._load_config(config_path)
        else:
            self.rules = self._get_default_rules()

    def _get_default_rules(self) -> Dict:
        """Get default bot signature rules"""
        return {
            "bots": {
                "github-copilot": {
                    "author_patterns": [
                        "github-copilot",
                        "copilot",
                        "copilot[bot]",
                    ],
                    "email_patterns": [
                        "@users.noreply.github.com",
                    ],
                    "message_patterns": [],
                    "tool_name": "GitHub Copilot",
                },
                "claude-code": {
                    "author_patterns": [
                        "claude-code",
                        "claude code",
                        "anthropic",
                    ],
                    "email_patterns": [
                        "claude@anthropic.com",
                    ],
                    "message_patterns": [],
                    "tool_name": "Claude Code",
                },
                "cursor": {
                    "author_patterns": [
                        "cursor",
                    ],
                    "email_patterns": [
                        "cursor@",
                    ],
                    "message_patterns": [],
                    "tool_name": "Cursor",
                },
                "chatgpt": {
                    "author_patterns": [
                        "chatgpt",
                        "openai",
                    ],
                    "email_patterns": [
                        "chatgpt@openai.com",
                    ],
                    "message_patterns": [],
                    "tool_name": "ChatGPT",
                },
            }
        }

    def _load_config(self, config_path: str) -> Dict:
        """Load bot signature rules from YAML file"""
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or self._get_default_rules()

    def detect(self, commit: CommitMetadata) -> Optional[DetectionSignal]:
        """
        Check if a commit is authored by a known bot.
        
        Args:
            commit: CommitMetadata to analyze
        
        Returns:
            DetectionSignal if bot detected, None otherwise
        """
        bot_found, tool_name = self._match_patterns(commit)
        
        if bot_found:
            return DetectionSignal(
                signal_type=DetectionSignalType.BOT_AUTHOR,
                confidence=0.95,
                description=f"Commit authored by {tool_name}",
                details={
                    "author": commit.author,
                    "email": commit.author_email,
                    "tool": tool_name,
                    "commit_sha": commit.sha,
                },
            )
        
        return None

    def _match_patterns(self, commit: CommitMetadata) -> tuple[bool, str]:
        """
        Check if commit matches any bot signature pattern.
        
        Returns:
            Tuple of (is_bot, tool_name)
        """
        author_str = f"{commit.author} {commit.author_email}".lower()
        message_lower = commit.message.lower()
        
        for bot_id, rules in self.rules.get("bots", {}).items():
            # Check author patterns
            for pattern in rules.get("author_patterns", []):
                if pattern.lower() in author_str:
                    return True, rules.get("tool_name", bot_id)
            
            # Check email patterns
            for pattern in rules.get("email_patterns", []):
                if pattern.lower() in author_str:
                    return True, rules.get("tool_name", bot_id)
            
            # Check co-authors
            for co_author in commit.co_authors:
                co_author_lower = co_author.lower()
                for pattern in rules.get("author_patterns", []):
                    if pattern.lower() in co_author_lower:
                        return True, rules.get("tool_name", bot_id)
            
            # Check message patterns
            for pattern in rules.get("message_patterns", []):
                if pattern.lower() in message_lower:
                    return True, rules.get("tool_name", bot_id)
        
        return False, ""

    def get_bot_authors_in_commits(self, commits: List[CommitMetadata]) -> Dict[str, List[str]]:
        """
        Identify all bot authors in a list of commits.
        
        Args:
            commits: List of CommitMetadata objects
        
        Returns:
            Dictionary mapping tool names to list of commits
        """
        bot_commits = {}
        
        for commit in commits:
            bot_found, tool_name = self._match_patterns(commit)
            if bot_found:
                if tool_name not in bot_commits:
                    bot_commits[tool_name] = []
                bot_commits[tool_name].append(commit.sha)
        
        return bot_commits
