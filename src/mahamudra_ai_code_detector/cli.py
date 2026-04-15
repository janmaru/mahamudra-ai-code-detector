"""Main CLI entry point for AI code detector"""

import sys
from pathlib import Path
from typing import Optional
import click
from mahamudra_ai_code_detector.utils.git_analyzer import GitAnalyzer
from mahamudra_ai_code_detector.detectors.bot_signatures import BotSignatureDetector
from mahamudra_ai_code_detector.detectors.change_velocity import ChangeVelocityDetector
from mahamudra_ai_code_detector.detectors.pr_patterns import PRPatternDetector
from mahamudra_ai_code_detector.detectors.comment_analysis import CommentAnalysisDetector
from mahamudra_ai_code_detector.detectors.style_uniformity import StyleUniformityDetector
from mahamudra_ai_code_detector.detectors.repetition import RepetitionDetector
from mahamudra_ai_code_detector.detectors.similarity_search import SimilaritySearchEngine
from mahamudra_ai_code_detector.utils.report_generator import ReportGenerator
from mahamudra_ai_code_detector.utils.json_output import JSONOutputFormatter
from mahamudra_ai_code_detector.utils.cli_output import CLIOutputFormatter
from mahamudra_ai_code_detector.utils.index_manager import IndexManager


@click.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Choice(["cli", "json"]),
    default="cli",
    help="Output format (cli or json)",
)
@click.option(
    "--output-file",
    "-f",
    type=click.Path(),
    help="Write output to file instead of stdout",
)
@click.option(
    "--disable-similarity",
    is_flag=True,
    help="Disable similarity search (faster but less accurate)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output with more details",
)
def main(repo_path: str, output: str, output_file: Optional[str], 
         disable_similarity: bool, verbose: bool):
    """
    Analyze a Git repository to detect AI-generated code.
    
    \b
    REPO_PATH: Path to the Git repository to analyze
    
    Example:
        mahamudra-detector /path/to/repo --output json -f report.json
    """
    try:
        click.echo("🔍 Initializing AI code detector...", err=True)
        
        repo_path_obj = Path(repo_path).resolve()
        if not (repo_path_obj / ".git").exists():
            click.echo(
                click.style("❌ Error: Not a valid Git repository", fg="red"),
                err=True
            )
            sys.exit(1)
        
        # Initialize analyzers
        git_analyzer = GitAnalyzer(str(repo_path_obj))
        bot_detector = BotSignatureDetector()
        velocity_detector = ChangeVelocityDetector()
        pr_detector = PRPatternDetector()
        comment_detector = CommentAnalysisDetector()
        style_detector = StyleUniformityDetector()
        repetition_detector = RepetitionDetector()
        similarity_engine = SimilaritySearchEngine()
        report_gen = ReportGenerator()
        
        # Load indexes if similarity search is enabled
        if not disable_similarity:
            index_manager = IndexManager()
            index_manager.initialize_default_indexes()
            ai_index = index_manager.load_ai_index()
            foss_index = index_manager.load_foss_index()
            similarity_engine.load_ai_pattern_index(ai_index)
            similarity_engine.load_foss_pattern_index(foss_index)
        
        click.echo("📊 Extracting repository metadata...", err=True)
        
        # Get commits and files
        all_commits = git_analyzer.get_all_commits()
        file_list = git_analyzer.get_file_list()
        
        if verbose:
            click.echo(f"   Found {len(all_commits)} commits", err=True)
            click.echo(f"   Found {len(file_list)} files", err=True)
        
        click.echo("🔎 Running detection pipeline...", err=True)
        
        # Analyze each file
        file_analyses = []
        
        for file_path in file_list:
            try:
                # Skip binary and large files
                full_path = repo_path_obj / file_path
                if not full_path.is_file():
                    continue
                
                if full_path.stat().st_size > 1024 * 1024:  # Skip >1MB files
                    continue
                
                # Read file content
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        code = f.read()
                except (UnicodeDecodeError, IOError):
                    continue
                
                # Get commits for this file
                file_commits = git_analyzer.get_commits_by_path(file_path)
                
                signals = []
                
                # Run bot detection on ALL commits for this file
                # (AI code might have been introduced at any point)
                if file_commits:
                    for commit in file_commits:
                        bot_signal = bot_detector.detect(commit)
                        if bot_signal:
                            signals.append(bot_signal)
                            break  # Once we find a bot author, we're done
                
                comment_signal = comment_detector.detect_high_comment_density(code)
                if comment_signal:
                    signals.append(comment_signal)
                
                comment_signal2 = comment_detector.detect_ai_comment_patterns(code)
                if comment_signal2:
                    signals.append(comment_signal2)
                
                style_signal = style_detector.detect_overly_uniform_indentation(code)
                if style_signal:
                    signals.append(style_signal)
                
                rep_signal = repetition_detector.detect_high_line_repetition(code)
                if rep_signal:
                    signals.append(rep_signal)
                
                boilerplate_signal = repetition_detector.detect_boilerplate_patterns(code)
                if boilerplate_signal:
                    signals.append(boilerplate_signal)
                
                # Create file analysis
                file_analysis = report_gen.create_file_analysis(
                    file_path,
                    signals,
                    file_commits
                )
                file_analyses.append(file_analysis)
                
            except Exception as e:
                if verbose:
                    click.echo(f"   Warning analyzing {file_path}: {e}", err=True)
                continue
        
        if verbose:
            click.echo(f"   Analyzed {len(file_analyses)} files", err=True)
        
        click.echo("📈 Generating report...", err=True)
        
        # Get bot authors
        bot_authors = bot_detector.get_bot_authors_in_commits(all_commits)
        
        # Create analyses
        repo_analysis = report_gen.create_repository_analysis(
            str(repo_path_obj),
            repo_path_obj.name,
            file_analyses,
            all_commits,
            bot_authors,
        )
        
        # Generate final report
        report = report_gen.create_report(repo_analysis)
        
        # Format output
        if output == "json":
            result = JSONOutputFormatter.format_report(report)
        else:
            result = CLIOutputFormatter.format_report(report)
        
        # Write output
        if output_file:
            with open(output_file, "w") as f:
                f.write(result)
            click.echo(
                click.style(f"✅ Report written to {output_file}", fg="green"),
                err=True
            )
        else:
            click.echo(result)
        
    except Exception as e:
        click.echo(
            click.style(f"❌ Error: {e}", fg="red"),
            err=True
        )
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
