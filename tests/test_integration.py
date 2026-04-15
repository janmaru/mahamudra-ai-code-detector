"""Integration tests for the detection pipeline"""

import pytest
import tempfile
from pathlib import Path
from mahamudra_ai_code_detector.utils.git_analyzer import GitAnalyzer
from mahamudra_ai_code_detector.detectors.bot_signatures import BotSignatureDetector
from mahamudra_ai_code_detector.utils.report_generator import ReportGenerator


class TestGitAnalyzer:
    """Test Git analyzer with real repository"""

    def test_git_repo_initialization(self, tmp_path):
        """Test initializing analyzer with a valid repo"""
        # Create a temporary git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        import subprocess
        subprocess.run(["git", "init"], cwd=str(repo_path), check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(repo_path),
            check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=str(repo_path),
            check=True
        )
        
        # Test analyzer initialization
        analyzer = GitAnalyzer(str(repo_path))
        assert analyzer.repo_path == repo_path

    def test_invalid_repo_raises_error(self):
        """Test that invalid repo path raises error"""
        with pytest.raises(ValueError):
            GitAnalyzer("/nonexistent/path")


class TestReportGenerator:
    """Test report generation"""

    def test_file_score_aggregation(self):
        from mahamudra_ai_code_detector.models.detection_models import DetectionSignal, DetectionSignalType
        
        signals = [
            DetectionSignal(
                signal_type=DetectionSignalType.COMMENT_DENSITY,
                confidence=0.8,
                description="High comment density",
                details={}
            ),
            DetectionSignal(
                signal_type=DetectionSignalType.REPETITION,
                confidence=0.6,
                description="Repetitive code",
                details={}
            ),
        ]
        
        gen = ReportGenerator()
        score = gen.aggregate_file_score("test.py", signals)
        
        assert 0 <= score <= 1
        assert score > 0  # Should have some non-zero score

    def test_language_detection(self):
        gen = ReportGenerator()
        
        assert gen._detect_language("test.py") == "Python"
        assert gen._detect_language("test.js") == "JavaScript"
        assert gen._detect_language("test.txt") == "Unknown"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
