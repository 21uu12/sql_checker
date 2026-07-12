from __future__ import annotations

import argparse
from pathlib import Path

from tools.analyzer import analyze_sql
from tools.complexity import assess_complexity
from tools.llm_reviewer import create_agent_review
from tools.metadata import load_table_metadata
from tools.report import render_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="分析 SQL 并生成治理报告。")
    parser.add_argument("sql_file", type=Path, help="待审查 SQL 文件的路径。")
    parser.add_argument("--metadata", type=Path, default=Path("metadata/tables.json"))
    parser.add_argument("--out", type=Path, default=Path("outputs/report.md"))
    parser.add_argument(
        "--review-mode",
        choices=("auto", "rules", "agent"),
        default="auto",
        help="选择本地规则、Agent 复核或自动路由。",
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
    print(f"已写入 {args.out}（路由：{complexity.route}，分数：{complexity.score}）")


if __name__ == "__main__":
    main()
