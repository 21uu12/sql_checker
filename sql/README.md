# SQL 上传目录

将需要治理的 SQL 文件放在此目录中。每次提交或更新这里的 `.sql` 文件，GitHub Actions 会自动执行 Circle 评分。

建议按 Circle 建立子目录：

```text
sql/
└── <circle 名称>/
    ├── order_summary.sql
    └── user_metrics.sql
```

例如，上传一个新 SQL 文件：

```text
sql/daily_order/order_summary.sql
```

系统会扫描 `sql/` 下的全部 SQL 文件，并给出当前 Circle 的汇总评分。`examples/` 中的教学样例不会参与正式评分。
