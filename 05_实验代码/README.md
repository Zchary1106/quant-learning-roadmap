# 最小可运行实验

这些实验只用于学习验证，不连接券商、不下真实订单。默认生成合成价格，避免网络和数据许可阻塞。

## 安装

```bash
cd /Users/yadongzhai/MyWork/量化/05_实验代码
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pytest -q
```

## 运行顺序

```bash
python labs/lab_01_metrics.py
python labs/lab_02_sma_backtest.py
python labs/lab_03_factor_ic.py
python labs/lab_04_portfolio_risk.py
python labs/lab_05_real_data_pipeline.py
python labs/lab_06_walk_forward.py
python labs/lab_07_portfolio_tail_risk.py
python labs/lab_08_block_bootstrap.py
```

每个实验先看输出，再做三件事：手算一个小样本；故意制造错误看测试能否抓住；把结论写进研究日志。

## 离线真实数据案例

`data/raw/aapl_2015_2017.csv` 是固定的公开 AAPL 日线快照，来源、获取时间、
字段边界和 SHA-256 写在 `data/aapl_2015_2017.data-card.yml`。Lab 5 会先检查
OHLCV 不变量，再生成 `data/processed/market.sqlite`，其中包含 `raw_ohlcv`、
`clean_ohlcv` 和 `features_daily` 三层表。固定快照用于保证离线可复现，不代表
数据适合严肃 point-in-time 研究或实盘。

Lab 6 只在每个训练窗口内选择均线参数，再拼接连续样本外收益；Lab 7 增加风险
贡献、历史 VaR 和 Expected Shortfall；Lab 8 用移动块 bootstrap 展示时间依赖
如何影响均值区间。这些方法都需要报告假设和敏感性，不能机械套用。

## 练习改造

1. 把合成价格替换为自己的 CSV，但保留原始文件和数据卡。
2. 把均线回测的执行延迟从 1 bar 改成 0，观察不当时序会怎样改变结果。
3. 把成本从 0 调到 5/10/20 bps，画净收益曲线。
4. 修改 Sortino、Calmar 和回撤持续时间的边界约定，并先写测试。
5. 因子实验加入行业分组和换手；风险实验加入权重上限。

## 代码边界

这是一套教学最小实现，不处理真实市场的停牌、涨跌停、部分成交、公司行动、保证金、借券、税费、时区、容量或订单状态。它的价值是把核心公式和时间对齐变得可检查，不是替代成熟框架。
