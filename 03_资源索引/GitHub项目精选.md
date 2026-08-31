# GitHub 开源项目精选

## 选择方法

不是按 Star 排名，而是同时检查：最近代码推送、是否归档、许可证、文档、技术栈、学习目标与上手成本。下表元数据来自 GitHub 公共 API，快照日期为 **2026-08-30**；Star 和活跃度会变化。

## 推荐主线

| 项目 | 快照（约 Star / 最近推送） | 许可 | 最适合学什么 | 建议 |
|---|---:|---|---|---|
| [AKShare](https://github.com/akfamily/akshare) | 22.3k / 2026-08-28 | MIT | 中国公开财经接口、字段与数据清洗 | 第 2 周起按需用；生产稳定性与上游授权另评估 |
| [yfinance](https://github.com/ranaroussi/yfinance) | 25.1k / 2026-08-27 | Apache-2.0 | 快速获取海外学习数据、接口封装 | 适合原型；遵守 Yahoo 数据条款，不作为唯一生产源 |
| [backtesting.py](https://github.com/kernc/backtesting.py) | 8.9k / 2026-08-05 | AGPL-3.0 | 小型策略、API 简洁、可视化 | 第 9 周入门；分发/服务场景先理解 AGPL |
| [bt](https://github.com/pmorissette/bt) | 3.0k / 2026-08-07 | MIT | 资产配置、权重算法、组合回测 | 第 15 周用于和自写组合比较 |
| [zipline-reloaded](https://github.com/stefan-jansen/zipline-reloaded) | 1.9k / 2026-01-06 | Apache-2.0 | Zipline 范式、事件和管线式研究 | 想学 Zipline 时优先于原仓库 |
| [Qlib](https://github.com/microsoft/qlib) | 48.1k / 2026-07-23 | MIT | 因子、ML 工作流、数据与实验管理 | 第 14/17 周；先理解其约定再跑大型例子 |
| [VeighNa/vn.py](https://github.com/vnpy/vnpy) | 44.9k / 2026-08-28 | MIT | 中国交易生态、网关、事件驱动 | 工程分支首选；先模拟，不直接接真实账户 |
| [LEAN](https://github.com/QuantConnect/Lean) | 21.4k / 2026-08-28 | Apache-2.0 | 多资产全栈引擎、算法框架 | C#/Python；规模大，按事件/组合/订单模块阅读 |
| [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) | 28.1k / 2026-08-30 | LGPL-3.0 | 确定性事件驱动、回放、订单模型 | 高阶工程阅读；Rust 内核，上手成本高 |
| [WonderTrader](https://github.com/wondertrader/wondertrader) | 6.3k / 2025-09-30 | MIT | 中国期货/多策略框架、C++ 核心 | 工程分支对比 vn.py；先读架构和示例 |
| [machine-learning-for-trading](https://github.com/stefan-jansen/machine-learning-for-trading) | 20.7k / 2026-08-30 | MIT | 从数据到 ML/回测的配套实验 | ML 分支教材库；逐章重做，不只运行 Notebook |
| [FinRL](https://github.com/AI4Finance-Foundation/FinRL) | 16.2k / 2026-07-13 | MIT | 金融强化学习实验框架 | 高阶专题；先用规则/监督基准审视环境和奖励 |

## 按特殊市场选择

- [Freqtrade](https://github.com/freqtrade/freqtrade)：约 53.8k Star，2026-08-27 推送，GPL-3.0；适合学习加密交易机器人、回测、优化和部署。加密市场和托管/交易所风险不能外推到股票。
- [Hummingbot](https://github.com/hummingbot/hummingbot)：约 19.7k，2026-08-28 推送，Apache-2.0；适合连接器、做市和订单执行，高频实盘风险高。
- [RQAlpha](https://github.com/ricequant/rqalpha)：约 6.7k，2026-08-28 推送；学习中国证券回测接口很方便，但许可证对非商业与商业用途分别规定，GitHub API 不能映射为标准 SPDX，使用前阅读仓库 `LICENSE`。
- [vectorbt](https://github.com/polakowo/vectorbt)：约 8.9k，2026-08-02 推送；适合批量向量化实验。仓库为 Commons Clause 条件的自定义许可，GitHub API 显示 `NOASSERTION`，尤其商业使用前逐条核对。

## 历史影响大，但不作为新手主线

| 项目 | 快照证据 | 怎么用 |
|---|---|---|
| [Quantopian/zipline](https://github.com/quantopian/zipline) | 未归档，但最近推送 2024-02 | 读架构/历史教程；新环境优先 zipline-reloaded |
| [Backtrader](https://github.com/mementum/backtrader) | 最近推送 2024-08，GPL-3.0 | 学 Strategy/Indicator/Broker 抽象；依赖兼容需自测 |
| [PyAlgoTrade](https://github.com/gbeced/pyalgotrade) | GitHub 标记 archived，最近推送 2023-11 | 只作历史代码阅读，不启动新项目 |

## 源码学习方法

不要先克隆十几个仓库。每阶段只选一个，用 5 个问题阅读：

1. 最小示例从哪个入口进入？
2. 数据、策略、组合、订单、成交的对象边界是什么？
3. 时间和交易日历如何表示？
4. 费用、滑点、部分成交和状态恢复在哪里实现？
5. 哪些假设是默认值，若换到你的市场会失效？

建议顺序：`backtesting.py → bt/zipline-reloaded → Qlib（研究）或 vn.py（工程） → LEAN/NautilusTrader（高阶）`。每读一个项目，画一张调用链并实现一个 100 行以内的同类最小版本。
