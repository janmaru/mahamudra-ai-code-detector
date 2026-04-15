"""Detector for unnatural comment patterns typical of AI-generated code"""

import re
from typing import List, Optional, Dict
from mahamudra_ai_code_detector.models.detection_models import (
    DetectionSignal,
    DetectionSignalType,
)


class CommentAnalysisDetector:
    """Detect unnatural comment density and patterns in code"""

    def __init__(self, high_density_threshold: float = 0.3):
        """
        Initialize detector with thresholds.
        
        Args:
            high_density_threshold: Flag files with comment ratio above this (0-1)
        """
        self.high_density_threshold = high_density_threshold
        # Language-agnostic patterns (work with //, #, etc.)
        self.ai_comment_patterns = [
            r"(?://|#)\s+This\s+(function|class|method|module|code|script|variable)\s+(is|does|will|defines)",
            r"(?://|#)\s+Here\s+(we|I)\s+(define|create|initialize|set up)",
            r"(?://|#)\s+The\s+.*?\s+(function|class|method)\s+(takes|accepts|receives)",
            r"(?://|#)\s+Return.*?value",
            r"(?://|#)\s+Check\s+if",
            r"(?://|#)\s+Initialize.*?\s+(with|using)",
            r"(?://|#)\s+(?:TODO|FIXME|HACK|XXX)",
            r"(?://|#)\s+(?:Author:|Created:|Modified:)",
        ]

    def analyze_comment_density(self, code: str) -> Dict:
        """
        Calculate comment density and patterns in code.
        Supports Python (#), C-style (//), and block comments (/* */), etc.
        
        Args:
            code: Source code to analyze
        
        Returns:
            Dictionary with comment statistics
        """
        lines = code.split("\n")
        comment_lines = 0
        code_lines = 0
        blank_lines = 0
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # Track block comments /* */ for C#, Java, JavaScript.
            # Check end first so "/* ... */" on a single line is handled correctly,
            # and a "*/" marker does not stay active into the next line.
            if "*/" in stripped:
                in_block_comment = False
                comment_lines += 1
                continue

            if in_block_comment:
                comment_lines += 1
                continue

            if "/*" in stripped:
                in_block_comment = True
                comment_lines += 1
                continue
            
            if not stripped:
                blank_lines += 1
            # Support Python (#), C-style (//), and HTML/XML (<!-- -->)
            elif stripped.startswith(("#", "//", "<!--", "*")):
                comment_lines += 1
            else:
                code_lines += 1
        
        total_lines = code_lines + comment_lines + blank_lines
        if total_lines == 0:
            return {}
        
        density = comment_lines / (code_lines + comment_lines) if (code_lines + comment_lines) > 0 else 0
        
        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "blank_lines": blank_lines,
            "comment_density": density,
        }

    def detect_high_comment_density(self, code: str) -> Optional[DetectionSignal]:
        """
        Flag files with unusually high comment density.
        
        AI-generated code often has excessive, line-by-line explanations.
        
        Args:
            code: Source code to analyze
        
        Returns:
            DetectionSignal if high density detected
        """
        stats = self.analyze_comment_density(code)
        if not stats:
            return None
        
        density = stats.get("comment_density", 0)
        
        if density > self.high_density_threshold and stats["code_lines"] > 10:
            return DetectionSignal(
                signal_type=DetectionSignalType.COMMENT_DENSITY,
                confidence=min(0.75, 0.5 + density),
                description=f"Unusually high comment density: {density*100:.1f}%",
                details={
                    "comment_density": density,
                    "comment_lines": stats["comment_lines"],
                    "code_lines": stats["code_lines"],
                },
            )
        
        return None

    def detect_ai_comment_patterns(self, code: str) -> Optional[DetectionSignal]:
        """
        Detect comment patterns typical of AI assistants.
        
        AI tools often produce very specific, explanatory comments
        for each code block in a consistent format.
        
        Args:
            code: Source code to analyze
        
        Returns:
            DetectionSignal if AI-typical patterns detected
        """
        matches = 0
        
        for pattern in self.ai_comment_patterns:
            matches += len(re.findall(pattern, code, re.IGNORECASE | re.MULTILINE))
        
        # Also check for excessive "this" and "that" in comments
        comment_lines = [
            line for line in code.split("\n")
            if line.strip().startswith(("#", "//", "<!--", "*"))
        ]
        comment_text = " ".join(comment_lines).lower()
        
        high_frequency_words = ["this", "that", "the", "here"]
        word_frequencies = {
            word: comment_text.count(f" {word} ") 
            for word in high_frequency_words
        }
        
        avg_word_freq = sum(word_frequencies.values()) / len(word_frequencies)
        
        if matches >= 3 or (avg_word_freq > 5 and len(comment_lines) > 5):
            return DetectionSignal(
                signal_type=DetectionSignalType.COMMENT_DENSITY,
                confidence=0.7,
                description="Comments exhibit AI-typical explanatory patterns",
                details={
                    "pattern_matches": matches,
                    "comment_lines": len(comment_lines),
                    "word_frequencies": word_frequencies,
                },
            )
        
        return None

    def detect_comment_code_mismatch(self, code: str) -> Optional[DetectionSignal]:
        """
        Detect mismatches between comments and actual code.
        
        This can indicate AI hallucination where the tool
        generates comments that don't match the implementation.
        
        Args:
            code: Source code to analyze
        
        Returns:
            DetectionSignal if mismatch patterns detected
        """
        lines = code.split("\n")
        mismatches = 0
        comment_prefixes = ("#", "//", "<!--", "*")

        for i, line in enumerate(lines):
            if line.strip().startswith(comment_prefixes):
                comment = line.strip().lower()

                # Check next few lines for related code
                next_code_lines = [
                    lines[j].strip().lower()
                    for j in range(i+1, min(i+5, len(lines)))
                    if lines[j].strip() and not lines[j].strip().startswith(comment_prefixes)
                ]
                
                if not next_code_lines:
                    continue
                
                # Check for keyword mismatches
                comment_keywords = set(re.findall(r"\b\w{4,}\b", comment))
                code_keywords = set(re.findall(r"\b\w{4,}\b", " ".join(next_code_lines)))
                
                overlap = len(comment_keywords & code_keywords)
                if overlap == 0 and len(comment_keywords) > 2:
                    mismatches += 1
        
        if mismatches >= 3:
            return DetectionSignal(
                signal_type=DetectionSignalType.COMMENT_DENSITY,
                confidence=0.65,
                description=f"Detected {mismatches} comment-code mismatches",
                details={
                    "mismatch_count": mismatches,
                    "indicator": "Comments may not accurately describe following code",
                },
            )
        
        return None
