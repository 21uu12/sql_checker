from __future__ import annotations

import re
from dataclasses import dataclass

try:
    import sqlglot
    from sqlglot import expressions as exp
except ImportError:
    sqlglot = None
    exp = None


TABLE_PATTERN = re.compile(r"\b(?:from|join)\s+([a-zA-Z_][\w.]*)(?:\s+(?:as\s+)?([a-zA-Z_]\w*))?", re.IGNORECASE)
WHERE_PATTERN = re.compile(r"\bwhere\b(?P<where>.*?)(?:\bgroup\s+by\b|\border\s+by\b|\blimit\b|$)", re.IGNORECASE | re.DOTALL)
FUNCTION_FILTER_PATTERN = re.compile(r"\b(date|date_trunc|substr|substring|cast)\s*\(\s*([a-zA-Z_][\w.]*)", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedSql:
    normalized_sql: str
    parser_engine: str
    tables: tuple[str, ...]
    aliases: dict[str, str]
    has_select_star: bool
    where_clause: str
    function_wrapped_columns: tuple[str, ...]
    join_count: int
    line_count: int
    cte_count: int
    subquery_count: int
    union_count: int
    window_function_count: int
    case_count: int


def parse_sql(sql: str) -> ParsedSql:
    normalized = strip_comments(sql)
    line_count = len([line for line in sql.splitlines() if line.strip()])
    if sqlglot is not None:
        try:
            return parse_with_sqlglot(normalized, line_count)
        except Exception:
            # SQL dialects vary. The prototype remains usable for unsupported SQL.
            pass

    tables: list[str] = []
    aliases: dict[str, str] = {}

    for table, alias in TABLE_PATTERN.findall(normalized):
        table_name = table.lower()
        tables.append(table_name)
        if alias and alias.lower() not in {"where", "on", "left", "right", "inner", "full", "cross", "join"}:
            aliases[alias.lower()] = table_name

    where_match = WHERE_PATTERN.search(normalized)
    where_clause = where_match.group("where").strip() if where_match else ""
    function_columns = tuple(match.group(2).lower() for match in FUNCTION_FILTER_PATTERN.finditer(where_clause))

    return ParsedSql(
        normalized_sql=normalized,
        parser_engine="regex fallback (install sqlglot for AST parsing)",
        tables=tuple(dict.fromkeys(tables)),
        aliases=aliases,
        has_select_star=bool(re.search(r"\bselect\s+\*", normalized, re.IGNORECASE)),
        where_clause=where_clause,
        function_wrapped_columns=function_columns,
        join_count=len(re.findall(r"\bjoin\b", normalized, re.IGNORECASE)),
        line_count=line_count,
        cte_count=len(re.findall(r"\b(?:with|,)\s*[a-zA-Z_]\w*\s+as\s*\(", normalized, re.IGNORECASE)),
        subquery_count=len(re.findall(r"\(\s*select\b", normalized, re.IGNORECASE)),
        union_count=len(re.findall(r"\bunion(?:\s+all)?\b", normalized, re.IGNORECASE)),
        window_function_count=len(re.findall(r"\bover\s*\(", normalized, re.IGNORECASE)),
        case_count=len(re.findall(r"\bcase\b", normalized, re.IGNORECASE)),
    )


def parse_with_sqlglot(normalized: str, line_count: int) -> ParsedSql:
    tree = sqlglot.parse_one(normalized)
    tables = tuple(dict.fromkeys(table.name.lower() for table in tree.find_all(exp.Table)))
    aliases = {}
    for table in tree.find_all(exp.Table):
        if table.alias:
            aliases[table.alias.lower()] = table.name.lower()

    where = tree.find(exp.Where)
    where_clause = where.this.sql() if where else ""
    function_columns = []
    if where:
        for function in where.find_all(exp.Func):
            column = function.find(exp.Column)
            if column:
                function_columns.append(column.sql().lower())

    return ParsedSql(
        normalized_sql=normalized,
        parser_engine="sqlglot AST",
        tables=tables,
        aliases=aliases,
        has_select_star=any(isinstance(star, exp.Star) for star in tree.find_all(exp.Star)),
        where_clause=where_clause,
        function_wrapped_columns=tuple(dict.fromkeys(function_columns)),
        join_count=sum(1 for _ in tree.find_all(exp.Join)),
        line_count=line_count,
        cte_count=sum(1 for _ in tree.find_all(exp.CTE)),
        subquery_count=sum(1 for _ in tree.find_all(exp.Subquery)),
        union_count=sum(1 for _ in tree.find_all(exp.Union)),
        window_function_count=sum(1 for _ in tree.find_all(exp.Window)),
        case_count=sum(1 for _ in tree.find_all(exp.Case)),
    )


def strip_comments(sql: str) -> str:
    without_line_comments = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    without_block_comments = re.sub(r"/\*.*?\*/", "", without_line_comments, flags=re.DOTALL)
    return re.sub(r"\s+", " ", without_block_comments).strip()
