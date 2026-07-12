WITH recent_orders AS (
    SELECT
        user_id,
        order_id,
        amount,
        create_time,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY create_time DESC
        ) AS row_num
    FROM dwd_order_detail
    WHERE create_time >= '2026-07-01'
),
active_users AS (
    SELECT user_id
    FROM dim_user
    WHERE status = 'active'
)
SELECT
    u.user_id,
    CASE WHEN o.amount > 1000 THEN 'high_value' ELSE 'standard' END AS user_type
FROM active_users u
LEFT JOIN recent_orders o ON u.user_id = o.user_id AND o.row_num = 1
WHERE EXISTS (
    SELECT 1
    FROM dwd_order_detail check_order
    WHERE check_order.user_id = u.user_id
)
UNION ALL
SELECT user_id, 'unknown' AS user_type
FROM dim_user
WHERE status IS NULL;
