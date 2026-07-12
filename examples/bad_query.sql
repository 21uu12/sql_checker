select *
from dwd_order_detail a
left join dim_user b
  on a.user_id = b.user_id
where date(a.create_time) = '2026-07-01'
  and b.status = 'active';
