# mahamudra-ai-code-detector

Analyzes git repositories to estimate where AI coding assistants (GitHub Copilot, Claude Code, Cursor, ChatGPT-based tools) were likely involved in writing or editing code.

Intended as an **aid for code review and auditing** — not as forensic proof of authorship.

## Install

```bash
git clone https://github.com/yourusername/mahamudra-ai-code-detector.git
cd mahamudra-ai-code-detector
pip install -e .
```

Requires Python 3.9+.

## Usage

### CLI

```bash
# Terminal report
mahamudra-detector /path/to/repo

# JSON for automation
mahamudra-detector /path/to/repo --output json -f report.json

# Verbose
mahamudra-detector /path/to/repo -v
```

### Desktop GUI

```bash
python run_ui.py
```

Browse a repository in the left panel, click **Analyze Repository**, read risk distribution and flagged files in the right panel. Files are color-coded: 🟢 low (<40%), 🟡 medium (40-70%), 🔴 high (>70%).

## Example output

```
AI CODE DETECTION REPORT
Repository: my-project
Total files: 87
AI-flagged: 12 (13.8%)

Risk Distribution:
  High:   3
  Medium: 9
  Low:    75

HIGH-RISK FILES (>70% AI likelihood)
┌─────────────────────┬──────────┬──────────┬─────────┐
│ File                │ Language │ AI Score │ Signals │
├─────────────────────┼──────────┼──────────┼─────────┤
│ src/utils.py        │ Python   │ 82%      │ 4       │
│ src/parser.py       │ Python   │ 78%      │ 3       │
└─────────────────────┴──────────┴──────────┴─────────┘
```

## Testing

```bash
pytest tests/ -v
```

## Documentation

- [docs/analisi-tecnica.md](docs/analisi-tecnica.md) — architecture, pipeline, algorithms, configuration
- [docs/analisi-funzionale.md](docs/analisi-funzionale.md) — purpose, signals, risk levels, use cases, workflows

## License

MIT — see LICENSE.

## Disclaimer

This tool is provided for educational and compliance auditing. It is not a legal instrument and does not prove authorship. Always combine automated detection with human review.
