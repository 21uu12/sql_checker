# SQL 治理 Circle

这是一个面向 GitHub SQL 仓库的自动治理工具。每次提交或更新 SQL 后，GitHub Actions 会自动扫描仓库中的 SQL 文件，按固定规则评分，并生成 Circle 评价报告。

## 可以做什么

- 自动扫描 Git 仓库中的全部 `.sql` 文件。
- 检查 `SELECT *`、函数包装过滤列、缺少 `WHERE`、缺少已知分区过滤条件和多 JOIN 风险。
- 读取 `metadata/tables.json` 中的静态表元数据，补充分区列和负责人信息。
- 对每个 SQL 文件评分，并汇总为整个 Circle 的评分和评价。
- 识别 CTE、子查询、窗口函数、`UNION` 等复杂 SQL，并标记为深度复核。
- 在 GitHub Actions 摘要中展示完整 Markdown 报告。
- 在 PR 中自动新增或更新 Circle 评分评论。
- 将完整报告保存为 GitHub Actions 构建产物，保留 30 天。

## 工作方式

```text
提交或更新 SQL
        ↓
GitHub Actions 被触发
        ↓
准备临时 Python 环境并安装依赖
        ↓
运行 circle.py 扫描全部 SQL
        ↓
执行确定性规则、计算评分和复杂度
        ↓
生成 Circle Markdown 报告
        ↓
Actions 摘要、报告产物和 PR 评分评论
```

工作流定义在 `.github/workflows/sql-governance.yml`。当 `.sql` 文件、表元数据或治理程序发生变化时，会自动触发；也可以在 GitHub Actions 页面手动运行。

## 评分规则

每个 SQL 文件从 100 分开始：

- 每个 P1 发现项扣 25 分。
- 每个 P2 发现项扣 10 分。
- Circle 评分为全部 SQL 文件评分的平均值。

| 分数 | Circle 评价 |
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

- Circle 评分与评价。
- P1、P2 发现项数量。
- 每个 SQL 文件的分数、评价和审查路由。
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
python circle.py <Git 工作目录> --metadata metadata/tables.json --out outputs/circle_report.md
```

没有元数据文件时，程序仍会运行，但只输出可从 SQL 文本中确定的规则结论，不会猜测分区、表规模或负责人。

## 边界

- 不执行 SQL。
- 不自动终止查询。
- 不修改生产任务或 SQL 文件。
- 不自动发送通知。
- 不调用外部大模型 API。

后续若接入 Agent，应保留固定规则评分，并将模型用于复杂 SQL 的解释与优化建议；模型输出必须通过结构化校验后才能写入报告。
