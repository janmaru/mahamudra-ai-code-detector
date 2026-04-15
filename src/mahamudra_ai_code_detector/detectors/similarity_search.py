"""Similarity search against known AI/FOSS patterns"""

from typing import List, Dict, Optional
from mahamudra_ai_code_detector.detectors.fingerprinting import (
    CodeFingerprint,
    FingerprintingEngine,
)
from mahamudra_ai_code_detector.models.detection_models import (
    DetectionSignal,
    DetectionSignalType,
)


class SimilaritySearchEngine:
    """Search code fingerprints against known AI/FOSS pattern indexes"""

    def __init__(self):
        """Initialize similarity search engine"""
        self.fingerprinting_engine = FingerprintingEngine()
        self.ai_pattern_index: List[CodeFingerprint] = []
        self.foss_pattern_index: List[CodeFingerprint] = []
        self.similarity_threshold = 0.7

    def load_ai_pattern_index(self, fingerprints: List[CodeFingerprint]):
        """
        Load known AI-generated code patterns.
        
        Args:
            fingerprints: List of fingerprints from known AI-generated samples
        """
        self.ai_pattern_index = fingerprints

    def load_foss_pattern_index(self, fingerprints: List[CodeFingerprint]):
        """
        Load known FOSS code patterns.
        
        Args:
            fingerprints: List of fingerprints from known FOSS projects
        """
        self.foss_pattern_index = fingerprints

    def search_ai_patterns(self, code_fingerprints: List[CodeFingerprint]) -> Dict:
        """
        Search code against known AI-generated patterns.
        
        Args:
            code_fingerprints: Fingerprints of code being analyzed
        
        Returns:
            Dictionary with search results
        """
        matches = self.fingerprinting_engine.find_matching_fingerprints(
            code_fingerprints, 
            self.ai_pattern_index
        )
        
        if not matches:
            return {
                "matches_found": False,
                "match_count": 0,
                "borrowed_ratio": 0.0,
                "matches": [],
            }
        
        borrowed_ratio = len(matches) / len(code_fingerprints) if code_fingerprints else 0.0
        
        return {
            "matches_found": True,
            "match_count": len(matches),
            "borrowed_ratio": borrowed_ratio,
            "matches": [
                {
                    "code_location": f"{m[0].file_path}:{m[0].line_start}-{m[0].line_end}",
                    "pattern_source": m[1].file_path,
                }
                for m in matches[:10]  # Limit to 10 results
            ],
        }

    def search_foss_patterns(self, code_fingerprints: List[CodeFingerprint]) -> Dict:
        """
        Search code against known FOSS patterns.
        
        Useful for license compliance checking.
        
        Args:
            code_fingerprints: Fingerprints of code being analyzed
        
        Returns:
            Dictionary with FOSS match results
        """
        matches = self.fingerprinting_engine.find_matching_fingerprints(
            code_fingerprints,
            self.foss_pattern_index
        )
        
        if not matches:
            return {
                "foss_matches_found": False,
                "match_count": 0,
                "matches": [],
            }
        
        return {
            "foss_matches_found": True,
            "match_count": len(matches),
            "matches": [
                {
                    "code_location": f"{m[0].file_path}:{m[0].line_start}-{m[0].line_end}",
                    "source_project": m[1].file_path,
                }
                for m in matches[:10]
            ],
        }

    def detect_ai_similarity(self, code: str, file_path: str) -> Optional[DetectionSignal]:
        """
        Check if code is similar to known AI-generated patterns.
        
        Args:
            code: Source code to analyze
            file_path: Path to the file
        
        Returns:
            DetectionSignal if significant similarity found
        """
        if not self.ai_pattern_index:
            return None
        
        fingerprints = self.fingerprinting_engine.create_chunks(code, file_path)
        search_results = self.search_ai_patterns(fingerprints)
        
        if search_results["borrowed_ratio"] > self.similarity_threshold:
            return DetectionSignal(
                signal_type=DetectionSignalType.SIMILARITY,
                confidence=min(0.9, 0.6 + search_results["borrowed_ratio"]),
                description=f"Code similar to known AI-generated patterns ({search_results['borrowed_ratio']*100:.1f}% match)",
                details={
                    "borrowed_ratio": search_results["borrowed_ratio"],
                    "match_count": search_results["match_count"],
                },
            )
        
        return None

    def detect_foss_similarity(self, code: str, file_path: str) -> Optional[DetectionSignal]:
        """
        Check if code is similar to known FOSS projects.
        
        This can indicate AI was trained on or derived from FOSS code.
        
        Args:
            code: Source code to analyze
            file_path: Path to the file
        
        Returns:
            DetectionSignal if FOSS similarity found
        """
        if not self.foss_pattern_index:
            return None
        
        fingerprints = self.fingerprinting_engine.create_chunks(code, file_path)
        search_results = self.search_foss_patterns(fingerprints)
        
        if search_results["foss_matches_found"]:
            match_ratio = search_results["match_count"] / len(fingerprints) if fingerprints else 0
            
            return DetectionSignal(
                signal_type=DetectionSignalType.SIMILARITY,
                confidence=0.65,
                description=f"Code similar to FOSS projects ({match_ratio*100:.1f}% match)",
                details={
                    "foss_match_ratio": match_ratio,
                    "match_count": search_results["match_count"],
                },
            )
        
        return None
