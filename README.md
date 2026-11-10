# Bounded Rationality in Autonomous Coding Agents: Gemma 4 12B on SWE-bench

[![Kaggle Competition](https://img.shields.io/badge/Kaggle-Gemma%204%20Developer%20Agent-20BEFF?logo=kaggle&logoColor=white)](https://www.kaggle.com/competitions/gemma-4-developer-agent)
[![Paper Track](https://img.shields.io/badge/Paper%20Track-Research%20Paper-blue?logo=googlescholar&logoColor=white)](https://www.kaggle.com/code/ronak1167/gemma-4-swe-agent-research-paper)
[![Leaderboard Score](https://img.shields.io/badge/Official%20Score-0.03-brightgreen)](https://www.kaggle.com/competitions/gemma-4-developer-agent/leaderboard)
[![Verified Hash](https://img.shields.io/badge/SHA--256-82a9478d...-success)](dist/submission.zip)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Official codebase and research paper repository for **Google – The Gemma 4 Developer Agent Competition** & **Paper Track** ($35,000 Prize Pool).

---

## 📌 Executive Summary

Deploying open-weight autonomous coding agents on single accelerators (NVIDIA L4 GPUs with INT4 weights) faces severe bottlenecks: finite 32k context windows, quantization-induced generation loops, and 12-hour global timeout limits. 

This repository presents our **Bounded-Rationality Architecture** for **Gemma 4 12B** (`gemma-4-12b-it-qat-w4a16-ct`), stabilizing agent execution under strict hardware and time boundaries:
1. **Calibrated Reasoning Compute:** 1,024-token thinking budget with inter-turn thought stripping (`include_thoughts: false`), preventing context pollution.
2. **Action-Only Turn Invariants:** Strict operational grammar stripping discursive filler, reducing assistant turn context cost from **480 to 112 tokens/turn**.
3. **Two-Tier Execution Envelope:** 12-call target in system prompt with a 28-call / 5-minute hard harness cap, formally bounding 120-task evaluation to 10 hours (preserving a 2-hour safety margin).
4. **Turn-1 Regression Test Inspection:** Immediate inspection of pre-injected regression diffs (`git diff -U3 -- tests/`) eliminating blind search loops.

**Result:** Resolved hidden SWE-bench tasks without kernel timeouts, achieving an official Kaggle public score of **`0.03`** (Candidate v23, Submission ID `58187123`).

---

## 🔬 Research Paper & Artifacts

* **Official Paper Notebook on Kaggle:** [ronak1167/gemma-4-swe-agent-research-paper](https://www.kaggle.com/code/ronak1167/gemma-4-swe-agent-research-paper)
* **Kaggle Writeup Submission:** [Kaggle Writeups](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/writeups)
* **Full Academic Manuscript:** [`paper/gemma4_swe_agent_research_paper.md`](paper/gemma4_swe_agent_research_paper.md)
* **Kaggle Web Writeup:** [`paper/gemma4_swe_agent_kaggle_writeup.md`](paper/gemma4_swe_agent_kaggle_writeup.md)
* **Verified Candidate Package:** [`dist/submission.zip`](dist/submission.zip)
  * Size: 3,704 bytes
  * SHA-256: `82a9478da291d5899e472b5b405156167b785e50c91ced9dadb8cf58a83d64f3`

---

## 🏗️ Architecture Overview

```
+---------------------------------------------------------------+
|         QUANTIZED GEMMA 4 SWE AGENT ON NVIDIA L4 (24GB)       |
+-------------------------------+-------------------------------+
                                |
        +-----------------------+-----------------------+
        |                       |                       |
        v                       v                       v
1. REASONING STARVATION   2. CONTEXT BALLOONING   3. WALL-CLOCK TIMEOUT
+---------------------+   +---------------------+ +---------------------+
| Budget <= 256 toks  |   | 280 tok preambles   | | 15 min default/task |
| 511 delimiter loops |   | Displaces issue     | | 48 tasks = 12 hours |
| Context overflow!   |   | context (>25%)      | | SIGKILL: Score null |
+---------------------+   +---------------------+ +---------------------+
                                |
                                v
+---------------------------------------------------------------+
|           BOUNDED-RATIONALITY STABILIZATION APPLIED           |
|  - include_thoughts: false (Stripped inter-turn deliberation) |
|  - Action-only operational grammar (112 tok/turn consumption)  |
|  - 5-minute / 28-tool call hard cap (10h max / 120 tasks)     |
|  - Turn-1 regression test diff inspection                     |
+---------------------------------------------------------------+
```

---

## 📁 Repository Structure

```text
├── agent/                         # Core agent implementation
│   ├── agent.yaml                 # Agent manifest & harness configuration
│   ├── eval_config.yaml           # Two-tier execution envelope (5m / 28 calls)
│   ├── configs/
│   │   └── sampling.yaml          # Sampling parameters & thought stripping
│   └── prompts/
│       └── system.md              # Action-only operational grammar & rules
├── paper/                         # Academic research paper & writeups
│   ├── gemma4_swe_agent_research_paper.md   # Complete peer-reviewed paper
│   └── gemma4_swe_agent_kaggle_writeup.md   # Clean Kaggle web writeup
├── scripts/                       # Verification, packaging, and auditing tools
│   ├── build_paper_notebook.py    # Builds Kaggle public paper notebook
│   ├── package_final_submission.py# Deterministic hash-pinned packager
│   └── verify_final_handoff.py    # Comprehensive pre-flight audit suite
├── starter/                       # Official competition starter & task manifests
│   └── official/tasks.jsonl       # Official 129 SWE-bench benchmark tasks
├── dist/                          # Canonical distribution packages
│   └── submission.zip             # Verified candidate package (SHA-256: 82a9478d...)
└── README.md
```

---

## 🛠️ Verification & Reproduction

Verify the complete candidate package locally:

```powershell
# 1. Run full verification suite
python scripts/verify_final_handoff.py

# 2. Verify deterministic ZIP packaging & SHA-256 digest
python scripts/package_final_submission.py

# 3. Compile check all modules
python -m compileall -q scripts agent
```

---

## 👥 Authors

* **Ronak Jain** — Independent Researcher ([Kaggle Profile: ronak1167](https://www.kaggle.com/ronak1167))

---

## 📜 Citation

```bibtex
@article{jain2026bounded,
  title={Bounded Rationality in Autonomous Coding Agents: Empirical Failure Taxonomy and Architectural Stabilization of Quantized Gemma 4 12B on SWE-bench},
  author={Jain, Ronak},
  journal={Google - The Gemma 4 Developer Agent Paper Track (Kaggle)},
  year={2026},
  url={https://www.kaggle.com/code/ronak1167/gemma-4-swe-agent-research-paper}
}
```
