from __future__ import annotations

import argparse
from pathlib import Path

from tools.analyzer import analyze_sql
from tools.complexity import assess_complexity
from tools.llm_reviewer import create_agent_review
from tools.metadata import load_table_metadata
from tools.report import render_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze SQL and generate a governance report.")
    parser.add_argument("sql_file", type=Path, help="Path to the SQL file to review.")
    parser.add_argument("--metadata", type=Path, default=Path("metadata/tables.json"))
    parser.add_argument("--out", type=Path, default=Path("outputs/report.md"))
    parser.add_argument(
        "--review-mode",
        choices=("auto", "rules", "agent"),
        default="auto",
        help="Choose local rules, Agent review, or automatic routing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sql = args.sql_file.read_text(encoding="utf-8")
    metadata = load_table_metadata(args.metadata)
    result = analyze_sql(sql, metadata)
    complexity = assess_complexity(result.parsed, args.review_mode)
    agent_review = create_agent_review(sql, result.parsed, complexity) if complexity.route == "agent" else None
    report = render_report(result, complexity, agent_review)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(f"wrote {args.out} (route: {complexity.route}, score: {complexity.score})")


if __name__ == "__main__":
    main()
