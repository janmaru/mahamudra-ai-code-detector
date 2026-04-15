"""JSON output formatter for reports"""

import json
from typing import Dict, Any
from datetime import datetime
from mahamudra_ai_code_detector.models.detection_models import Report


class JSONOutputFormatter:
    """Format reports as JSON for automation and CI integration"""

    @staticmethod
    def format_report(report: Report) -> str:
        """
        Convert Report object to JSON string.
        
        Args:
            report: Report object to format
        
        Returns:
            JSON string representation of report
        """
        report_dict = JSONOutputFormatter._report_to_dict(report)
        return json.dumps(report_dict, indent=2, default=str)

    @staticmethod
    def _report_to_dict(report: Report) -> Dict[str, Any]:
        """Convert Report to dictionary"""
        return {
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "repository": report.repository_analysis.repo_name,
                "repository_path": report.repository_analysis.repo_path,
            },
            "summary": {
                "total_commits": report.repository_analysis.total_commits,
                "total_files": report.repository_analysis.total_files,
                "ai_flagged_files": report.repository_analysis.ai_flagged_files,
                "ai_risk_percentage": round(report.repository_analysis.ai_risk_percentage, 2),
            },
            "risk_distribution": {
                "high_risk": len(report.high_risk_files),
                "medium_risk": len(report.medium_risk_files),
                "low_risk": len(report.low_risk_files),
            },
            "bot_authors_detected": report.repository_analysis.bot_authors,
            "high_risk_files": [
                JSONOutputFormatter._file_analysis_to_dict(f)
                for f in report.high_risk_files[:20]  # Limit to top 20
            ],
            "medium_risk_files": [
                JSONOutputFormatter._file_analysis_to_dict(f)
                for f in report.medium_risk_files[:20]
            ],
            "recommendations": report.recommendations,
            "methodology": report.methodology_notes,
        }

    @staticmethod
    def _file_analysis_to_dict(file_analysis) -> Dict[str, Any]:
        """Convert FileAnalysis to dictionary"""
        return {
            "file_path": file_analysis.file_path,
            "language": file_analysis.language,
            "ai_likelihood_score": round(file_analysis.ai_likelihood_score, 3),
            "commit_count": file_analysis.commit_count,
            "lines_added": file_analysis.lines_added,
            "lines_removed": file_analysis.lines_removed,
            "first_seen": file_analysis.first_seen.isoformat() if file_analysis.first_seen else None,
            "last_modified": file_analysis.last_modified.isoformat() if file_analysis.last_modified else None,
            "signals": [
                {
                    "type": signal.signal_type.value,
                    "confidence": round(signal.confidence, 3),
                    "description": signal.description,
                }
                for signal in file_analysis.signals
            ],
        }
