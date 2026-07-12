# StarRocks Optimization Skill

StarRocks-oriented rules for this project:

- Prefer partition pruning through direct range predicates.
- Avoid wrapping partition columns in functions inside `WHERE`.
- Replace `date(create_time) = '2026-07-01'` with:

```sql
create_time >= '2026-07-01'
and create_time < '2026-07-02'
```

- Wide projections increase scan and network cost. Prefer explicit columns.
- For large joins, check:
  - join keys
  - join type
  - whether dimension tables can be filtered first
  - whether fact tables can be pre-aggregated

Do not claim a query is definitely slow without runtime evidence such as scan bytes, profile, CPU time, memory, or row counts. Use "risk" wording until runtime data is available.
