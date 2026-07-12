# SQL 增量治理

这是一个面向 GitHub SQL 仓库的自动治理工具。每次提交或更新 `sql/` 目录中的 SQL 后，GitHub Actions 只分析本次变更的 SQL，并与上一版内容比较。

## 可以做什么

- 自动识别本次新增、修改和删除的 `.sql` 文件。
- 检查 `SELECT *`、函数包装过滤列、缺少 `WHERE`、缺少已知分区过滤条件和多 JOIN 风险。
- 读取 `metadata/tables.json` 中的静态表元数据，补充分区列和负责人信息。
- 对每个变更 SQL 文件评分，并显示与上一版的分数变化。
- 识别 CTE、子查询、窗口函数、`UNION` 等复杂 SQL，并标记为深度复核。
- 在 GitHub Actions 摘要中展示完整 Markdown 报告。
- 在 PR 中自动新增或更新 SQL 变更评论。
- 将完整报告保存为 GitHub Actions 构建产物，保留 30 天。

## 工作方式

```text
提交或更新 `sql/` 中的 SQL
        ↓
GitHub Actions 被触发
        ↓
准备临时 Python 环境并安装依赖
        ↓
识别本次提交变更的 SQL，并读取每个文件的上一版内容
        ↓
仅对新增和修改的 SQL 执行确定性规则、计算评分和复杂度
        ↓
生成 SQL 增量 Markdown 报告
        ↓
Actions 摘要、报告产物和 PR 评分评论
```

工作流定义在 `.github/workflows/sql-governance.yml`。当 `sql/` 下的 `.sql` 文件、表元数据或治理程序发生变化时，会自动触发；也可以在 GitHub Actions 页面手动运行。

## 上传 SQL

将 SQL 放在 `sql/` 下，可按业务主题建立独立目录：

```text
sql/
└── daily_order/
    ├── order_summary.sql
    └── order_detail.sql
```

提交一个新的 `.sql` 文件后，工作流只审查这个文件；修改已有 SQL 时，会给出与上一版的对比；删除 SQL 时，只记录删除。`examples/` 仅用于本地演示，不参与 GitHub 的正式审查。

## 评分规则

每个 SQL 文件从 100 分开始：

- 每个 P1 发现项扣 25 分。
- 每个 P2 发现项扣 10 分。
- 每个 SQL 文件独立评分，不计算全仓库平均分。

| 分数 | SQL 评价 |
| ---: | --- |
| 90-100 | 良好 |
| 70-89 | 关注 |
| 40-69 | 需要复核 |
| 0-39 | 高风险 |

当前固定规则如下：

| 编码 | 优先级 | 检查内容 |
| --- | --- | --- |
| SQL001 | P2 | 使用 `SELECT *` |
| SQL002 | P1 | 过滤列被函数包装，可能导致分区裁剪失效 |
| SQL003 | P1 | 缺少 `WHERE`，或已知分区表缺少分区过滤条件 |
| SQL004 | P2 | 存在两个或以上的 JOIN，需要进行基数审查 |

## 报告内容

每份报告包含：

- 本次变更的 SQL 文件数量。
- P1、P2 发现项相对上一版的变化。
- 每个变更 SQL 文件的当前分数、上一版分数和变化值。
- 每条问题的证据、影响和修改建议。
- 需要人工确认的后续检查项。

复杂 SQL 会路由到 `agent`，表示需要更深入复核；当前版本仅生成受约束的复核任务，不会调用大模型。

## 本地运行

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

分析单个 SQL：

```powershell
python main.py examples/bad_query.sql --metadata metadata/tables.json --out outputs/report.md
```

分析一个本地 Git 工作目录：

```powershell
python changed_sql.py --source sql --metadata metadata/tables.json --out outputs/changed_sql_report.md --baseline-ref HEAD^
```

没有元数据文件时，程序仍会运行，但只输出可从 SQL 文本中确定的规则结论，不会猜测分区、表规模或负责人。

## 边界

- 不执行 SQL。
- 不自动终止查询。
- 不修改生产任务或 SQL 文件。
- 不自动发送通知。
- 不调用外部大模型 API。

后续若接入 Agent，应保留固定规则评分，并将模型用于复杂 SQL 的解释与优化建议；模型输出必须通过结构化校验后才能写入报告。
