# 用这个项目学习 Codex 工程化

## 你要学的不是“让 AI 回答”

直接问：

```text
帮我优化这段 SQL。
```

通常得到的是一次性建议。它可能有用，但不可积累、不可验证、不可接入。

工程化使用 Codex：

```text
请先阅读 AGENTS.md、skills/starrocks_optimization.md、tools/analyzer.py。
保持现有报告格式不变，增加一条规则：
当大表没有分区字段过滤时输出 P1。
同时更新 bad_query.sql 或新增示例，并运行验证。
```

区别是 Codex 会在一个项目系统里工作：它能读规则、改工具、更新示例、运行验证，并把结果沉淀下来。

## 反例

```text
写一个 SQL 优化 Agent。
```

问题：
- 背景太大，Codex 容易一次生成很多不可维护代码。
- 没有输入输出契约。
- 没有验证方式。
- 没有说明哪些行为禁止，例如自动发通知、自动 kill 查询。

## 正例

```text
我们只做 v0：
输入：一个 SQL 文件。
输出：Markdown 治理报告。
规则：先检查 select *、date(column)、缺少分区过滤。
请把规则放到 skills/，把可执行逻辑放到 tools/，并提供 examples。
```

这个提示更好，因为它给了 Codex：
- 明确边界。
- 可实现的第一步。
- 项目结构要求。
- 可验证结果。

## 你接下来应该怎么练

### 练习 1：增加一条确定性规则

目标：

```text
当 SQL 没有 WHERE 时，标记 P1。
```

提示方式：

```text
请阅读 tools/analyzer.py 和 skills/sql_review.md。
给 analyzer 增加“缺少 WHERE 标记 P1”的规则。
更新 examples，运行 bad/good 两个样例，告诉我报告变化。
```

你学到的是：
- Codex 如何读已有代码。
- 如何做小步增量修改。
- 如何让规则、代码、示例同步。

### 练习 2：接入 query log CSV

目标：

```text
输入从单个 SQL 文件升级为 query_log.csv。
```

CSV 字段：

```text
query_id,user,scan_bytes,cpu_ms,sql
```

提示方式：

```text
在不破坏 main.py 现有 SQL 文件输入的前提下，新增 analyze-log 子命令。
读取 examples/query_log.csv，对每条 SQL 生成一份报告摘要。
scan_bytes > 50GB 时标记 P1。
```

你学到的是：
- 兼容旧接口。
- 把业务指标接入治理规则。
- 从“代码生成”转向“工作流扩展”。

### 练习 3：生成通知草稿，不自动发送

目标：

```text
根据报告生成企业微信/飞书通知草稿。
```

提示方式：

```text
新增 tools/notification.py，只生成通知草稿，不发送。
遵守 AGENTS.md：任何外部发送都必须人工确认。
报告里增加 notification_draft 字段或单独输出 notification.md。
```

你学到的是：
- Agent 的动作边界。
- 为什么真实生产 Agent 需要人工参与决策。

## 这个项目和直接问 AI 的本质区别

直接问 AI：

```text
问题 → 回答 → 结束
```

这个项目：

```text
上下文 → 规则 → 工具 → 示例 → 验证 → 报告 → 下一轮迭代
```

直接问适合临时理解概念。

工程化 Codex 适合：
- 长期维护项目。
- 把知识沉淀成规则。
- 把规则变成工具。
- 把工具接入真实流程。
- 让每次改动都能验证。

## 最重要的 Codex 提示模板

```text
请先阅读这些文件：
- AGENTS.md
- skills/<相关规则>.md
- tools/<相关代码>.py

目标：
<一句话说明这次要实现什么>

约束：
- 不改变现有 CLI 行为，除非必要。
- 不自动执行外部副作用。
- 更新示例和 README。
- 运行验证命令，并说明结果。
```

这个模板比“帮我做一个 Agent”强，因为它把 Codex 放进了一个可控的软件工程循环。
