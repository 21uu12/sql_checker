# SQL Governance Agent

一个用于学习 Codex 工程化工作方式的可接入项目雏形。

它现在做的事很小：

```text
SQL 文件 + 表元数据
        ↓
复杂度评估 + 自动路由
        ↓
Markdown 治理报告
```

这比“直接问 AI 优化 SQL”多了三件关键事：

- 项目上下文固定在 `AGENTS.md`，不用每次重新解释角色和边界。
- 规则沉淀在 `skills/`，优化标准可以持续迭代。
- 可执行逻辑沉淀在 `tools/`，结果可复现、可测试、可接入。

## Quick Start

```powershell
python main.py examples/bad_query.sql --metadata metadata/tables.json --out outputs/bad_query_report.md
```

## Review a SQL Circle

Review every `.sql` file in a local Git working directory and write one summary report:

```powershell
python circle.py <git-working-directory> --metadata metadata/tables.json --out outputs/circle_report.md
```

The Circle score starts at 100 for every SQL file. Each P1 finding deducts 25 points and each P2 finding deducts 10 points. The final Circle score is the average across reviewed SQL files. Complex SQL is marked for deeper review; it is not executed or modified.

第二版新增复杂度路由：

```powershell
python main.py examples/complex_query.sql --metadata metadata/tables.json --out outputs/complex_query_report.md
```

简单 SQL 走可重复执行的本地规则。复杂 SQL（CTE、子查询、窗口函数、UNION、多 JOIN 等）会生成一个受约束的 Agent 审阅任务。当前版本不会自行调用模型或产生费用；报告中会附上需要提交给模型的 Prompt。未来接入模型后，模型必须返回规定 JSON，再由程序写入 Markdown，不能直接让模型随意生成报告。

`sqlglot` 是 SQL 的结构化解析库。它将 SQL 变成语法树（AST），比正则更能处理 CTE、嵌套查询和别名。安装依赖后启用：

```powershell
python -m pip install -r requirements.txt
```

当前电脑无法连接 Python 包仓库时，程序仍可使用兼容解析器运行，并在报告的 `Parser` 一行明确提示。安装成功后会自动切换到 `sqlglot AST`。

## Project Layout

```text
sql-governance-agent/
├── AGENTS.md
├── README.md
├── main.py
├── examples/
│   ├── bad_query.sql
│   ├── complex_query.sql
│   └── good_query.sql
├── metadata/
│   └── tables.json
├── outputs/
├── skills/
│   ├── sql_review.md
│   ├── starrocks_optimization.md
│   └── report_format.md
└── tools/
    ├── analyzer.py
    ├── complexity.py
    ├── llm_reviewer.py
    ├── metadata.py
    ├── report.py
    └── sql_parser.py
```

## Learning Path

1. v0: 本地 SQL 文件分析，也就是当前版本。
2. v1: 接入 StarRocks query log，把 `query_id / scan_bytes / cpu_time / sql` 作为输入。
3. v2: 接入 Google Sheet 治理表，写回报告和负责人。
4. v3: 接入企业微信/飞书，但默认只生成消息草稿，人工确认后发送。
5. v4: 拆分 SubAgent：SQL 分析、血缘、负责人检索、报告生成。

## How To Learn Codex With This Project

每次不要只问“帮我写代码”。更好的问法是：

```text
请阅读 AGENTS.md、skills/sql_review.md 和 tools/analyzer.py。
在不改变现有输出格式的前提下，增加一条规则：
当 WHERE 中没有任何时间过滤条件时，标记为 P1。
同时更新 examples 和 README。
```

这样 Codex 会围绕仓库规则、技能文件、已有代码和示例做增量修改，而不是凭空生成答案。
