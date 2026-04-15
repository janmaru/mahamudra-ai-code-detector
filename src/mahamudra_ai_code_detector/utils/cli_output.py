"""Human-readable CLI output formatter"""

from typing import List
from colorama import Fore, Style, init
from tabulate import tabulate
from mahamudra_ai_code_detector.models.detection_models import Report, FileAnalysis


init(autoreset=True)


class CLIOutputFormatter:
    """Format reports for human-readable terminal output"""

    @staticmethod
    def format_report(report: Report) -> str:
        """
        Format Report as human-readable CLI output.
        
        Args:
            report: Report object to format
        
        Returns:
            Formatted string for terminal display
        """
        output = []
        
        # Header
        output.append(f"\n{Fore.CYAN}{'='*80}")
        output.append(f"{Fore.CYAN}AI CODE DETECTION REPORT")
        output.append(f"{Fore.CYAN}{'='*80}\n")
        
        # Repository info
        output.append(CLIOutputFormatter._format_summary(report))
        
        # Risk distribution
        output.append(CLIOutputFormatter._format_risk_distribution(report))
        
        # High-risk files
        if report.high_risk_files:
            output.append(CLIOutputFormatter._format_file_table(
                "HIGH-RISK FILES (>70% AI likelihood)",
                report.high_risk_files[:10],
                Fore.RED
            ))
        
        # Medium-risk files
        if report.medium_risk_files:
            output.append(CLIOutputFormatter._format_file_table(
                "MEDIUM-RISK FILES (40-70% AI likelihood)",
                report.medium_risk_files[:10],
                Fore.YELLOW
            ))
        
        # Bot authors
        if report.repository_analysis.bot_authors:
            output.append(CLIOutputFormatter._format_bot_authors(report))
        
        # Recommendations
        output.append(CLIOutputFormatter._format_recommendations(report))
        
        # Footer
        output.append(f"\n{Fore.CYAN}{'='*80}\n")
        
        return "\n".join(output)

    @staticmethod
    def _format_summary(report: Report) -> str:
        """Format repository summary"""
        analysis = report.repository_analysis
        
        lines = [
            f"{Fore.CYAN}Repository:{Style.RESET_ALL} {analysis.repo_name}",
            f"{Fore.CYAN}Path:{Style.RESET_ALL} {analysis.repo_path}",
            f"{Fore.CYAN}Total commits:{Style.RESET_ALL} {analysis.total_commits}",
            f"{Fore.CYAN}Total files:{Style.RESET_ALL} {analysis.total_files}",
            f"{Fore.CYAN}AI-flagged files:{Style.RESET_ALL} {analysis.ai_flagged_files} ({analysis.ai_risk_percentage:.1f}%)",
        ]
        
        return "\n".join(lines) + "\n"

    @staticmethod
    def _format_risk_distribution(report: Report) -> str:
        """Format risk level distribution"""
        high = len(report.high_risk_files)
        medium = len(report.medium_risk_files)
        low = len(report.low_risk_files)
        
        output = f"\n{Fore.CYAN}Risk Distribution:{Style.RESET_ALL}\n"
        
        if high > 0:
            output += f"  {Fore.RED}*{Style.RESET_ALL} High-risk:   {high}\n"
        if medium > 0:
            output += f"  {Fore.YELLOW}*{Style.RESET_ALL} Medium-risk: {medium}\n"
        if low > 0:
            output += f"  {Fore.GREEN}*{Style.RESET_ALL} Low-risk:    {low}\n"
        
        return output + "\n"

    @staticmethod
    def _format_file_table(title: str, files: List[FileAnalysis], color: str) -> str:
        """Format file analysis table"""
        output = f"\n{color}{title}{Style.RESET_ALL}\n"
        
        table_data = []
        for f in files:
            risk_color = CLIOutputFormatter._get_risk_color(f.ai_likelihood_score)
            score_str = f"{risk_color}{f.ai_likelihood_score:.2%}{Style.RESET_ALL}"
            
            signal_count = len(f.signals)
            
            table_data.append([
                f.file_path[:50],
                f.language or "Unknown",
                score_str,
                signal_count,
                f.commit_count,
            ])
        
        headers = ["File", "Language", "AI Score", "Signals", "Commits"]
        output += tabulate(table_data, headers=headers, tablefmt="grid")
        
        return output + "\n"

    @staticmethod
    def _format_bot_authors(report: Report) -> str:
        """Format bot authors section"""
        output = f"\n{Fore.RED}Bot Authors Detected:{Style.RESET_ALL}\n"
        
        for bot in report.repository_analysis.bot_authors:
            output += f"  {Fore.RED}*{Style.RESET_ALL} {bot}\n"
        
        return output + "\n"

    @staticmethod
    def _format_recommendations(report: Report) -> str:
        """Format recommendations section"""
        if not report.recommendations:
            return ""
        
        output = f"\n{Fore.CYAN}Recommendations:{Style.RESET_ALL}\n"
        
        for i, rec in enumerate(report.recommendations, 1):
            output += f"  {i}. {rec}\n"
        
        return output + "\n"

    @staticmethod
    def _get_risk_color(score: float) -> str:
        """Get color based on risk score"""
        if score > 0.7:
            return Fore.RED
        elif score > 0.4:
            return Fore.YELLOW
        else:
            return Fore.GREEN
