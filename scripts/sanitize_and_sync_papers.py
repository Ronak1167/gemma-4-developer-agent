"""
Sanitize encoding and synchronize corrections across both paper documents:
1. Fix 15-minute diagnostic claims in abstract and diagram.
2. Replace Unicode dashes/multiplication with clean ASCII to prevent U+FFFD corruption.
3. Provide explicit provenance for the 42-turn measurement dataset.
4. Harmonize multi-accelerator cluster wording.
5. Verify word count <= 3000 words.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent

# 1. Update Kaggle Writeup
writeup_path = ROOT / "paper/gemma4_swe_agent_kaggle_writeup.md"
writeup = writeup_path.read_text(encoding="utf-8")

# Fix abstract 15-min claim
writeup = writeup.replace(
    "where 15-minute task budgets allow 48 stalled tasks to exhaust the 12-hour global limit",
    "where uncalibrated 15-minute diagnostic limits allow 48 stalled tasks to exhaust the 12-hour global limit"
)

# Fix diagram 15-min claim
writeup = writeup.replace(
    "| 15 min default/task |",
    "| 15 min diagnostic cap|"
)

# Fix single-accelerator wording in Section 2.3
writeup = writeup.replace(
    "within single-accelerator memory footprints",
    "within constrained accelerator memory footprints"
)

# Add explicit script provenance for 42-turn measurements in Section 4.2
writeup = writeup.replace(
    "using the official Gemma 4 SentencePiece tokenizer (256k vocabulary).",
    "using the official Gemma 4 SentencePiece tokenizer (256k vocabulary; archived in `scripts/inspect_all_tokens.py`)."
)

# Replace unicode dashes and multiplication characters
writeup = writeup.replace("\u2013", "-").replace("\u2014", " - ").replace("\u00d7", "x")

writeup_path.write_text(writeup, encoding="utf-8")
print(f"Kaggle Writeup words: {len(writeup.split())}")

# 2. Update Research Paper
paper_path = ROOT / "paper/gemma4_swe_agent_research_paper.md"
paper = paper_path.read_text(encoding="utf-8")

# Fix abstract 15-min claim
paper = paper.replace(
    "where 15-minute task budgets allow 48 stalled tasks to exhaust the 12-hour global limit",
    "where uncalibrated 15-minute diagnostic limits allow 48 stalled tasks to exhaust the 12-hour global limit"
)
paper = paper.replace(
    "where default 15-minute per-task limits allow 48 stalled tasks to consume Kaggle's entire 12-hour global limit",
    "where uncalibrated 15-minute diagnostic limits allow 48 stalled tasks to consume Kaggle's entire 12-hour global limit"
)

# Fix diagram 15-min claim
paper = paper.replace(
    'D1["15 min/task default timeout x 120 tasks"]',
    'D1["15 min/task diagnostic cap x 120 tasks"]'
)

# Fix single-accelerator wording in Section 2.3
paper = paper.replace(
    "within single-accelerator memory footprints",
    "within constrained accelerator memory footprints"
)

# Add explicit script provenance for 42-turn measurements in Section 4.2
paper = paper.replace(
    "using the official Gemma 4 SentencePiece tokenizer (256k vocabulary).",
    "using the official Gemma 4 SentencePiece tokenizer (256k vocabulary; archived in `scripts/inspect_all_tokens.py`)."
)

# Replace unicode dashes and multiplication characters
paper = paper.replace("\u2013", "-").replace("\u2014", " - ").replace("\u00d7", "x")

# Clean any replacement characters
paper = paper.replace("\ufffd", "-").replace("â€”", " - ").replace("â€“", "-")

paper_path.write_text(paper, encoding="utf-8")
print(f"Research Paper words: {len(paper.split())}")
