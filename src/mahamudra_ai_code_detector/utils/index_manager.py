"""Manage fingerprint indexes for AI/FOSS pattern databases"""

import json
import pickle
from pathlib import Path
from typing import List, Optional, Dict
from mahamudra_ai_code_detector.detectors.fingerprinting import CodeFingerprint


class IndexManager:
    """Manage fingerprint indexes for similarity search"""

    def __init__(self, index_dir: Optional[str] = None):
        """
        Initialize index manager.
        
        Args:
            index_dir: Directory to store index files. Defaults to ~/.mahamudra/indexes
        """
        if index_dir:
            self.index_dir = Path(index_dir)
        else:
            self.index_dir = Path.home() / ".mahamudra" / "indexes"
        
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.ai_index_path = self.index_dir / "ai_patterns.pkl"
        self.foss_index_path = self.index_dir / "foss_patterns.pkl"

    def save_ai_index(self, fingerprints: List[CodeFingerprint]):
        """
        Save AI pattern fingerprints to disk.
        
        Args:
            fingerprints: List of fingerprints to save
        """
        with open(self.ai_index_path, "wb") as f:
            pickle.dump(fingerprints, f)

    def load_ai_index(self) -> List[CodeFingerprint]:
        """
        Load AI pattern fingerprints from disk.
        
        Returns:
            List of fingerprints, or empty list if not found
        """
        if not self.ai_index_path.exists():
            return []
        
        with open(self.ai_index_path, "rb") as f:
            return pickle.load(f)

    def save_foss_index(self, fingerprints: List[CodeFingerprint]):
        """
        Save FOSS pattern fingerprints to disk.
        
        Args:
            fingerprints: List of fingerprints to save
        """
        with open(self.foss_index_path, "wb") as f:
            pickle.dump(fingerprints, f)

    def load_foss_index(self) -> List[CodeFingerprint]:
        """
        Load FOSS pattern fingerprints from disk.
        
        Returns:
            List of fingerprints, or empty list if not found
        """
        if not self.foss_index_path.exists():
            return []
        
        with open(self.foss_index_path, "rb") as f:
            return pickle.load(f)

    def export_index_metadata(self, fingerprints: List[CodeFingerprint], 
                             output_path: str):
        """
        Export index metadata as JSON for inspection.
        
        Args:
            fingerprints: List of fingerprints
            output_path: Path to save JSON metadata
        """
        metadata = {
            "fingerprint_count": len(fingerprints),
            "unique_files": len(set(fp.file_path for fp in fingerprints)),
            "fingerprints": [
                {
                    "hash": fp.chunk_hash,
                    "file": fp.file_path,
                    "lines": f"{fp.line_start}-{fp.line_end}",
                }
                for fp in fingerprints[:100]  # Limit to first 100 for readability
            ],
        }
        
        with open(output_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def get_index_stats(self) -> Dict:
        """
        Get statistics about currently loaded indexes.
        
        Returns:
            Dictionary with index statistics
        """
        ai_index = self.load_ai_index()
        foss_index = self.load_foss_index()
        
        return {
            "ai_patterns": {
                "fingerprint_count": len(ai_index),
                "unique_files": len(set(fp.file_path for fp in ai_index)),
                "exists": self.ai_index_path.exists(),
            },
            "foss_patterns": {
                "fingerprint_count": len(foss_index),
                "unique_files": len(set(fp.file_path for fp in foss_index)),
                "exists": self.foss_index_path.exists(),
            },
        }

    def initialize_default_indexes(self):
        """
        Create default (empty) indexes if they don't exist.
        
        This allows the tool to run without pre-built indexes.
        """
        if not self.ai_index_path.exists():
            self.save_ai_index([])
        
        if not self.foss_index_path.exists():
            self.save_foss_index([])
