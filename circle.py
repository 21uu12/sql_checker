from __future__ import annotations

import argparse
from pathlib import Path

from tools.circle import CircleReview, review_sql_directory
from tools.metadata import load_table_metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审查 Git 工作目录中的全部 SQL 文件。")
    parser.add_argument("source", type=Path, help="包含 SQL 文件的本地 Git 工作目录。")
    parser.add_argument("--metadata", type=Path, default=Path("metadata/tables.json"))
    parser.add_argument("--out", type=Path, default=Path("outputs/circle_report.md"))
    return parser.parse_args()


def render_circle_report(review: CircleReview) -> str:
    files = review.sql_files
    score = f"{review.score}/100" if review.score is not None else "不适用（未找到 SQL 文件）"
    p1_count = sum(item.p1_count for item in files)
    p2_count = sum(item.p2_count for item in files)
    agent_count = sum(item.route == "agent" for item in files)
    lines = [
        "# SQL 治理 Circle 报告",
        "",
        f"来源：`{review.source}`",
        f"已审查 SQL 文件：{len(files)}",
        f"Circle 评分：**{score}**",
        f"Circle 评价：**{review.evaluation}**",
        "",
        "## 规则汇总",
        "",
        f"- P1 发现项：{p1_count}",
        f"- P2 发现项：{p2_count}",
        f"- 需深度复核的复杂 SQL 文件：{agent_count}",
        "",
        "评分规则：每个 P1 发现项扣 25 分，每个 P2 发现项扣 10 分；Circle 评分为文件评分的平均值。",
        "",
        "## 文件结果",
        "",
        "| SQL 文件 | 分数 | 评价 | 发现项 | 路由 |",
        "| --- | ---: | --- | ---: | --- |",
    ]
    for item in files:
        findings = f"P1: {item.p1_count}, P2: {item.p2_count}"
        if item.error:
            findings = f"无法读取：{item.error}"
        lines.append(f"| `{item.path.as_posix()}` | {item.score} | {item.evaluation} | {findings} | {item.route} |")

    lines.extend(
        [
            "",
            "## Circle 评价",
            "",
            circle_evaluation_text(review, p1_count, agent_count),
            "",
            "## 下一步人工检查",
            "",
            "- 在合并或调度前复核包含 P1 问题的文件。",
            "- 将复杂 SQL 文件分配给数据工程师进行深度复核。",
            "- 在将分区发现项作为最终结论前，确认表元数据仍是最新的。",
            "",
        ]
    )
    return "\n".join(lines)


def circle_evaluation_text(review: CircleReview, p1_count: int, agent_count: int) -> str:
    if not review.sql_files:
        return "未找到 SQL 文件，当前 Circle 没有可审查范围。"
    if review.evaluation == "良好":
        return "在当前静态规则下，该 Circle 状态良好；复杂文件仍应单独复核。"
    if review.evaluation == "关注":
        return "该 Circle 存在可控的规则问题，应在大范围上线前处理列出的 P1/P2 发现项。"
    if review.evaluation == "需要复核":
        return f"该 Circle 需要复核：{p1_count} 个 P1 发现项和 {agent_count} 个复杂 SQL 文件需要关注。"
    return f"在当前规则下，该 Circle 为高风险：{p1_count} 个 P1 发现项需要在生产使用前进行人工复核。"


def main() -> None:
    args = parse_args()
    if not args.source.is_dir():
        raise SystemExit(f"来源目录不存在：{args.source}")

    metadata = load_table_metadata(args.metadata)
    review = review_sql_directory(args.source, metadata)
    report = render_circle_report(review)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    score = f"{review.score}/100" if review.score is not None else "未评分"
    print(f"已写入 {args.out}（{len(review.sql_files)} 个 SQL 文件，{score}，{review.evaluation}）")


if __name__ == "__main__":
    main()
