select
  a.order_id,
  a.user_id,
  a.amount,
  b.user_level
from dwd_order_detail a
left join dim_user b
  on a.user_id = b.user_id
where a.create_time >= '2026-07-01'
  and a.create_time < '2026-07-02'
  and b.status = 'active';
