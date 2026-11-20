---
name: public_issue_memory
description: Read-only lexical retrieval over the official public 129-task development corpus. Finds analogous issue descriptions and changed-file/symbol metadata without returning gold patch code.
---

# Public issue memory

Use this skill once for an issue in FastAPI, Rich, Requests, or HTTPX when it may help localization.

Run scripts/search.py once with:
- query: the full problem statement copied from the current task context;
- repo: the exact repository slug, such as fastapi/fastapi;
- exclude_instance: the current task instance ID when visible;
- top_k: 3.

The script automatically excludes an exact normalized full-statement match from the public corpus, even if no instance ID is supplied. Do not use a short keyword query when the current task could be in the public corpus. If you cannot pass the full statement and do not know the task ID, skip retrieval.

The index is derived from the local official public development-task manifest. It contains issue descriptions, repository names, changed file paths, diff hunk labels, and prior test file names. It does NOT contain gold patch bodies or hidden evaluation tasks.

Treat every result as a weak retrieval hint. Similar wording does not establish the same root cause. Verify the current repository source, base revision, API behavior, and existing tests before editing. Do not copy patches from memory or infer a fix from a task ID.

The script is offline, read-only, uses only Python's standard library, and returns a small JSON response. Do not call it repeatedly with minor query variations.
