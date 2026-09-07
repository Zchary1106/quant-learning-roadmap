# QuantDesk：非日线参考记录的版本化存储

`daily` 以专用 `daily_bars` 表存储，因为它会直接喂给日频研究。其余数据源使用 `reference_records`：

```text
(snapshot_id, endpoint, record_key)
  -> record_type
  -> JSON-safe normalized record
  -> record SHA-256
```

这种设计保留不同记录类型的字段边界，同时避免把未经验证的公司行动、ST 规则或成分股有效区间强行压缩为同一种日线表。

## 不可变规则

- 同一记录重复写入相同值是幂等的；
- 相同 `snapshot_id/endpoint/record_key` 出现不同值会拒绝，不能覆盖；
- 不同 endpoint 或 snapshot 可以并存；
- 读取必须显式指定 `snapshot_id` 与 endpoint；
- 写入记录会保留 `source`、时间、枚举和日期的 JSON-safe 表达。

## 当前边界

引用记录已能标准化和版本化落库，但只有 `daily` 已接入现有 `quantlearn` 回测桥接。公司行动现金账本、复权研究价、完整停复牌状态重建和 PIT 资产池仍需在真实数据权限与覆盖验证后实现。
