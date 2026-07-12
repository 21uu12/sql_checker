from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from tools.analyzer import analyze_sql
from tools.notification_payload import build_notification_payload, load_owner_targets
from tools.sql_review import SqlFileReview, review_sql_text
from tools.metadata import TableMetadata, load_table_metadata


@dataclass(frozen=True)
class ChangedSqlReview:
    status: str
    path: Path
    current: Optional[SqlFileReview]
    baseline: Optional[SqlFileReview]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="仅审查本次 Git 提交中变更的 SQL 文件。")
    parser.add_argument("--source", type=Path, default=Path("sql"))
    parser.add_argument("--metadata", type=Path, default=Path("metadata/tables.json"))
    parser.add_argument("--baseline-ref", default="HEAD^")
    parser.add_argument("--out", type=Path, default=Path("outputs/changed_sql_report.md"))
    parser.add_argument("--owner-metadata", type=Path, default=Path("metadata/owners.json"))
    parser.add_argument("--notification-out", type=Path)
    return parser.parse_args()


def changed_sql_files(source: Path, baseline_ref: str) -> list[tuple[str, Path]]:
    result = subprocess.run(
        ["git", "diff", "--name-status", baseline_ref, "HEAD", "--", source.as_posix()],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        initial = subprocess.run(
            ["git", "ls-files", "--", source.as_posix()],
            capture_output=True,
            text=True,
            check=False,
        )
        return [("A", Path(path)) for path in initial.stdout.splitlines() if path.endswith(".sql")]

    changes: list[tuple[str, Path]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") and len(parts) == 3:
            if parts[1].endswith(".sql"):
                changes.append(("D", Path(parts[1])))
            if parts[2].endswith(".sql"):
                changes.append(("A", Path(parts[2])))
        elif len(parts) == 2 and parts[1].endswith(".sql"):
            changes.append((status[0], Path(parts[1])))
    return changes


def read_git_file(reference: str, path: Path) -> Optional[str]:
    result = subprocess.run(
        ["git", "show", "{0}:{1}".format(reference, path.as_posix())],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def review_changes(source: Path, metadata: dict[str, TableMetadata], baseline_ref: str) -> list[ChangedSqlReview]:
    reviews: list[ChangedSqlReview] = []
    for status, repository_path in changed_sql_files(source, baseline_ref):
        relative_path = repository_path.relative_to(source)
        baseline_sql = read_git_file(baseline_ref, repository_path)
        baseline = review_sql_text(relative_path, baseline_sql, metadata) if baseline_sql is not None else None
        if status == "D":
            reviews.append(ChangedSqlReview("删除", relative_path, None, baseline))
            continue

        current_sql = repository_path.read_text(encoding="utf-8")
        current = review_sql_text(relative_path, current_sql, metadata)
        label = "新增" if status == "A" else "修改"
        reviews.append(ChangedSqlReview(label, relative_path, current, baseline))
    return reviews


def render_report(
    reviews: list[ChangedSqlReview], source: Path, baseline_ref: str, metadata: dict[str, TableMetadata]
) -> str:
    p1_change = sum(item.current.p1_count if item.current else 0 for item in reviews) - sum(item.baseline.p1_count if item.baseline else 0 for item in reviews)
    p2_change = sum(item.current.p2_count if item.current else 0 for item in reviews) - sum(item.baseline.p2_count if item.baseline else 0 for item in reviews)
    worsened = [item for item in reviews if item.current and item.baseline and item.current.score < item.baseline.score]
    lines = [
        "# SQL 增量治理报告",
        "",
        f"对比基线：`{baseline_ref}`",
        f"本次变更 SQL 文件：**{len(reviews)}**",
        f"新增 P1 发现项：**{p1_change:+d}**",
        f"新增 P2 发现项：**{p2_change:+d}**",
        f"评分变差的 SQL：**{len(worsened)}**",
        "",
        "## 变更结果",
        "",
        "| SQL 文件 | 变更类型 | 当前分数 | 上一版分数 | 分数变化 |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for item in reviews:
        current_score = str(item.current.score) if item.current else "不适用"
        baseline_score = str(item.baseline.score) if item.baseline else "不适用"
        score_change = "不适用"
        if item.current and item.baseline:
            score_change = "{0:+d}".format(item.current.score - item.baseline.score)
        lines.append(f"| `{item.path.as_posix()}` | {item.status} | {current_score} | {baseline_score} | {score_change} |")

    for item in reviews:
        if item.current is None:
            continue
        result = analyze_sql((source / item.path).read_text(encoding="utf-8"), metadata)
        lines.extend(["", f"## `{item.path.as_posix()}`", ""])
        if not result.findings:
            lines.extend(["本次变更未触发高风险规则。", ""])
            continue
        for finding in result.findings:
            lines.extend(
                [
                    f"### {finding.priority} {finding.code}：{finding.title}",
                    "",
                    f"- 证据：{finding.evidence}",
                    f"- 影响：{finding.impact}",
                    f"- 建议：{finding.recommendation}",
                    "",
                ]
            )
    if not reviews:
        lines.extend(["本次提交没有新增、修改或删除 `sql/` 下的 SQL 文件。", ""])
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    if not args.source.is_dir():
        raise SystemExit(f"SQL 来源目录不存在：{args.source}")
    metadata = load_table_metadata(args.metadata)
    reviews = review_changes(args.source, metadata, args.baseline_ref)
    report = render_report(reviews, args.source, args.baseline_ref, metadata)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    if args.notification_out:
        payload = build_notification_payload(
            reviews,
            args.source,
            metadata,
            load_owner_targets(args.owner_metadata),
            args.baseline_ref,
            report,
        )
        args.notification_out.parent.mkdir(parents=True, exist_ok=True)
        args.notification_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {args.out}（变更 SQL：{len(reviews)}）")


if __name__ == "__main__":
    main()
