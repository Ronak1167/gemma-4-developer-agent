# Bounded Rationality in Autonomous Coding Agents: Empirical Failure Taxonomy and Architectural Stabilization of Quantized Gemma 4 12B on SWE-bench

**Author:** Ronak Jain  
**Affiliation:** Independent Researcher  
**Track:** Google - The Gemma 4 Developer Agent Paper Track  
**Competition Hub:** [Google - The Gemma 4 Developer Agent Paper Track](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper)  
**Public Kaggle Notebook:** [ronak1167/gemma-4-swe-agent-research-paper](https://www.kaggle.com/code/ronak1167/gemma-4-swe-agent-research-paper)  
**Verified Candidate Package:** SHA-256 `82a9478da291d5899e472b5b405156167b785e50c91ced9dadb8cf58a83d64f3`  

---

## Abstract

Deploying open-weight autonomous software engineering (SWE) agents on commodity accelerator clusters (specifically, 4 x NVIDIA L4 GPUs with INT4-quantized weights) faces three acute bottlenecks: finite context limits, degeneration patterns observed under INT4 quantization, and evaluation timeout boundaries. We present an empirical failure analysis and architectural stabilization framework for **Gemma 4 12B** (`gemma-4-12b-it-qat-w4a16-ct`) on the official 129-task SWE-bench benchmark. Through trajectory auditing of diagnostic runs, we formalize a three-part failure taxonomy: *(i)* **Reasoning Token Starvation**, where under-budgeted thinking channels trigger degenerate repetition loops (specifically, 511 repeating delimiter pairs spanning 14,308 characters at trajectory index 12 / ATIF step 13, causing a terminal $30,721 + 2,048 = 32,769 > 32,768$ context overflow); *(ii)* **Conversational Context Ballooning**, where discursive preambles consume $>25\%$ of context capacity; and *(iii)* **Evaluation Wall-Clock Exhaustion**, where uncalibrated 15-minute diagnostic limits allow 48 stalled tasks to exhaust the 12-hour global limit ($48 \times 15\text{m} = 720\text{m}$), causing kernel timeout (`publicScore: null`). To resolve these failure modes, we introduce a bounded-rationality architecture featuring: *(1)* calibrated 1,024-token thinking budgeting with inter-turn thought stripping (`include_thoughts: false`); *(2)* strict action-only turn invariants; *(3)* a two-tier execution envelope (12-call target, 28-call / 5-minute cap) bounding 120-task runtime to 10 hours; and *(4)* Turn-1 regression test diff inspection. Our framework enables timeout-free evaluation, achieving an official Kaggle public score of 0.03.

---

## 1. Introduction

Autonomous software engineering agents interactively resolve defects: exploring repository codebases, reproducing failures via regression tests, and synthesizing minimal patches (Jimenez et al., 2024). While closed frontier models leverage 100k+ token windows, deploying open-weight models under competitive constraints imposes four strict boundaries: (1) **Offline Execution:** Zero internet access with local wheelhouse dependencies; (2) **Constrained Inference:** NVIDIA L4 GPUs running quantized Gemma 4 (`gemma-4-12b-it-qat-w4a16-ct`, ~1.8 GB VRAM/GPU); (3) **Finite Context Window:** A hard 32,768-token (32k) serving ceiling; and (4) **Global Wall-Clock Ceiling:** A strict 12-hour (720m) limit covering setup and evaluation across up to 120 hidden tasks.

Uncalibrated baselines fail catastrophically under these bounds (e.g., submission `58080103` timed out with `publicScore: null`). Our central thesis is that **open-weight SWE agents require bounded rationality** (Simon, 1955): token expenditure, reasoning channels, and execution envelopes must be mathematically bounded to maintain multi-turn stability.

### Key Contributions
* **Empirical Failure Taxonomy:** Formally characterizing three distinct failure modes in quantized reasoning agents on SWE-bench: reasoning starvation loops, conversational ballooning, and wall-clock exhaustion.
* **Root-Cause Trajectory Autopsies:** Step-by-step trace audits identifying exact token overflow arithmetic and channel-repetition collapse.
* **Bounded-Rationality Architectural Framework:** Stabilization system decoupling per-turn reasoning from conversational memory, enforcing action-only operational grammars, and aligning event compaction with harness constraints.
* **Packaging Integrity & Reproducibility:** Documenting cross-platform zlib hash divergence between Linux and Windows, and verifying cryptographic parity across all candidate artifacts.

---

## 2. Related Work

### 2.1 Autonomous Coding Agents & SWE-bench
SWE-bench (Jimenez et al., 2024) shifted code evaluation from isolated function synthesis (Chen et al., 2021) to real-world repository maintenance. Early frameworks like SWE-agent (Yang et al., 2024), Aider (Gauthier, 2024), and OpenHands (Wang et al., 2024) engineered agent interfaces for large frontier models with 128k+ contexts, degrading sharply when applied to 32k open-weight models without strict context governors.

### 2.2 Test-Time Reasoning Compute
Chain-of-thought prompting (Wei et al., 2022; Wang et al., 2023) and ReAct-style reasoning channels (`<|channel>thought`; Yao et al., 2023) improve deduction but introduce novel failure modes. How test-time reasoning interacts with multi-turn tool trajectories under finite context limits remains underexplored; unstripped thoughts rapidly saturate memory over extended turns.

### 2.3 Quantized Model Deployment
Deploying 12B models within constrained accelerator memory footprints relies on INT4 Quantization-Aware Training (QAT; Jacob et al., 2018; Dettmers et al., 2023). While preserving standard benchmark perplexity, 4-bit quantization alters multi-turn instruction adherence, which we hypothesize increases vulnerability to degenerate repetition cycles under severe token starvation.

---

## 3. Problem Formulation and System Profile

### 3.1 Task Formulation
A defect resolution task is formulated as T = (R, I, S_repo, P*), where R is the repository, I is the issue description, S_repo is the base commit, and P* is the gold reference patch (strictly held out for the benchmark evaluation oracle and inaccessible to the agent). The agent interacts over discrete turns: at turn t, given interaction history, it invokes one of nine harness tools: `read_file`, `edit_file`, `write_file`, `run_command`, `get_status`, `submit_patch`, `get_code_neighbors`, `search_similar_code`, or `get_code_subgraph`. Evaluation is strictly binary: does the patch apply cleanly and pass the test suite without regressions?

We formalize defect resolution under bounded rationality as a constrained policy optimization problem:
* Maximize: Expected passed tasks across the benchmark evaluation suite.
* Subject to:
  1. Per-task time: t_i <= 300 seconds (5-minute session limit)
  2. Per-task tool budget: n_i <= 28 tool invocations
  3. Context window: L_prompt + L_output <= 32,768 tokens (serving context ceiling)
  4. Global evaluation cap: Total task runtime + setup time <= 720 minutes (12 hours)

### 3.2 Evaluation Environment
All experiments were conducted under the competition execution profile:
* **Accelerator:** 4 x NVIDIA L4 GPU cluster (24 GB GDDR6 per GPU, 96 GB aggregate VRAM).
* **Inference Engine & Model:** Agent Development Kit (ADK) and vLLM serving `gemma-4-12b-it-qat-w4a16-ct` (INT4 QAT). While `gemma-4-31b` is the starter default, 12B is one of four officially permitted competition models (`ALLOWED_MODEL_NAMES`), selected here for focused study of bounded-rationality failure modes.
* **Context Capacity:** 32,768 tokens (32k ceiling enforced by the competition vLLM/ADK serving profile; native architecture supports 256k).
* **Global Evaluation Cap:** 12 hours (720 minutes) across approximately 120 hidden evaluation tasks.

---

## 4. Empirical Failure Taxonomy of Quantized SWE Agents

Through fine-grained trajectory auditing of selected execution traces from competition diagnostic runs, alongside structural analysis of the 129-task public benchmark manifest, we identified three primary failure vectors:

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
| Budget <= 256 toks  |   | 280 tok preambles   | | 15 min diagnostic cap|
| 511 delimiter loops |   | Displaces issue     | | 48 tasks = 12 hours |
| Context overflow!   |   | context (>25%)      | | SIGKILL: Score null |
+---------------------+   +---------------------+ +---------------------+
```

### 4.1 Failure Mode 1: Reasoning Token Starvation and Degenerate Thought Loops
Gemma 4 12B generates internal chain-of-thought tokens within dedicated delimiter channels (`<|channel>thought ... <channel|>`). When configuring the reasoning budget:

1. **Under-provisioned Budget (<= 256 tokens):** Repository reasoning cannot finish within 256 tokens; hitting the cap mid-deliberation induces abrupt truncation.
2. **Degenerate Loop Collapse:** In `trace_fastapi_15589.json` at zero-based trajectory index 12 (corresponding to serialized ATIF step ID 13 within the 21-step trajectory), the starved model entered a self-reinforcing repetition loop. The model emitted **511 repeated delimiter pairs** (`<|channel>thought
<channel|>`) producing **14,308 characters** of empty channel syntax. When appended to prompt history, input tokens surged to:
   * Tokens in: 30,721
   * Tokens requested: 2,048
   * Total tokens: 32,769 (exceeding the 32,768 window ceiling)

This triggered a terminal `ContextWindowExceededError`, aborting the task without patch generation.

### 4.2 Failure Mode 2: Conversational Context Ballooning
Standard prompts encourage discursive commentary. We isolated and tokenized the natural language preambles preceding tool calls across a diagnostic sample of 42 baseline turns sampled from competition diagnostic failure traces (`trace_fastapi_15589.json`, `trace_rich_4077.json`) using the official Gemma 4 SentencePiece tokenizer (256k vocabulary). The complete dataset of 42 extracted turns, preambles, and token counts is reproducible via `scripts/inspect_all_tokens.py` and archived in `reports/tokenization_42_turns_dataset.json`. 

These isolated pre-action preambles averaged **280 tokens per turn** (standard deviation = 64). Over a 30-turn trajectory, conversational commentary alone consumes over 8,400 tokens (25.6% of context capacity), while ADK event compaction summaries bloat and displace initial issue descriptions.

### 4.3 Failure Mode 3: Global Evaluation Wall-Clock Exhaustion
Under unconstrained diagnostic budgets (where earlier candidate configurations explicitly set `max_time_minutes: 15.0`), stalled tasks exhaust 15 minutes each. If sandbox initialization and wheelhouse extraction consume s minutes, the maximum number of stalled tasks before triggering the global 12-hour timeout (720 minutes) is:
* Failure Ceiling: K = floor((720 - s) / 15) <= 48 tasks
* Diagnostic Stalled Tasks: 48 tasks x 15 minutes = 720 minutes

If 48 of 120 tasks loop or stall, the entire 12-hour budget is consumed, triggering container termination and a null leaderboard score (`publicScore: null`), as observed in submission `58080103`. Bounding task runtime to 5 minutes directly eliminates this vulnerability.

---

## 5. Architectural Design and Remediation Methodology

To resolve these failure modes, we designed a four-layer bounded-rationality architecture:

### 5.1 Calibrated Thought Budgeting with Inter-Turn Stripping
We configured `thinking_budget: 1024` tokens in `configs/sampling.yaml`, providing sufficient depth for complex deduction while preventing mid-thought truncation:

```yaml
# configs/sampling.yaml
temperature: 0.2
top_p: 0.95
max_output_tokens: 4096
thinking_config:
  thinking_budget: 1024
  include_thoughts: false
```

Crucially, **`include_thoughts: false`** strips `<|channel>thought` tokens from conversation history before appending the assistant's turn. Deliberations do not consume memory across turns, capping context growth strictly to actions and observations.

### 5.2 Action-Only Turn Invariants
We re-engineered `prompts/system.md` into an operational grammar enforcing the **Action-Only Invariant**:
> *"The assistant must emit ONLY tool invocations or submit_patch(). Natural language preambles, discursive commentary, and apologies are strictly forbidden."*

Tokenizing the 42 audited turns revealed that total assistant turns (combining 280-token discursive preambles with tool syntax) averaged 480 tokens (std dev = 82). Enforcing action-only invariants to strip natural language commentary dropped mean assistant turn consumption from **480 to 112 tokens** (std dev = 24), preserving crucial headroom for source diffs and test logs.

### 5.3 Two-Tier Execution Envelope
We calibrated execution across two synchronized tiers:
1. **Prompt Target (`prompts/system.md`):** Directs the agent to spend at most 12 counted tool calls, targeting patch edits by calls 4 to 6.
2. **Harness Boundary (`eval_config.yaml`):** Caps execution at 28 tool calls, 300 seconds (5 minutes), and 200 turns:

```yaml
# agent/eval_config.yaml
evaluation:
  timeout_seconds: 300
  max_tool_calls: 28
  max_time_minutes: 5
  max_turns: 200
```

Bounding task execution time to at most 5.0 minutes establishes a formal upper bound on total agent evaluation time:
* 120 tasks x 5.0 minutes = 600 minutes = 10.0 hours
This preserves **at least two hours of safety margin** within the 12-hour ceiling for container setup, wheelhouse extraction, and notebook teardown.

### 5.4 Turn-1 Regression Test Inspection
To maximize efficiency within the 12-call target, `system.md` enforces a mandatory initial action:
> *"Call 1 MUST be: `run_command("git diff -U3 -- tests/")`."*

Inspecting the pre-injected regression test reveals the expected symbol and failure condition immediately without blind exploration.

### 5.5 Bounded Execution Pipeline

The operational loop proceeds systematically: (1) initialize with action-only prompt and problem issue; (2) enforce envelope bounds ($t < 300\text{s}$, tool calls $\le 28$); (3) trigger compaction at 14,336 tokens (interval 15) while retaining the Turn-1 test diff; (4) generate deduction within the 1,024-token reasoning budget; (5) strip thought delimiters between turns (`include_thoughts: false`); (6) validate minimal git diff upon `submit_patch()`; otherwise execute tool and recurse until resolved.

---

## 6. Empirical Evaluation and Benchmark Analysis

### 6.1 Benchmark Sharding Architecture
The official public benchmark manifest (`starter/official/tasks.jsonl`) contains 129 tasks across four repositories: FastAPI (67 tasks, 51.9%), Rich (48 tasks, 37.2%), Requests (13 tasks, 10.1%), and HTTPX (1 task, 0.8%). We engineered an automated pipeline partitioning the 129 tasks across four balanced shards for modular validation:

| Shard | Tasks | Primary Repository | Target Budget | Shard Status |
| :---: | :---: | :--- | :---: | :---: |
| **0** | 32 | `fastapi/fastapi` | 160 min | Validated |
| **1** | 33 | `fastapi`, `requests` | 165 min | Validated |
| **2** | 32 | `Textualize/rich` | 160 min | Validated |
| **3** | 32 | `rich`, `httpx` | 160 min | Validated |
| **Total** | **129** | **Full Manifest** | **645 min** | **Partitioned** |

### 6.2 Verified Baseline Performance: `rich_4077`
In baseline evaluation (Version 18 smoke test), the agent resolved task `rich_4077`, requiring `FileProxy.isatty()` to delegate to the underlying stream:

The baseline execution achieved a verified pass:
* **Status:** `resolved = true`, Pytest exit code 0 (4 passed in 0.05 seconds).
* **Patch Size:** 324 bytes (exact byte match to reference patch).
* **Resource Expenditure:** 39 tool calls, 578.04 seconds (9.63 minutes).

```diff
--- a/rich/file_proxy.py
+++ b/rich/file_proxy.py
@@ -37,3 +37,5 @@ class FileProxy:
     def flush(self) -> None:
         self.__file.flush()
+
+    def isatty(self) -> bool:
+        return self.__file.isatty()
```

While verified, this baseline demonstrates unconstrained latency: 39 tool calls and 9.6 minutes were spent exploring extraneous directories before locating the defect.

### 6.3 Diagnostic Failure Analysis: Candidate v22 Trajectory Audit
In diagnostic runs (Candidate v22 across 3 tasks), uncalibrated settings triggered multi-task failures:
* **`fastapi_15589`:** Triggered Failure Mode 1 (511 repeating empty delimiter pairs at index 12 / step ID 13), crashing with `ContextWindowExceededError` at 32,769 tokens.
* **`rich_4077`:** Exceeded the 32k window during test ingestion due to conversational ballooning.
* **`rich_3944`:** Exhausted the 15-minute session limit without emitting a patch.

This confirms that unstripped reasoning history and discursive preambles cause systematic multi-task failure. Stabilizing these boundaries in Candidate v23 enabled full evaluation across the benchmark without timeouts, achieving an official Kaggle public score of 0.03.

### 6.4 Context Token Growth Dynamics
We modeled token accumulation across trajectory horizon:
Under action-only invariants with thought stripping, assistant turns add an empirical average of approximately 112 tokens per turn. Given a typical baseline prompt of roughly 3,500 tokens and conservative diff additions, the theoretical upper bound at turn 28 is modeled at under 16,500 tokens - preserving comfortable headroom below the 32,768 ceiling.

---

## 7. Determinism, Integrity, and Cross-Platform Packaging

We audited packaging integrity and identified cross-platform zlib divergence: archives uploaded to Kaggle Datasets unpack automatically, and re-zipping yields `bd22384a9f...` on Linux Python 3.12 versus `82a9478da2...` on Windows Python 3.14. Both local archives - `dist/submission.zip` and `dist/submission-final.zip` - are byte-for-byte identical (3,704 bytes each; SHA-256 `82a9478da291d5899e472b5b405156167b785e50c91ced9dadb8cf58a83d64f3`).

Crucially, all archives extract to identical 7,088 uncompressed bytes with matching source digests:
* `agent.yaml`: `2949364aec51a49ab9288a1f7c18cfca7d65e275bd31d26d98d4f0331e8f6c6b`
* `eval_config.yaml`: `d5f2db6ccb0a135e85c7453c7d2b016689db926046baad16cfcdc4461ab30144`
* `configs/sampling.yaml`: `e32c2e3c58d012c557d6497a62d0fe3bc27bd7adab67f8a4ad3f4122ea48f0a4`
* `prompts/system.md`: `4f10d6bd13c362c9377fafe1e0af54afec604527bdf73d879f7da886ada48dc3`

Our packaging script independently validates individual source hashes, guaranteeing zero configuration drift.

---

## 8. Discussion, Threats to Validity, and Generalizability

### 8.1 Thinking Budget vs. History Pollution
Increasing reasoning budgets does not monotonically improve agent outcomes. While reasoning tokens benefit deduction, unstripped reasoning history severely pollutes conversational context. Quantized 12B models suffer heightened attention drift when history retains outdated scratchpad tokens. Decoupling per-turn reasoning (`thinking_budget: 1024`) from conversational memory via inter-turn stripping (`include_thoughts: false`) resolves this dilemma.

### 8.2 Threats to Validity
* **Internal:** Container initialization and CUDA latency introduce runtime jitter. Harness timing hooks isolate model latency from provisioning.
* **External:** The benchmark evaluates Python repositories. Compiled languages requiring build steps (e.g., Rust or C++) may require expanded tool budgets (~36 calls).
* **Construct:** Resolution is measured against unit tests, which may not catch non-functional performance regressions.

### 8.3 Cross-Model Generalizability
While our empirical observations are grounded in Gemma 4 12B, we hypothesize that the bounded-rationality principles may generalize to other open-weight model families:
1. **Llama-3 & Qwen-2.5:** These models expose structured tool-calling syntax that we hypothesize will benefit from action-only grammars by preventing multi-turn conversational drift.
2. **DeepSeek-R1 Distillations:** Distilled reasoning models exhibit acute context-bloat vulnerabilities when thinking traces persist across turns. We hypothesize that inter-turn thought stripping is equally critical for sustaining multi-turn stability in these architectures.

---

## 9. Conclusion and Broader Impact

Building autonomous developer agents with open-weight models under strict compute constraints requires disciplined systems engineering. We presented an empirical failure taxonomy of quantized Gemma 4 12B on SWE-bench and developed an architectural stabilization framework that: (1) suppresses degenerate repetition loops via calibrated 1,024-token thinking budgeting and thought stripping; (2) eliminates context bloat via action-only turn invariants; (3) formally bounds total runtime to 10 hours across 120 tasks under Kaggle's 12-hour ceiling; and (4) accelerates defect localization through Turn-1 regression test diff inspection. All source code, verification suites, and notebook pipelines are open-sourced, offering a reproducible foundation for robust autonomous coding agents on commodity accelerators.

---

## References

1. Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O., & Narasimhan, K. (2024). *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* ICLR.
2. Google DeepMind. (2024). *Gemma: Open Models Based on Gemini Research and Technology.* arXiv:2403.08295. Kaggle. (2026). *Google - The Gemma 4 Developer Agent Competition.* Overview: https://www.kaggle.com/competitions/gemma-4-developer-agent/overview; Kaggle Staff Model Announcement: https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287; Model weights: https://www.kaggle.com/models/google/gemma-4.
3. Yang, J., Jimenez, C. E., Wettig, A., Lieret, K., Yao, S., Narasimhan, K., & Press, O. (2024). *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering.* arXiv:2405.15793.
4. Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models.* ICLR.
5. Dettmers, T., Pagnoni, A., Holtzman, A., & Zettlemoyer, L. (2023). *QLoRA: Efficient Finetuning of Quantized LLMs.* NeurIPS; Jacob, B., et al. (2018). *Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference.* CVPR.
6. Wang, G., Chen, Z., Tang, H., Jiang, J., & Li, B. (2024). *OpenHands: An Open Platform for AI Software Developers.* arXiv:2407.16741.
7. Wei, J., Wang, X., Schuurmans, D., Bosma, M., Xia, F., Chi, E., Le, Q. V., & Zhou, D. (2022). *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models.* NeurIPS.
8. Wang, X., Wei, J., Schuurmans, D., Le, Q., Chi, E., Narang, S., Chowdhery, A., & Zhou, D. (2023). *Self-Consistency Improves Chain of Thought Reasoning in Language Models.* ICLR.
9. Gauthier, P. (2024). *Aider: AI Pair Programming in Your Terminal.* https://aider.chat.
10. Chen, M., Tworek, J., Jun, H., Yuan, Q., Pinto, H. P. d. O., Kaplan, J., et al. (2021). *Evaluating Large Language Models Trained on Code.* arXiv:2107.03374.
11. Simon, H. A. (1955). *A Behavioral Model of Rational Choice.* The Quarterly Journal of Economics, 69(1), 99-118.