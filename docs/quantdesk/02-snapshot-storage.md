# QuantDesk Phase 3：不可变快照与研究库

## 为什么数据版本必须是一等对象

回测结果只有在数据、代码、参数和时间语义固定时才能复现。QuantDesk 因此不允许原始快照或标准化日线“静默覆盖”：

```text
Provider response
  -> raw/<snapshot_id>/<endpoint>.json
  -> raw/<snapshot_id>/<endpoint>.manifest.json
  -> SQLite daily_bars(snapshot_id, ts_code, trade_date)
```

## Raw Snapshot

每个原始 JSON 快照都配套 manifest，至少记录：

- `snapshot_id`、provider、endpoint、source URL；
- 获取时间、请求参数和返回字段；
- 行数和 SHA-256；
- 原始 JSON 的规范化字节序列。

同一 `snapshot_id/endpoint` 重复写入相同内容是幂等的；写入不同内容会失败，而不是覆盖旧证据。

## SQLite 研究层

`daily_bars` 的键是 `(snapshot_id, ts_code, trade_date)`，使两个历史版本可以共存。再次写入相同条目不会重复；相同键但不同内容会失败。研究代码必须显式指定 `snapshot_id`，不能不加版本地读取“最新数据”。

## 数据质量和恢复

- 写入前执行日频质量闸门；
- 所有 bar 要有同一个 source snapshot；
- SQLite 开启外键约束；
- 本地 raw 和 research 数据库都被 `.gitignore` 忽略，避免把未经审查的大型或受限数据上传；
- fixture 位于 `tests/fixtures/`，用于离线、确定性测试。

## 运行验证

```bash
cd /Users/yadongzhai/MyWork/量化/05_实验代码
.venv/bin/python -m pytest -q tests/test_quantdesk_storage.py
```

## 研究桥接

`quantdesk.research` 可以将固定版本的 `DailyBar` 转为：

- 保留 `snapshot_id` 和 `available_at` 的 research frame；
- 供现有 `quantlearn` 教学函数读取的未复权 OHLCV frame。

桥接不会删除数据版本，也不把日线变成成交保证。策略代码仍需显式处理决策时点、可交易性状态和执行成本。
