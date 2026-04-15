"""Fingerprinting engine for code similarity detection"""

import hashlib
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CodeFingerprint:
    """Represents a fingerprint of a code chunk"""
    chunk_hash: str
    chunk_content: str
    line_start: int
    line_end: int
    file_path: str


class FingerprintingEngine:
    """Create and manage code fingerprints for similarity detection"""

    def __init__(self, window_size: int = 5, overlap: int = 2):
        """
        Initialize fingerprinting engine.
        
        Args:
            window_size: Number of lines per chunk
            overlap: Number of overlapping lines between consecutive chunks
        """
        self.window_size = window_size
        self.overlap = overlap

    def normalize_code_line(self, line: str) -> str:
        """
        Normalize a code line for fingerprinting.
        
        Remove whitespace variations but preserve structure.
        
        Args:
            line: Code line to normalize
        
        Returns:
            Normalized line
        """
        # Remove comments
        if "#" in line:
            line = line.split("#")[0]
        
        # Strip leading/trailing whitespace
        line = line.strip()
        
        # Normalize multiple spaces to single space
        line = " ".join(line.split())
        
        return line

    def create_chunks(self, code: str, file_path: str) -> List[CodeFingerprint]:
        """
        Split code into overlapping chunks and create fingerprints.
        
        Args:
            code: Source code
            file_path: Path to the file
        
        Returns:
            List of CodeFingerprint objects
        """
        lines = code.split("\n")
        fingerprints = []
        
        step = self.window_size - self.overlap
        
        for i in range(0, len(lines) - self.window_size + 1, step):
            chunk_lines = lines[i:i + self.window_size]
            
            # Normalize chunk
            normalized = [self.normalize_code_line(line) for line in chunk_lines]
            chunk_content = "\n".join(normalized)
            
            if chunk_content.strip():  # Only fingerprint non-empty chunks
                chunk_hash = self._hash_chunk(chunk_content)
                
                fingerprints.append(
                    CodeFingerprint(
                        chunk_hash=chunk_hash,
                        chunk_content=chunk_content,
                        line_start=i,
                        line_end=i + self.window_size,
                        file_path=file_path,
                    )
                )
        
        return fingerprints

    def _hash_chunk(self, chunk_content: str) -> str:
        """
        Create hash fingerprint of code chunk.
        
        Args:
            chunk_content: Normalized code chunk
        
        Returns:
            Hex hash string
        """
        return hashlib.sha256(chunk_content.encode()).hexdigest()[:16]

    def calculate_resemblance(self, fingerprints1: List[CodeFingerprint], 
                            fingerprints2: List[CodeFingerprint]) -> float:
        """
        Calculate resemblance score between two sets of fingerprints.
        
        Uses Jaccard similarity on fingerprint sets.
        
        Args:
            fingerprints1: First set of fingerprints
            fingerprints2: Second set of fingerprints
        
        Returns:
            Similarity score (0-1)
        """
        hashes1 = set(fp.chunk_hash for fp in fingerprints1)
        hashes2 = set(fp.chunk_hash for fp in fingerprints2)
        
        if not hashes1 and not hashes2:
            return 1.0
        if not hashes1 or not hashes2:
            return 0.0
        
        intersection = len(hashes1 & hashes2)
        union = len(hashes1 | hashes2)
        
        return intersection / union if union > 0 else 0.0

    def find_matching_fingerprints(self, fingerprints: List[CodeFingerprint], 
                                  index_fingerprints: List[CodeFingerprint]) -> List[Tuple[CodeFingerprint, CodeFingerprint]]:
        """
        Find matching fingerprints between code and an index.
        
        Args:
            fingerprints: Fingerprints from code being analyzed
            index_fingerprints: Fingerprints from reference index
        
        Returns:
            List of matching fingerprint pairs
        """
        index_hashes = {fp.chunk_hash: fp for fp in index_fingerprints}
        
        matches = []
        for fp in fingerprints:
            if fp.chunk_hash in index_hashes:
                matches.append((fp, index_hashes[fp.chunk_hash]))
        
        return matches

    def estimate_borrowed_code_ratio(self, code_fingerprints: List[CodeFingerprint],
                                    index_fingerprints: List[CodeFingerprint]) -> float:
        """
        Estimate what percentage of code matches the index.
        
        Args:
            code_fingerprints: Fingerprints from code being analyzed
            index_fingerprints: Fingerprints from reference index
        
        Returns:
            Ratio of matching fingerprints (0-1)
        """
        if not code_fingerprints:
            return 0.0
        
        matches = self.find_matching_fingerprints(code_fingerprints, index_fingerprints)
        
        return len(matches) / len(code_fingerprints)
