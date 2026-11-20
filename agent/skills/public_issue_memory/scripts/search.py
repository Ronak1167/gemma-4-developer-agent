from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+")
STOP = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for",
    "is", "are", "be", "with", "when", "that", "this", "it", "as",
    "by", "from", "at", "not", "if", "should", "can", "will", "was",
    "were", "has", "have", "had", "into", "than", "then", "their",
    "there", "which", "what", "how", "does", "do", "also",
}


def tokenize(text: str) -> list[str]:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return [t.lower() for t in TOKEN_RE.findall(text) if t.lower() not in STOP and len(t) > 1]


def normalize_issue(text: str) -> str:
    return " ".join(text.casefold().split())


def exact_self_match(index: list[dict], query: str) -> str | None:
    normalized = normalize_issue(query)
    if len(normalized) < 20:
        return None
    for doc in index:
        if normalize_issue(doc.get("problem_statement", "")) == normalized:
            return doc.get("instance_id")
    return None


def document_text(doc: dict) -> str:
    return " ".join([
        doc.get("problem_statement", ""),
        doc.get("hints_text", ""),
        doc.get("repo", ""),
        " ".join(doc.get("changed_files", [])),
        " ".join(doc.get("changed_symbols", [])),
    ])


def search(index: list[dict], query: str, repo: str | None = None,
           exclude_instance: str | None = None, top_k: int = 3) -> list[dict]:
    q = Counter(tokenize(query))
    if not q:
        return []
    auto_exclude = exact_self_match(index, query)
    excluded = {x for x in (exclude_instance, auto_exclude) if x}
    docs = []
    df = Counter()
    for doc in index:
        if doc.get("instance_id") in excluded:
            continue
        tokens = tokenize(document_text(doc))
        tf = Counter(tokens)
        docs.append((doc, tokens, tf))
        df.update(set(tokens))
    n = len(docs)
    if not n:
        return []
    avgdl = sum(len(tokens) for _, tokens, _ in docs) / n or 1.0
    scored = []
    for doc, tokens, tf in docs:
        score = 0.0
        dl = len(tokens)
        for term, qf in q.items():
            freq = tf.get(term, 0)
            if not freq:
                continue
            idf = math.log(1.0 + (n - df[term] + 0.5) / (df[term] + 0.5))
            denom = freq + 1.5 * (1.0 - 0.75 + 0.75 * dl / avgdl)
            score += idf * (freq * 2.5 / denom) * (1.0 + math.log(qf))
        same_repo = bool(repo and doc.get("repo") == repo)
        if same_repo:
            score += 1.25
        if score > 0:
            scored.append((score, same_repo, doc))
    scored.sort(key=lambda item: (-item[0], -int(item[1]), item[2].get("instance_id", "")))
    results = []
    for score, same_repo, doc in scored[:max(1, min(top_k, 5))]:
        excerpt = " ".join(doc.get("problem_statement", "").split())[:360]
        results.append({
            "instance_id": doc.get("instance_id"),
            "repo": doc.get("repo"),
            "bm25_score": round(score, 4),
            "same_repo": same_repo,
            "problem_excerpt": excerpt,
            "changed_files": doc.get("changed_files", [])[:6],
            "changed_symbols": doc.get("changed_symbols", [])[:6],
            "prior_test_files": doc.get("test_files", [])[:3],
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--repo", default=None)
    parser.add_argument("--exclude-instance", "--exclude_instance", default=None)
    parser.add_argument("--top-k", "--top_k", type=int, default=3)
    args = parser.parse_args()
    index_path = Path(__file__).resolve().parents[1] / "assets" / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    auto_excluded = exact_self_match(index, args.query)
    results = search(index, args.query, args.repo, args.exclude_instance, args.top_k)
    payload = {
        "source": "official public development-task metadata; retrieval hints only",
        "query": args.query[:240],
        "repo_filter": args.repo,
        "auto_excluded_instance_id": auto_excluded,
        "results": results,
        "warning": "Analogies are not proof. Verify current source and tests; no gold patch code is included.",
    }
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    if len(encoded) > 3800:
        for item in payload["results"]:
            item["problem_excerpt"] = item["problem_excerpt"][:220]
            item["changed_files"] = item["changed_files"][:4]
            item["changed_symbols"] = item["changed_symbols"][:4]
            item["prior_test_files"] = item["prior_test_files"][:2]
        encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    if len(encoded) > 3800:
        payload["results"] = payload["results"][:2]
        encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    if len(encoded) > 3800:
        payload["results"] = payload["results"][:1]
        encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    if len(encoded) > 3800:
        payload["results"] = []
        encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    print(encoded)


if __name__ == "__main__":
    main()
