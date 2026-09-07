# QuantDesk Phase 4：历史资产池与可交易性

## 历史资产池不是今天的成分股

`index_member_all` 的 `in_date` / `out_date` 只能表达有效区间。它们不能自动证明策略在历史决策日知道某只股票已进入或退出指数。因此 QuantDesk 的 `IndexMembership` 必须同时记录：

- 有效开始/结束日期；
- `available_at`；
- PIT 可信度：`VERIFIED`、`EFFECTIVE_INTERVAL_ONLY` 或 `UNKNOWN`；
- source snapshot。

`build_index_universe()` 会将尚未在决策时点可见的活跃成分放到 `unresolved_codes`。只有没有未解决记录且全部资料是 `VERIFIED` 时，`require_verified_point_in_time()` 才允许将资产池标记为 PIT 已验证。

## 可交易性不是一个简单布尔值

日线研究使用三个状态：

| 结果 | 含义 |
|---|---|
| `TRADEABLE` | 已知日级证据没有阻止交易 |
| `NOT_TRADEABLE` | 交易日历明确关闭，或明确处于停牌 |
| `UNKNOWN` | 行情、日历、停牌或涨跌停证据不完整，或收盘贴近对应涨跌停 |

日线收盘价落在涨停附近不证明买单可成交，跌停附近也不证明卖单可成交。因此此类情况返回 `UNKNOWN`，回测必须使用保守执行规则而不是自动假设成交。

ST 状态被保留为风险和规则上下文，不能简单解释为不可交易。

## 运行验证

```bash
cd /Users/yadongzhai/MyWork/量化/05_实验代码
.venv/bin/python -m pytest -q tests/test_quantdesk_universe.py tests/test_quantdesk_tradability.py
```
