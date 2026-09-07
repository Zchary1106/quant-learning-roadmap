# QuantDesk 数据源设计 v3.1 审查

审查日期：2026-09-07
审查输入：用户提供的 `quantdesk-data-sources-v3.1.json`

## 结论

v3.1 是一份合格的中国 A 股研究数据源清单，不是完整量化交易系统设计。它正确列出了 Tushare Pro 的主数据、交易日历、日线、复权、分红、涨跌停、停复牌、ST、日度指标和指数成分端点，但仍需由系统实现数据契约、时间可见性、快照版本、质量闸门和可交易性保守规则。

QuantDesk MVP 的定位是**离线优先的日频研究数据底座**。它不接券商、没有真实订单对象，不能执行交易。

## 已采纳的数据源范围

| 设计 ID | Tushare endpoint | MVP 状态 | 处理原则 |
|---|---|---|---|
| D01 | `stock_basic` | Provider 白名单 | 当前状态不作为完整 PIT 历史 |
| D02 | `trade_cal` | `TradingSession` 契约 | 缺少日历记录时不可假设开市 |
| D03 | `daily` | 完整标准化与 SQLite 落库 | 保留原始 OHLC、手/千元单位 |
| D04 | `adj_factor` | 后续研究价模块 | 不覆盖原始执行参考价 |
| D05 | `dividend` | 后续公司行动模块 | 公告、除权、支付时间必须分开 |
| D06 | `stk_limit` | `LimitBand` 契约 | 涨跌停不证明成交 |
| D07 | `suspend_d` | `SuspensionStatus` 契约 | 缺失记录不等于可交易 |
| D08 | `stock_st` | `StStatus` 契约 | 作为风险上下文，不自动禁交易 |
| D09 | `daily_basic` | Provider 白名单 | 未核验字段单位不能隐式换算 |
| D10 | `index_member_all` | `IndexMembership` / universe | 有效区间不等于 PIT 公告证据 |

## 已落实的关键设计决定

1. 数据必须同时表达 `event_time`、`available_at` 和 `retrieved_at`，且三者带时区。
2. 日频标准记录同时保留供应商单位和标准单位：`vol × 100` 为股数，`amount × 1000` 为人民币。
3. 数据以 `snapshot_id` 版本化。原始 JSON 和 manifest 不可静默覆盖；SQLite 的主键为 `(snapshot_id, ts_code, trade_date)`。
4. 可交易性是 `TRADEABLE`、`NOT_TRADEABLE`、`UNKNOWN` 三态。缺数据或收盘贴涨跌停时不能虚构成交。
5. 历史指数成分必须带 PIT 可信度。`EFFECTIVE_INTERVAL_ONLY` 不允许被标为完全 PIT 验证。
6. Tushare Token 只在进程环境变量中读取，永不写入仓库、manifest、异常或审计对象。
7. 当前官方 Python 客户端资料显示其 Pro API 使用 HTTP endpoint。QuantDesk 的 stdlib transport 默认拒绝 HTTP；真实调用需要使用者显式选择 `--allow-insecure-http`。

## 2026-09-07 增量实现

除 `daily` 外，当前实现已对以下设计端点增加 provider-shaped fixture 与显式字段解析：`stock_basic`、`trade_cal`、`adj_factor`、`dividend`、`stk_limit`、`suspend_d`、`stock_st`、`daily_basic`、`index_member_all`。

这些解析器只承认 v3.1 已说明的字段与单位，不会：

- 把 `stock_basic` 当前行业或状态解释为完整 PIT 历史；
- 把 `free_share` 转换到未验证的单位；
- 从 `suspend_d` 单行事件推断完整日内停复牌状态；
- 将未经实际 schema 核验的 `stock_st.type` 映射为交易规则；
- 将 `index_member_all` 的有效区间升级为 PIT 已验证；
- 将 `adj_factor` 替代公司行动现金和股票账本。

## 未完成且不能伪称已完成的事项

- 真实 Tushare 账号权限、历史覆盖、额度、限流和许可尚未验证；
- 没有经过认证的生产数据快照；
- `adj_factor`、分红、ST、停复牌和成分股已支持 fixture 驱动的标准化/版本化落库，但尚未用真实认证数据验证；
- 历史成分、行业、ST 与公司行动是否满足完整 PIT 仍需数据证据；
- 没有撮合、券商接入、真实仓位、订单、资金或账户功能。

## MVP 验收标准

- 离线 fixture 可从 provider 形状数据写入 immutable raw snapshot 和 manifest；
- 标准化日线能在 SQLite 中以固定 `snapshot_id` 读取；
- 单位、OHLC、重复键、时间可见性和版本冲突会被测试拒绝；
- 无交易日历、涨跌停、停牌或行情时不会默认交易；
- 研究 frame 保留版本和可用时间，可桥接既有教学回测；
- 全部测试和 10 个 Lab 在无 Token、无真实网络请求时可运行。
