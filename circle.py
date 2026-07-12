from __future__ import annotations

import argparse
from pathlib import Path

from tools.circle import CircleReview, review_sql_directory
from tools.metadata import load_table_metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review all SQL files in a Git working directory.")
    parser.add_argument("source", type=Path, help="Local Git working directory containing SQL files.")
    parser.add_argument("--metadata", type=Path, default=Path("metadata/tables.json"))
    parser.add_argument("--out", type=Path, default=Path("outputs/circle_report.md"))
    return parser.parse_args()


def render_circle_report(review: CircleReview) -> str:
    files = review.sql_files
    p1_count = sum(item.p1_count for item in files)
    p2_count = sum(item.p2_count for item in files)
    agent_count = sum(item.route == "agent" for item in files)
    lines = [
        "# SQL Governance Circle Report",
        "",
        f"Source: `{review.source}`",
        f"SQL files reviewed: {len(files)}",
        f"Circle score: **{review.score}/100**",
        f"Circle evaluation: **{review.evaluation}**",
        "",
        "## Rule Summary",
        "",
        f"- P1 findings: {p1_count}",
        f"- P2 findings: {p2_count}",
        f"- Complex SQL files requiring deeper review: {agent_count}",
        "",
        "Score rule: each P1 finding deducts 25 points; each P2 finding deducts 10 points; the Circle score is the average file score.",
        "",
        "## File Results",
        "",
        "| SQL file | Score | Evaluation | Findings | Route |",
        "| --- | ---: | --- | ---: | --- |",
    ]
    for item in files:
        findings = f"P1: {item.p1_count}, P2: {item.p2_count}"
        if item.error:
            findings = f"Unreadable: {item.error}"
        lines.append(f"| `{item.path.as_posix()}` | {item.score} | {item.evaluation} | {findings} | {item.route} |")

    lines.extend(
        [
            "",
            "## Circle Evaluation",
            "",
            circle_evaluation_text(review, p1_count, agent_count),
            "",
            "## Next Human Check",
            "",
            "- Review P1 files before merging or scheduling them.",
            "- Assign complex SQL files to a data engineer for deeper review.",
            "- Confirm table metadata is current before treating partition findings as final.",
            "",
        ]
    )
    return "\n".join(lines)


def circle_evaluation_text(review: CircleReview, p1_count: int, agent_count: int) -> str:
    if not review.sql_files:
        return "No SQL files were found. The Circle has no reviewable scope."
    if review.evaluation == "Good":
        return "The Circle is in good shape under the current static rules. Continue reviewing complex files separately."
    if review.evaluation == "Watch":
        return "The Circle has manageable rule violations. Address the listed P1/P2 findings before broad rollout."
    if review.evaluation == "Needs Review":
        return f"The Circle needs review: {p1_count} P1 finding(s) and {agent_count} complex SQL file(s) require attention."
    return f"The Circle is high risk under the current rules: {p1_count} P1 finding(s) require human review before production use."


def main() -> None:
    args = parse_args()
    if not args.source.is_dir():
        raise SystemExit(f"source directory does not exist: {args.source}")

    metadata = load_table_metadata(args.metadata)
    review = review_sql_directory(args.source, metadata)
    report = render_circle_report(review)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(f"wrote {args.out} ({len(review.sql_files)} SQL files, {review.score}/100, {review.evaluation})")


if __name__ == "__main__":
    main()
