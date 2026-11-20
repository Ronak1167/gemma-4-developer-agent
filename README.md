# Gemma 4 Developer Agent — Competition Workspace

This repository contains the agent configuration, offline retrieval experiments, Kaggle diagnostic notebooks, and reproducibility artifacts for the **Google – The Gemma 4 Developer Agent Competition**.

## Current candidate status (20 November 2026)

- **Current candidate:** v35, configured for `gemma-4-31b-it-qat-w4a16-ct`.
- **Archive:** `dist/submission-v35.zip`
- **SHA-256:** `3aea564e179102e6d223ea97f953674088949ae1c7e4c6a89dc274cccff2797a`
- **Runtime envelope:** 300-second command timeout; 5 minutes per task; 40 tool calls; 500 turns.
- **Generation:** 4,096 maximum output tokens; 1,024 thinking budget; thoughts excluded between turns.
- **Context compaction:** 14,336-token threshold; interval 15; overlap 2; retain 5 events.
- **Retrieval:** read-only BM25 hints over the 129-task public development corpus; exact task self-exclusion; no gold patch bodies packaged.
- **Diagnostic:** four public development tasks across FastAPI, Rich, Requests and HTTPX. Private Kaggle notebook; internet disabled; GPU enabled; execution gate closed by default.

**Important:** v35 has passed local structural, archive, notebook-AST, task-manifest, retrieval self-exclusion, and independent integrity checks. It has **not** yet been run on the Kaggle 4×L4 GPU environment. No v35 score, 0.30 result, first-place result, or error-free performance claim is made. A private GPU diagnostic is required before selecting a leaderboard candidate.

## Verified historical result

An earlier v23 submission recorded an official public score of **0.03** (submission ID `58187123`). That is a historical result, not the score of v34 or v35.

## Rebuild and audit

Run from the repository root in PowerShell:

```powershell
py -3.13 workbench-v35\scripts\build_candidate.py --force
py -3.13 workbench-v35\scripts\build_diagnostic.py
py -3.13 workbench-v35\scripts\independent_audit.py
```

The builder verifies the agent source, retrieval corpus, deterministic ZIP packaging, and source/archive byte identity. The independent audit rechecks the archive, notebook, runtime budget consistency, official task manifest, retrieval self-exclusion for all 129 tasks, and Kaggle diagnostic privacy/gating metadata.

## Candidate history

- v33: 15-minute extended diagnostic candidate.
- v34: 5-minute production-budget candidate.
- v35: v34 with prompt/evaluator budget consistency fixed and regression checks added.

Previous archives are retained for comparison. Do not overwrite historical candidates when building new versions.

## Safety and release gates

- The diagnostic notebook does not generate or upload a leaderboard submission.
- The GPU diagnostic gate is deliberately closed by default.
- Never run a leaderboard submission action without explicit owner approval.
- Do not infer benchmark performance from static validation or retrieval-localization metrics.
- The competition's full evaluation has a 12-hour patch-generation budget; per-task limits must be benchmarked against actual throughput and pass rate.
