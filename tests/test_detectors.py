"""Unit tests for detection modules"""

import pytest
from mahamudra_ai_code_detector.detectors.comment_analysis import CommentAnalysisDetector
from mahamudra_ai_code_detector.detectors.style_uniformity import StyleUniformityDetector
from mahamudra_ai_code_detector.detectors.repetition import RepetitionDetector
from mahamudra_ai_code_detector.detectors.bot_signatures import BotSignatureDetector
from mahamudra_ai_code_detector.models.detection_models import CommitMetadata
from datetime import datetime


class TestCommentAnalysisDetector:
    """Test comment analysis detector"""

    def test_comment_density_calculation(self):
        code = """# This is a comment
x = 1
# Another comment
y = 2
# Yet another comment
z = 3"""
        
        detector = CommentAnalysisDetector()
        stats = detector.analyze_comment_density(code)
        
        assert stats["comment_lines"] == 3
        assert stats["code_lines"] == 3
        assert stats["comment_density"] == 0.5

    def test_high_comment_density_detection(self):
        code = "# Comment\nx = 1\n" * 100
        
        detector = CommentAnalysisDetector(high_density_threshold=0.4)
        signal = detector.detect_high_comment_density(code)
        
        assert signal is not None
        assert signal.confidence > 0.5


class TestStyleUniformityDetector:
    """Test style uniformity detector"""

    def test_naming_consistency(self):
        code = """def my_function():
    my_variable = 1
    another_var = 2
    return my_variable + another_var"""
        
        detector = StyleUniformityDetector()
        stats = detector.analyze_naming_consistency(code)
        
        assert stats["total_identifiers"] > 0
        assert stats["snake_case_ratio"] > 0.7

    def test_line_length_analysis(self):
        code = "x = 1\ny = 2\nz = 3\n"
        
        detector = StyleUniformityDetector()
        stats = detector.analyze_line_length(code)
        
        assert stats["line_count"] == 3
        assert stats["mean_length"] > 0


class TestRepetitionDetector:
    """Test repetition detector"""

    def test_repeated_lines_detection(self):
        code = """print("hello")
print("hello")
print("hello")
x = 1"""
        
        detector = RepetitionDetector()
        stats = detector.find_repeated_lines(code)
        
        assert stats["repeated_line_count"] >= 1

    def test_similarity_calculation(self):
        chunk1 = "def hello():\n    return 42"
        chunk2 = "def hello():\n    return 42"
        
        detector = RepetitionDetector()
        similarity = detector._calculate_similarity(chunk1, chunk2)
        
        assert similarity > 0.9


class TestBotSignatureDetector:
    """Test bot signature detector"""

    def test_copilot_detection(self):
        commit = CommitMetadata(
            sha="abc123",
            author="github-copilot[bot]",
            author_email="copilot@github.com",
            committer="github-copilot[bot]",
            committer_email="copilot@github.com",
            timestamp=datetime.now(),
            message="Auto-generated code",
            files_changed=5,
            insertions=100,
            deletions=10,
            is_bot_authored=False,
        )
        
        detector = BotSignatureDetector()
        signal = detector.detect(commit)
        
        assert signal is not None
        assert "Copilot" in signal.description

    def test_no_bot_detection(self):
        commit = CommitMetadata(
            sha="abc123",
            author="John Doe",
            author_email="john@example.com",
            committer="John Doe",
            committer_email="john@example.com",
            timestamp=datetime.now(),
            message="Manual code change",
            files_changed=1,
            insertions=10,
            deletions=2,
            is_bot_authored=False,
        )
        
        detector = BotSignatureDetector()
        signal = detector.detect(commit)
        
        assert signal is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
