"""Detector for code style uniformity and consistency patterns"""

import re
from typing import Optional, Dict, List
from mahamudra_ai_code_detector.models.detection_models import (
    DetectionSignal,
    DetectionSignalType,
)


class StyleUniformityDetector:
    """Detect overly uniform or perfect code style typical of AI generation"""

    def __init__(self, uniformity_threshold: float = 0.85):
        """
        Initialize detector with thresholds.
        
        Args:
            uniformity_threshold: Flag files with style uniformity above this
        """
        self.uniformity_threshold = uniformity_threshold

    def analyze_indentation(self, code: str) -> Dict:
        """
        Analyze indentation consistency.
        
        Args:
            code: Source code to analyze
        
        Returns:
            Dictionary with indentation statistics
        """
        lines = code.split("\n")
        indentation_levels = []
        indent_chars = {}
        
        for line in lines:
            if not line.strip():
                continue
            
            leading_spaces = len(line) - len(line.lstrip())
            indentation_levels.append(leading_spaces)
            
            # Check what character is used for indentation
            if line[0] == " ":
                indent_chars["spaces"] = indent_chars.get("spaces", 0) + 1
            elif line[0] == "\t":
                indent_chars["tabs"] = indent_chars.get("tabs", 0) + 1
        
        if not indentation_levels:
            return {}
        
        # Calculate uniformity (how consistent indentation is)
        from statistics import stdev, mean
        indent_stdev = stdev(indentation_levels) if len(indentation_levels) > 1 else 0
        indent_mean = mean(indentation_levels)
        
        uniformity = 1.0 - (indent_stdev / (indent_mean + 1))
        uniformity = max(0, min(1, uniformity))
        
        return {
            "indentation_levels": sorted(set(indentation_levels)),
            "indent_mean": indent_mean,
            "indent_stdev": indent_stdev,
            "uniformity": uniformity,
            "indent_chars": indent_chars,
        }

    def detect_overly_uniform_indentation(self, code: str) -> Optional[DetectionSignal]:
        """
        Flag code with suspiciously perfect indentation.
        
        Human code often has occasional indentation inconsistencies,
        while AI-generated code tends to be perfectly uniform.
        
        Args:
            code: Source code to analyze
        
        Returns:
            DetectionSignal if overly uniform indentation detected
        """
        stats = self.analyze_indentation(code)
        if not stats:
            return None
        
        uniformity = stats.get("uniformity", 0)
        
        if uniformity > self.uniformity_threshold and len(code.split("\n")) > 20:
            return DetectionSignal(
                signal_type=DetectionSignalType.STYLE_UNIFORMITY,
                confidence=0.6,
                description=f"Suspiciously uniform indentation: {uniformity*100:.1f}%",
                details={
                    "uniformity_score": uniformity,
                    "indentation_levels": stats["indentation_levels"],
                },
            )
        
        return None

    def analyze_naming_consistency(self, code: str) -> Dict:
        """
        Analyze identifier naming patterns and consistency.
        
        Args:
            code: Source code to analyze
        
        Returns:
            Dictionary with naming statistics
        """
        # Extract identifiers (variables, functions, classes)
        identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code)
        
        if not identifiers:
            return {}
        
        # Analyze naming conventions
        snake_case = sum(1 for i in identifiers if '_' in i and i.islower())
        camel_case = sum(1 for i in identifiers if any(c.isupper() for c in i[1:]))
        pascal_case = sum(1 for i in identifiers if i[0].isupper())
        
        total = len(identifiers)
        
        return {
            "total_identifiers": total,
            "snake_case_ratio": snake_case / total if total > 0 else 0,
            "camel_case_ratio": camel_case / total if total > 0 else 0,
            "pascal_case_ratio": pascal_case / total if total > 0 else 0,
        }

    def detect_inconsistent_naming(self, code: str) -> Optional[DetectionSignal]:
        """
        Detect mixed or overly consistent naming conventions.
        
        Perfect consistency is rare in human code; mixed conventions
        are also a red flag for AI assistance that doesn't adapt to codebase style.
        
        Args:
            code: Source code to analyze
        
        Returns:
            DetectionSignal if problematic naming patterns detected
        """
        stats = self.analyze_naming_consistency(code)
        if not stats or stats["total_identifiers"] < 10:
            return None
        
        ratios = [
            stats["snake_case_ratio"],
            stats["camel_case_ratio"],
            stats["pascal_case_ratio"],
        ]
        
        # Check for overly consistent single style (very high ratio)
        max_ratio = max(ratios)
        if max_ratio > 0.9:
            return DetectionSignal(
                signal_type=DetectionSignalType.STYLE_UNIFORMITY,
                confidence=0.55,
                description=f"Overly consistent naming convention: {max_ratio*100:.1f}% follow one style",
                details={
                    "snake_case_ratio": stats["snake_case_ratio"],
                    "camel_case_ratio": stats["camel_case_ratio"],
                    "pascal_case_ratio": stats["pascal_case_ratio"],
                },
            )
        
        # Check for completely mixed conventions
        non_zero_ratios = sum(1 for r in ratios if r > 0.1)
        if non_zero_ratios >= 3:
            return DetectionSignal(
                signal_type=DetectionSignalType.STYLE_UNIFORMITY,
                confidence=0.5,
                description="Highly inconsistent naming conventions",
                details={
                    "mixing_styles": non_zero_ratios,
                    "ratios": {
                        "snake_case": stats["snake_case_ratio"],
                        "camel_case": stats["camel_case_ratio"],
                        "pascal_case": stats["pascal_case_ratio"],
                    },
                },
            )
        
        return None

    def analyze_line_length(self, code: str) -> Dict:
        """
        Analyze code line length distribution.
        
        Args:
            code: Source code to analyze
        
        Returns:
            Dictionary with line length statistics
        """
        lines = [l for l in code.split("\n") if l.strip()]
        
        if not lines:
            return {}
        
        line_lengths = [len(line) for line in lines]
        
        from statistics import mean, stdev
        
        return {
            "mean_length": mean(line_lengths),
            "stdev_length": stdev(line_lengths) if len(line_lengths) > 1 else 0,
            "max_length": max(line_lengths),
            "min_length": min(line_lengths),
            "line_count": len(lines),
        }

    def detect_uniform_line_lengths(self, code: str) -> Optional[DetectionSignal]:
        """
        Flag code with suspiciously uniform line lengths.
        
        AI-generated code sometimes has very consistent line lengths.
        
        Args:
            code: Source code to analyze
        
        Returns:
            DetectionSignal if overly uniform line lengths detected
        """
        stats = self.analyze_line_length(code)
        if not stats or stats["line_count"] < 10:
            return None
        
        stdev_val = stats.get("stdev_length", 1)
        mean_val = stats.get("mean_length", 1)
        
        # Low variation coefficient indicates uniformity
        if mean_val > 0:
            variation_coefficient = stdev_val / mean_val
            if variation_coefficient < 0.15:
                return DetectionSignal(
                    signal_type=DetectionSignalType.STYLE_UNIFORMITY,
                    confidence=0.5,
                    description=f"Suspiciously uniform line lengths (variation: {variation_coefficient:.3f})",
                    details={
                        "mean_length": stats["mean_length"],
                        "stdev_length": stats["stdev_length"],
                        "variation_coefficient": variation_coefficient,
                    },
                )
        
        return None
