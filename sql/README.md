# SQL 上传目录

将需要治理的 SQL 文件放在此目录中。每次提交或更新这里的 `.sql` 文件，GitHub Actions 会自动执行增量 SQL 审查。

可按业务主题建立子目录：

```text
sql/
└── <业务主题>/
    ├── order_summary.sql
    └── user_metrics.sql
```

例如，上传一个新 SQL 文件：

```text
sql/daily_order/order_summary.sql
```

系统只审查本次提交中新增或修改的 SQL，并与文件上一版内容比较。`examples/` 中的教学样例不会参与正式审查。
