# N8N 通知接入

GitHub Actions 完成 SQL 增量审查后，会生成 `outputs/n8n_payload.json`。配置 N8N Webhook 后，Actions 会将该 JSON 发送给 N8N。

## 负责人通知元数据

`metadata/tables.json` 负责描述表的负责人、分区列和规模；`metadata/owners.json` 负责描述负责人对应的通知目标。

```text
SQL -> 表元数据 -> owner -> 通知目标
```

仓库中的 `approval_queue` 和 `recipient` 都是脱敏示例。团队接入时应替换为公司批准的审批队列、飞书群、企业微信群或工单系统标识，不要把个人手机号、Token 或 Webhook 地址提交到 Git。

## GitHub 配置

在 GitHub 仓库中创建两个 Actions Secret：

```text
N8N_SQL_GOVERNANCE_WEBHOOK_URL
N8N_SQL_GOVERNANCE_WEBHOOK_TOKEN
```

第一个值为 N8N 的 Production Webhook URL。第二个值为你在 N8N Header Auth 凭证中配置的 Token；Actions 将把它放在 `X-SQL-Governance-Token` 请求头中。未完整配置两个 Secret 时，工作流会继续生成报告，但跳过 N8N 发送。

## N8N 工作流

建议的 N8N 节点顺序：

```text
Webhook
  ↓
读取 JSON 中的 summary、recipients、sql_files
  ↓
判断 delivery_mode 是否为 approval_required
  ↓
创建审批任务或治理队列草稿
  ↓
人工批准后，再发送飞书、企业微信或创建 Jira 工单
```

Payload 的 `delivery_mode` 固定为 `approval_required`。因此 N8N 默认不应直接向个人发送通知；只有在人工审批步骤通过后，才能使用 `recipients` 中的通知目标。

## Payload 重点字段

```json
{
  "event_type": "sql_governance_review",
  "delivery_mode": "approval_required",
  "summary": {
    "changed_sql_count": 1,
    "p1_change": 0,
    "p2_change": 1,
    "worsened_sql_count": 0
  },
  "recipients": {
    "data-platform": [
      {
        "channel": "approval_queue",
        "recipient": "data-platform-governance"
      }
    ]
  }
}
```
