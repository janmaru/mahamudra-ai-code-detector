"""Detector for code repetition and near-duplicate patterns"""

import hashlib
from typing import Optional, Dict, List, Tuple
from mahamudra_ai_code_detector.models.detection_models import (
    DetectionSignal,
    DetectionSignalType,
)


class RepetitionDetector:
    """Detect repetitive patterns and boilerplate typical of AI generation"""

    def __init__(self, min_chunk_size: int = 20, similarity_threshold: float = 0.8):
        """
        Initialize detector with thresholds.
        
        Args:
            min_chunk_size: Minimum lines to consider as a chunk
            similarity_threshold: Minimum similarity to flag as duplicate
        """
        self.min_chunk_size = min_chunk_size
        self.similarity_threshold = similarity_threshold

    def normalize_code(self, code: str) -> str:
        """
        Normalize code for comparison (remove whitespace variations).
        
        Args:
            code: Source code
        
        Returns:
            Normalized code
        """
        lines = code.split("\n")
        normalized = []
        for line in lines:
            # Remove leading/trailing whitespace but preserve structure
            normalized.append(line.strip())
        return "\n".join(line for line in normalized if line)

    def find_repeated_lines(self, code: str) -> Dict:
        """
        Find lines that appear multiple times in the code.
        
        Args:
            code: Source code to analyze
        
        Returns:
            Dictionary with repetition statistics
        """
        lines = [l.strip() for l in code.split("\n") if l.strip()]
        
        line_counts = {}
        for line in lines:
            if len(line) > 10:  # Only count non-trivial lines
                line_counts[line] = line_counts.get(line, 0) + 1
        
        repeated_lines = {line: count for line, count in line_counts.items() if count > 1}
        
        return {
            "total_lines": len(lines),
            "repeated_line_count": len(repeated_lines),
            "most_repeated": sorted(repeated_lines.items(), key=lambda x: x[1], reverse=True)[:5],
            "repetition_ratio": len(repeated_lines) / len(lines) if lines else 0,
        }

    def detect_high_line_repetition(self, code: str) -> Optional[DetectionSignal]:
        """
        Flag code with many repeated lines.
        
        Args:
            code: Source code to analyze
        
        Returns:
            DetectionSignal if high repetition detected
        """
        stats = self.find_repeated_lines(code)
        
        if stats["repetition_ratio"] > 0.3:
            return DetectionSignal(
                signal_type=DetectionSignalType.REPETITION,
                confidence=0.7,
                description=f"High line repetition: {stats['repetition_ratio']*100:.1f}% of lines are repeated",
                details={
                    "repeated_line_count": stats["repeated_line_count"],
                    "total_lines": stats["total_lines"],
                    "most_repeated": stats["most_repeated"],
                },
            )
        
        return None

    def find_similar_functions(self, code: str) -> List[Tuple[int, int, float]]:
        """
        Find similar code blocks/functions.
        
        Args:
            code: Source code to analyze
        
        Returns:
            List of (start_line, end_line, similarity) tuples
        """
        lines = code.split("\n")
        chunks = []
        
        # Limit chunks to prevent O(n²) explosion on large files.
        # Size the step so the sampling produces ~target_chunks chunks
        # evenly distributed across the whole file, avoiding bias toward
        # the beginning (the previous step=len/100 + chunks[:50] cap only
        # ever compared the first half of large files).
        target_chunks = 50
        available = max(1, len(lines) - self.min_chunk_size)
        step = max(1, available // target_chunks) if len(lines) > 100 else 1

        for i in range(0, len(lines) - self.min_chunk_size, step):
            chunk = "\n".join(lines[i:i + self.min_chunk_size])
            chunks.append((i, i + self.min_chunk_size, chunk))

        similarities = []

        # Safety cap: still bound pairwise comparisons to target_chunks.
        capped_chunks = chunks[:target_chunks]
        for i, (start1, end1, chunk1) in enumerate(capped_chunks):
            for start2, end2, chunk2 in capped_chunks[i+1:]:
                similarity = self._calculate_similarity(chunk1, chunk2)
                if similarity > self.similarity_threshold:
                    similarities.append((start1, start2, similarity))

        return similarities

    def _calculate_similarity(self, chunk1: str, chunk2: str) -> float:
        """
        Calculate similarity between two code chunks using Jaccard similarity.
        
        Args:
            chunk1: First code chunk
            chunk2: Second code chunk
        
        Returns:
            Similarity score (0-1)
        """
        norm1 = self.normalize_code(chunk1)
        norm2 = self.normalize_code(chunk2)
        
        # Use character n-grams for comparison
        def get_ngrams(text: str, n: int = 3) -> set:
            return set(text[i:i+n] for i in range(len(text)-n+1))
        
        ngrams1 = get_ngrams(norm1)
        ngrams2 = get_ngrams(norm2)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        
        return intersection / union if union > 0 else 0.0

    def detect_boilerplate_patterns(self, code: str) -> Optional[DetectionSignal]:
        """
        Detect repetitive boilerplate code.
        
        AI often generates the same boilerplate patterns multiple times.
        
        Args:
            code: Source code to analyze
        
        Returns:
            DetectionSignal if boilerplate patterns detected
        """
        similarities = self.find_similar_functions(code)
        
        if len(similarities) >= 3:
            avg_similarity = sum(s[2] for s in similarities) / len(similarities)
            
            return DetectionSignal(
                signal_type=DetectionSignalType.REPETITION,
                confidence=min(0.85, 0.6 + (avg_similarity - self.similarity_threshold) * 2),
                description=f"Detected {len(similarities)} similar code blocks (avg similarity: {avg_similarity:.2f})",
                details={
                    "similar_block_count": len(similarities),
                    "average_similarity": avg_similarity,
                    "examples": similarities[:3],  # Show first 3 examples
                },
            )
        
        return None

    def analyze_function_complexity(self, code: str) -> Dict:
        """
        Analyze code complexity metrics that might indicate AI generation.
        
        Args:
            code: Source code to analyze
        
        Returns:
            Dictionary with complexity statistics
        """
        lines = code.split("\n")
        
        # Count various structural elements
        function_defs = sum(1 for l in lines if l.strip().startswith("def "))
        class_defs = sum(1 for l in lines if l.strip().startswith("class "))
        conditional_blocks = sum(1 for l in lines if any(kw in l for kw in ["if ", "elif ", "else:"]))
        loop_blocks = sum(1 for l in lines if any(kw in l for kw in ["for ", "while "]))
        
        return {
            "function_count": function_defs,
            "class_count": class_defs,
            "conditional_count": conditional_blocks,
            "loop_count": loop_blocks,
            "average_function_length": len(lines) / (function_defs + 1) if function_defs > 0 else len(lines),
        }

    def detect_simplistic_implementation(self, code: str) -> Optional[DetectionSignal]:
        """
        Flag code that looks suspiciously simple or template-like.
        
        Args:
            code: Source code to analyze
        
        Returns:
            DetectionSignal if overly simplistic patterns detected
        """
        stats = self.analyze_function_complexity(code)
        
        # Check if code is mostly linear with few control structures
        total_structures = (
            stats["conditional_count"] + 
            stats["loop_count"] + 
            stats["class_count"]
        )
        
        lines = len(code.split("\n"))
        
        if lines > 50 and total_structures < lines * 0.05:
            return DetectionSignal(
                signal_type=DetectionSignalType.REPETITION,
                confidence=0.5,
                description="Code structure is suspiciously linear and template-like",
                details={
                    "total_lines": lines,
                    "control_structures": total_structures,
                    "structure_ratio": total_structures / lines if lines > 0 else 0,
                },
            )
        
        return None
