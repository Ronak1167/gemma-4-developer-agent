# Independent Audit — v35

Date: 2026-11-20

## Summary

v35 was created as a separate candidate from v34. Previous candidate directories and archives were preserved. The changes address an actual prompt/evaluator contract defect and add a regression check to the build process.

## Findings and changes

1. **Critical budget contradiction fixed.** v34 configured `max_time_minutes=5` and a 300-second command timeout, while its system prompt told the model it had a fifteen-minute hard task budget. v35 now states five minutes / 300 seconds explicitly.
2. **Corrupted test-duration guidance fixed.** v34 prompt contained the malformed text `90?180 seconds`. v35 now recommends a focused test expected to finish within 60 to 120 seconds and tells the agent to account for remaining time before launching tests.
3. **Adaptive budget planning added.** v35 prompt sets early discovery/localization targets and reserves the final calls for patch completion, tests, diff review, status and submission. These are guidance, not rigid call quotas.
4. **Builder regression checks added.** The v35 builder rejects stale fifteen-minute or malformed timing guidance and requires the prompt's five-minute budget to match the evaluator configuration.

## Build results

- Candidate: v35
- Model: `gemma-4-31b-it-qat-w4a16-ct`
- Archive: `dist/submission-v35.zip`
- Size: 47,385 bytes
- SHA-256: `3aea564e179102e6d223ea97f953674088949ae1c7e4c6a89dc274cccff2797a`
- Archive members: 9, exact allowlist; ZIP CRC and byte-identity checks passed.
- Diagnostic notebook: `dist/kaggle_v35_diagnostic/kaggle_mini_benchmark.ipynb`
- Notebook: 11 cells; code cells parse; outputs cleared; execution counts null.
- Kaggle metadata: private, GPU enabled, internet disabled.
- GPU execution gate: closed.
- Leaderboard submission: not made.

## Independent validation performed

The separate `independent_audit.py` script passed after rebuilding the candidate:

- YAML parsing including `!include` tags.
- Root and analyzer model consistency.
- Five-minute evaluator/prompt/notebook budget consistency.
- Read-only analyzer tool allowlist.
- Exact archive member list, CRC, source byte identity and SHA-256.
- Notebook AST and clean-output checks.
- Diagnostic metadata privacy, GPU and offline settings.
- Four diagnostic task IDs checked against the official 129-task manifest, including repository and non-empty test-patch checks.
- Retrieval corpus contains 129 unique entries and no patch/test-patch bodies.
- Exact self-exclusion and response-size checks for all 129 retrieval queries.
- Build report archive hash and byte-size reconciliation.
- No leaderboard submission code or output was produced.

## Remaining blockers and limits

- **No real Gemma 31B GPU inference has been run for v35.**
- Kaggle API package is absent locally and no local Kaggle token file or Kaggle credential environment variable was found. No secrets were read or exposed.
- Laptop GPU is AMD Radeon 8050S, not the required Kaggle 4×L4 evaluation hardware.
- Static validation cannot prove issue-resolution quality, 0.30 score, first place, or absence of runtime errors.
- The previous 0.03 score belongs to the historical v23 submission, not v35.

## Release decision

v35 is the latest locally verified candidate, **not yet performance-qualified**. Next gate: upload the private candidate dataset and closed-gate diagnostic notebook, independently verify cloud readback and metadata, then deliberately authorize the GPU smoke test. Run the four-task diagnostic, inspect every trace/patch/test result, and iterate based on actual failures. Do not submit a leaderboard entry without explicit owner approval.

## Additional diagnostic reliability repair

A second review found that the original diagnostic notebook asserted that all four task results must exist before exporting artifacts. If the model server or evaluator failed partway through, that assertion could prevent partial traces and error details from being packaged.

The v35 diagnostic builder now:
- catches evaluator exceptions and writes a traceback artifact;
- does not abort solely because the aggregate result object is absent or incomplete;
- reads whatever summary/task-result records were produced;
- reports missing task IDs and malformed records explicitly;
- distinguishes requested-task resolution rate from resolution among recorded tasks;
- packages partial logs, patches, traces, and the diagnostic summary.

The diagnostic builder itself compiles, regenerates the notebook, and validates that these recovery paths remain present. The independent audit was rerun after this change and passed.

## Final local verification state

- Candidate archive SHA remains unchanged: `3aea564e179102e6d223ea97f953674088949ae1c7e4c6a89dc274cccff2797a`.
- Builder rerun: PASS.
- Diagnostic notebook rebuild: PASS.
- Independent audit after rebuild: PASS.
- Python compileall for v35 scripts and retrieval code: PASS.
- Retrieval self-exclusion: 129/129.
- No GPU execution or leaderboard submission.
