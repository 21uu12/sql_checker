SELECT *
FROM dwd_order_detail
-- N8N Webhook 集成测试：此注释不影响 SQL 评分。
WHERE create_time >= '2026-07-01'
  AND create_time < '2026-07-02';
