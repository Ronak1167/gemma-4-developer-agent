"""
Refine paper and writeup text to strictly respect Kaggle's 3,000-word limit
while preserving 100% of the empirical facts, citations, equations, and tables.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

for filename in ("gemma4_swe_agent_kaggle_writeup.md", "gemma4_swe_agent_research_paper.md"):
    filepath = ROOT / "paper" / filename
    text = filepath.read_text(encoding="utf-8")
    orig_words = len(text.split())

    # Streamline Section 5.5 in Kaggle writeup
    if "BOUNDED SWE AGENT EXECUTION PIPELINE" in text:
        start_idx = text.find("### 5.5 Step-by-Step Bounded Execution Loop")
        end_idx = text.find("## 6. Empirical Evaluation and Benchmark Analysis")
        if start_idx != -1 and end_idx != -1:
            replacement_s55 = (
                "### 5.5 Bounded Execution Pipeline\n\n"
                "The operational loop proceeds systematically: (1) initialize with action-only prompt and problem issue; "
                "(2) enforce envelope bounds ($t < 300\\text{s}$, tool calls $\\le 28$); "
                "(3) trigger compaction at 14,336 tokens (interval 15) while retaining the Turn-1 test diff; "
                "(4) generate deduction within the 1,024-token reasoning budget; "
                "(5) strip thought delimiters between turns (`include_thoughts: false`); "
                "(6) validate minimal git diff upon `submit_patch()`; otherwise execute tool and recurse until resolved.\n\n---\n\n"
            )
            text = text[:start_idx] + replacement_s55 + text[end_idx:]

    # Streamline Abstract
    old_abs_target = "Deploying open-weight autonomous software engineering (SWE) agents"
    if old_abs_target in text:
        abs_start = text.find("## Abstract\n\n")
        abs_end = text.find("\n\n---\n\n## 1. Introduction")
        if abs_start != -1 and abs_end != -1:
            streamlined_abs = (
                "## Abstract\n\n"
                "Deploying open-weight autonomous software engineering (SWE) agents on commodity accelerators (e.g., NVIDIA L4 GPUs with INT4 weights) "
                "faces three acute bottlenecks: finite context limits, quantization-induced degeneration, and evaluation timeout boundaries. "
                "We present an empirical failure analysis and architectural stabilization framework for **Gemma 4 12B** (`gemma-4-12b-it-qat-w4a16-ct`) "
                "on the official 129-task SWE-bench benchmark. Through trajectory auditing of diagnostic runs, we formalize a three-part failure taxonomy: "
                "*(i)* **Reasoning Token Starvation**, where under-budgeted thinking channels trigger degenerate repetition loops (specifically, 511 repeating delimiter pairs "
                "spanning 14,308 characters at trajectory index 12 / ATIF step 13, causing a terminal $30,721 + 2,048 = 32,769 > 32,768$ context overflow); "
                "*(ii)* **Conversational Context Ballooning**, where discursive preambles consume $>25\\%$ of context capacity; and "
                "*(iii)* **Evaluation Wall-Clock Exhaustion**, where 15-minute task budgets allow 48 stalled tasks to exhaust the 12-hour global limit ($48 \\times 15\\text{m} = 720\\text{m}$), "
                "causing kernel timeout (`publicScore: null`). To resolve these failure modes, we introduce a bounded-rationality architecture featuring: "
                "*(1)* calibrated 1,024-token thinking budgeting with inter-turn thought stripping (`include_thoughts: false`); "
                "*(2)* strict action-only turn invariants; *(3)* a two-tier execution envelope (12-call target, 28-call / 5-minute cap) bounding 120-task runtime to 10 hours; and "
                "*(4)* Turn-1 regression test diff inspection. Our framework enables timeout-free evaluation, achieving an official Kaggle public score of 0.03."
            )
            text = text[:abs_start] + streamlined_abs + text[abs_end:]

    filepath.write_text(text, encoding="utf-8")
    new_words = len(text.split())
    print(f"{filename}: {orig_words} words -> {new_words} words (reduction: {orig_words - new_words})")
