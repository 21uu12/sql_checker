from __future__ import annotations

from dataclasses import dataclass

from tools.metadata import TableMetadata
from tools.sql_parser import ParsedSql, parse_sql


@dataclass(frozen=True)
class Finding:
    code: str
    priority: str
    title: str
    evidence: str
    impact: str
    recommendation: str


@dataclass(frozen=True)
class AnalysisResult:
    parsed: ParsedSql
    owners: tuple[str, ...]
    findings: tuple[Finding, ...]


def analyze_sql(sql: str, metadata: dict[str, TableMetadata]) -> AnalysisResult:
    parsed = parse_sql(sql)
    findings: list[Finding] = []

    if parsed.has_select_star:
        findings.append(
            Finding(
                code="SQL001",
                priority="P2",
                title="治理敏感查询中应避免使用 SELECT *",
                evidence="投影中使用了 SELECT *。",
                impact="宽投影会增加扫描量、网络传输量和下游内存压力。",
                recommendation="只选择所需列，并在常规分析查询中排除大文本或 Blob 列。",
            )
        )

    if parsed.function_wrapped_columns:
        columns = ", ".join(parsed.function_wrapped_columns)
        findings.append(
            Finding(
                code="SQL002",
                priority="P1",
                title="函数包装过滤列可能导致分区裁剪失效",
                evidence=f"WHERE 中存在被函数包装的列：{columns}。",
                impact="分区列被函数包装时，StarRocks 可能无法裁剪分区。",
                recommendation="将过滤条件改写为范围条件，例如 col >= '2026-07-01' 且 col < '2026-07-02'。",
            )
        )

    partition_findings = find_partition_pruning_risks(parsed, metadata)
    findings.extend(partition_findings)

    if parsed.join_count >= 2:
        findings.append(
            Finding(
                code="SQL004",
                priority="P2",
                title="多个 JOIN 需要进行基数审查",
                evidence=f"该查询包含 {parsed.join_count} 个 JOIN 子句。",
                impact="大型 JOIN 可能放大中间结果行数，并提高 Shuffle 或内存成本。",
                recommendation="确认关联键具有选择性，预聚合大型事实表，并避免关联未使用的维表。",
            )
        )

    owners = tuple(sorted({metadata[t].owner for t in parsed.tables if t in metadata and metadata[t].owner != "unknown"}))
    return AnalysisResult(parsed=parsed, owners=owners, findings=tuple(findings))


def find_partition_pruning_risks(parsed: ParsedSql, metadata: dict[str, TableMetadata]) -> list[Finding]:
    findings: list[Finding] = []
    where_lower = parsed.where_clause.lower()
    if not where_lower:
        return [
            Finding(
                code="SQL003",
                priority="P1",
                title="缺少 WHERE 条件",
                evidence="未找到 WHERE 子句。",
                impact="该查询可能扫描整张表。",
                recommendation="在生产环境运行前添加有边界的时间或分区过滤条件。",
            )
        ]

    for table in parsed.tables:
        table_meta = metadata.get(table)
        if not table_meta or not table_meta.partition_columns:
            continue

        has_partition_filter = any(column in where_lower for column in table_meta.partition_columns)
        if not has_partition_filter:
            findings.append(
                Finding(
                    code="SQL003",
                    priority="P1",
                title=f"表 {table} 缺少分区过滤条件",
                evidence=f"已知分区列为 {', '.join(table_meta.partition_columns)}，但 WHERE 中未出现这些列。",
                impact="该查询可能扫描不必要的分区。",
                recommendation="在分区列上添加明确且有边界的过滤条件。",
                )
            )

    return findings
