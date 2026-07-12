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
                title="Avoid SELECT * in governance-sensitive queries",
                evidence="The projection uses SELECT *.",
                impact="Wide projection increases scan, network transfer, and downstream memory pressure.",
                recommendation="Select only required columns and keep large text/blob columns out of routine analysis queries.",
            )
        )

    if parsed.function_wrapped_columns:
        columns = ", ".join(parsed.function_wrapped_columns)
        findings.append(
            Finding(
                code="SQL002",
                priority="P1",
                title="Function-wrapped filter columns may disable partition pruning",
                evidence=f"WHERE contains function-wrapped column(s): {columns}.",
                impact="StarRocks may be unable to prune partitions when the partition column is wrapped by a function.",
                recommendation="Rewrite filters as range predicates, for example col >= '2026-07-01' and col < '2026-07-02'.",
            )
        )

    partition_findings = find_partition_pruning_risks(parsed, metadata)
    findings.extend(partition_findings)

    if parsed.join_count >= 2:
        findings.append(
            Finding(
                code="SQL004",
                priority="P2",
                title="Multiple joins need cardinality review",
                evidence=f"The query contains {parsed.join_count} JOIN clauses.",
                impact="Large joins can multiply intermediate rows and raise shuffle or memory cost.",
                recommendation="Confirm join keys are selective, pre-aggregate large fact tables, and avoid joining unused dimensions.",
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
                title="Missing WHERE clause",
                evidence="No WHERE clause was found.",
                impact="The query may scan full tables.",
                recommendation="Add a bounded time or partition filter before running the query in production.",
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
                    title=f"Missing partition filter for {table}",
                    evidence=f"Known partition columns are {', '.join(table_meta.partition_columns)}, but none appear in WHERE.",
                    impact="The query may scan unnecessary partitions.",
                    recommendation="Add an explicit bounded predicate on the partition column.",
                )
            )

    return findings
