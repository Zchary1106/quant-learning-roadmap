# QuantDesk：统一导入编排器

`ingest_tushare_result()` 连接已经彼此分离的四层：

```text
Explicit Provider QueryResult
  -> immutable raw response + manifest
  -> endpoint-specific normalizer
  -> daily_bars or reference_records
  -> fixed snapshot_id for research reads
```

它不是网络抓取函数。网络调用、Token、原始响应、数据可用时间和标准化规则仍然是可独立审计的输入。

## 必填边界

- `result.endpoint` 必须和 `SourceMetadata.endpoint` 一致；
- `daily`、日历、复权、分红、停复牌、ST、日度指标、指数成分必须显式提供 `availability_for`；
- `stock_st` 必须显式提供已验证的 `type_mapping`；
- raw response 缺失时会写出带 `raw_response_unavailable: true` 的重建信封，不能伪称保存了原始服务端响应；
- `daily` 进入专用 `daily_bars`；其余记录进入通用、不可变的 `reference_records`。

## Lab 11

```bash
cd /Users/yadongzhai/MyWork/量化/05_实验代码
.venv/bin/python labs/lab_11_quantdesk_ingestion.py
```

Lab 11 使用 fixture 验证整个编排链，不能替代真实数据权限、许可、覆盖或 point-in-time 完整性验证。
