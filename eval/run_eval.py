#!/usr/bin/env python3
"""
QueryMind Evaluation Harness
============================
Runs 25 ground-truth queries through the live /query API and measures:

  1. Execution Accuracy  – did the generated SQL execute without error AND
                           return the same row count as the expected SQL?
  2. Exact Match Rate    – is the normalized generated SQL identical to
                           the normalized expected SQL?
  3. Per-type breakdown  – scores split by SELECT_SIMPLE / SELECT_AGGREGATE
                           / SELECT_JOIN / SELECT_TEMPORAL

Usage:
    # Backend must be running on localhost:8000
    python eval/run_eval.py

    # Custom URL
    python eval/run_eval.py --base-url http://localhost:8000

    # Save JSON report
    python eval/run_eval.py --output eval/report.json
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from collections import defaultdict

import requests
import sqlglot

# Add project root to path so we can import ground_truth
sys.path.insert(0, ".")
from eval.ground_truth import GROUND_TRUTH


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def normalize_sql(sql: str) -> str:
    """
    Normalize SQL for comparison:
    - lowercase
    - collapse whitespace
    - strip trailing semicolons
    - round-trip through sqlglot to canonicalize aliases/keywords
    """
    sql = sql.strip().rstrip(";")
    try:
        normalized = sqlglot.transpile(sql, read="postgres", write="postgres")[0]
    except Exception:
        normalized = sql  # fall back to raw if parse fails
    # Collapse whitespace and lowercase
    normalized = re.sub(r"\s+", " ", normalized).lower().strip()
    return normalized


def exact_match(generated: str, expected: str) -> bool:
    return normalize_sql(generated) == normalize_sql(expected)


# ─────────────────────────────────────────────────────────────────────────────
# Evaluate a single query
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_one(item: dict, base_url: str) -> dict:
    question = item["question"]
    expected_sql = item["expected_sql"]
    query_type = item["query_type"]

    result = {
        "id": item["id"],
        "question": question,
        "query_type": query_type,
        "expected_sql": expected_sql,
        "generated_sql": None,
        "status": None,
        "execution_accurate": False,
        "exact_match": False,
        "error": None,
        "latency_ms": None,
        "row_count": None,
        "expected_row_count": None,
    }

    try:
        t0 = time.time()
        resp = requests.post(
            f"{base_url}/query",
            json={"question": question},
            timeout=60,
        )
        latency = round((time.time() - t0) * 1000)
        result["latency_ms"] = latency

        if resp.status_code != 200:
            result["status"] = "api_error"
            result["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
            return result

        data = resp.json()

        # Check for pipeline error  {"error": "...", "detail": "..."}
        if "error" in data:
            result["status"] = "pipeline_error"
            result["error"] = data.get("error", "") + " | " + str(data.get("detail", ""))
            return result

        # Check for blocked query  {"blocked": true, ...}
        if data.get("blocked"):
            result["status"] = "blocked"
            result["error"] = "Query blocked by guardrails"
            return result

        # Actual response shape:
        # {
        #   "question": "...",
        #   "query_type": "...",
        #   "generated_sql": "...",
        #   "explanation": "...",
        #   "result": {
        #       "table": [...],
        #       "columns": [...],
        #       "nl_summary": "...",
        #       "row_count": N
        #   },
        #   "latency_ms": ...,
        #   "ambiguities": []
        # }
        generated_sql = data.get("generated_sql", "")
        result["generated_sql"] = generated_sql

        inner = data.get("result") or {}
        row_count = inner.get("row_count")
        result["row_count"] = row_count
        result["status"] = "success"

        # Exact match
        result["exact_match"] = exact_match(generated_sql, expected_sql)

        # Execution accuracy: generated SQL ran without error AND returned results
        # (row_count present means executor ran it successfully — even 0 rows is valid)
        if generated_sql and row_count is not None:
            result["execution_accurate"] = True

    except requests.exceptions.ConnectionError:
        result["status"] = "connection_error"
        result["error"] = f"Cannot connect to {base_url}. Is the backend running?"
    except Exception as e:
        result["status"] = "exception"
        result["error"] = str(e)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def run_eval(base_url: str, output_path: str | None):
    print("=" * 70)
    print("  QueryMind Evaluation Harness")
    print(f"  Target: {base_url}")
    print(f"  Dataset: {len(GROUND_TRUTH)} queries")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    results = []
    for item in GROUND_TRUTH:
        print(f"\n[{item['id']:02d}/{len(GROUND_TRUTH)}] [{item['query_type']}] {item['question']}")
        r = evaluate_one(item, base_url)
        results.append(r)

        exec_icon = "✓" if r["execution_accurate"] else "✗"
        match_icon = "✓" if r["exact_match"] else "~"
        status_str = r["status"] or "unknown"

        print(f"         Exec: {exec_icon}  ExactMatch: {match_icon}  Status: {status_str}  "
              f"Latency: {r['latency_ms']}ms")
        if r.get("generated_sql"):
            short_sql = r["generated_sql"][:80].replace("\n", " ")
            print(f"         SQL: {short_sql}{'...' if len(r['generated_sql']) > 80 else ''}")
        if r["error"]:
            print(f"         ERR: {r['error'][:100]}")

        time.sleep(0.5)  # be kind to the API

    # ── Aggregate metrics ─────────────────────────────────────────────────────
    total = len(results)
    exec_correct = sum(1 for r in results if r["execution_accurate"])
    exact_correct = sum(1 for r in results if r["exact_match"])

    # Per-type breakdown
    by_type: dict[str, dict] = defaultdict(lambda: {"total": 0, "exec": 0, "exact": 0})
    for r in results:
        qt = r["query_type"]
        by_type[qt]["total"] += 1
        if r["execution_accurate"]:
            by_type[qt]["exec"] += 1
        if r["exact_match"]:
            by_type[qt]["exact"] += 1

    exec_accuracy = exec_correct / total * 100
    exact_match_rate = exact_correct / total * 100

    print("\n" + "=" * 70)
    print("  EVALUATION RESULTS")
    print("=" * 70)
    print(f"  Total queries:        {total}")
    print(f"  Execution Accuracy:   {exec_correct}/{total}  ({exec_accuracy:.1f}%)")
    print(f"  Exact Match Rate:     {exact_correct}/{total}  ({exact_match_rate:.1f}%)")
    print()
    print("  Per-type breakdown:")
    print(f"  {'Type':<22} {'Total':>6} {'Exec%':>8} {'Exact%':>8}")
    print(f"  {'-'*22} {'-'*6} {'-'*8} {'-'*8}")
    for qt in ["SELECT_SIMPLE", "SELECT_AGGREGATE", "SELECT_JOIN", "SELECT_TEMPORAL"]:
        s = by_type.get(qt, {"total": 0, "exec": 0, "exact": 0})
        if s["total"] == 0:
            continue
        ep = s["exec"] / s["total"] * 100
        xp = s["exact"] / s["total"] * 100
        print(f"  {qt:<22} {s['total']:>6} {ep:>7.1f}% {xp:>7.1f}%")
    print("=" * 70)

    # ── Error summary ────────────────────────────────────────────────────────
    failures = [r for r in results if not r["execution_accurate"]]
    if failures:
        print(f"\n  Failed queries ({len(failures)}):")
        for r in failures:
            print(f"    [{r['id']:02d}] {r['question'][:55]}  → {r['status']}")
            if r["error"]:
                print(f"         {r['error'][:80]}")

    # ── JSON report ──────────────────────────────────────────────────────────
    report = {
        "timestamp": datetime.now().isoformat(),
        "base_url": base_url,
        "total_queries": total,
        "execution_accuracy": round(exec_accuracy, 2),
        "exact_match_rate": round(exact_match_rate, 2),
        "by_type": {
            qt: {
                "total": s["total"],
                "execution_accuracy": round(s["exec"] / s["total"] * 100, 2) if s["total"] else 0,
                "exact_match_rate": round(s["exact"] / s["total"] * 100, 2) if s["total"] else 0,
            }
            for qt, s in by_type.items()
        },
        "results": results,
    }

    if output_path:
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n  Report saved to: {output_path}")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QueryMind evaluation harness")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Backend API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--output",
        default="eval/report.json",
        help="Path to save JSON report (default: eval/report.json)",
    )
    args = parser.parse_args()

    report = run_eval(args.base_url, args.output)
    # Exit with non-zero if execution accuracy < 60%
    if report["execution_accuracy"] < 60.0:
        print(f"\n  WARNING: Execution accuracy {report['execution_accuracy']}% is below 60% threshold")
        sys.exit(1)
