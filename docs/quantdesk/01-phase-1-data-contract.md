# QuantDesk Phase 1：日频研究数据契约

## 目标与边界

Phase 1 建立中国 A 股日频研究数据的离线可验证契约。它读取合成或录制 fixture，验证字段、单位、时间和可交易性边界；它不调用 Tushare、不读取 Token、不连接券商，也不能创建真实订单。

首个范围仅限：

- `SSE` 与 `SZSE` 普通股代码（`.SH`、`.SZ`）；
- Tushare `daily` 的日频原始行情；
- 研究层的数据质量、信息可用时间和日级可交易性判断。

## 时间语义

每条标准化记录必须携带：

| 字段 | 含义 |
|---|---|
| `event_time` | 市场事件实际发生时间 |
| `available_at` | 策略最早可合法使用该信息的时间 |
| `retrieved_at` | QuantDesk 实际取得这个快照的时间 |

这些时间均要求包含时区。策略决策时间早于 `available_at` 时，数据不可使用。

## 价格与单位

`DailyBarRaw` 保留供应商原始语义。`DailyBar` 同时保存原始和标准化数值，防止隐式换算：

| 供应商字段 | 原始单位 | 标准字段 | 换算 |
|---|---:|---|---:|
| `vol` | 手 | `volume_shares` | `vol × 100` |
| `amount` | 千元人民币 | `turnover_cny` | `amount × 1000` |

`open`、`high`、`low`、`close` 和 `pre_close` 在 Phase 1 中均是原始研究/执行参考价。复权研究价必须由后续模块生成并明确命名，不能覆盖这些字段。

## 可交易性

日线不足以证明订单能够成交。因此结果只有三种：

- `TRADEABLE`：当前已知日级约束未阻止交易；
- `NOT_TRADEABLE`：有明确停牌证据；
- `UNKNOWN`：缺少行情、涨跌停或停牌证据，或收盘位于对应价格限制。

`UNKNOWN` 绝不应在回测中自动当作成交。

## 数据质量闸门

进入研究层前，日频记录必须通过：

- `(ts_code, trade_date)` 唯一；
- 有限数值、正价格、非负成交量/成交额；
- `low ≤ open/close ≤ high`；
- 原始单位和标准化单位换算一致；
- `retrieved_at ≥ available_at`。

## 运行验证

```bash
cd /Users/yadongzhai/MyWork/量化/05_实验代码
.venv/bin/python -m pytest -q tests/test_quantdesk_contracts.py tests/test_quantdesk_tradability.py
```

## Phase 2 的认证边界

Tushare Pro 适配器在 `quantdesk.providers` 中实现为可注入 transport 的接口。导入模块或创建 Provider 不会发生网络调用；只有显式调用 `query()` 才可能发出请求。

- Token 仅从单次进程的 `TUSHARE_TOKEN` 环境变量读取；
- QuantDesk 不调用会把 Token 写入用户目录的 `set_token()`；
- `.env` 被 Git 忽略，仓库只提供不含值的 `.env.example`；
- 运行时请求、异常和审计对象都不保存或输出 Token；
- 在实际账户权限、许可与历史覆盖未核验前，测试应只使用 fake transport 或 fixture。

Tushare 官方 Python 客户端资料显示其动态接口将 `api_name`、`params`、`fields` 和 Token 发给服务端。QuantDesk 因此将 endpoint 限制为已审查的十个接口，并把网络层保留为显式注入点，而不是让教学代码在导入时自行联网。

## 离线端到端实验

运行 `labs/lab_09_quantdesk_research_store.py` 可以验证：

```text
合成 provider-shaped payload
  -> immutable raw snapshot + manifest
  -> normalized DailyBar
  -> versioned SQLite
  -> provenance-preserving research frame
  -> existing quantlearn SMA backtest
```

该实验只使用合成数据，不代表 Tushare 历史数据已获得、已授权或已完成质量核验。
