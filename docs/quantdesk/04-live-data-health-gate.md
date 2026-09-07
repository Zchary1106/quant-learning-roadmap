# QuantDesk Phase 6：真实数据健康检查闸门

## 当前状态

设计文档记录的端点字段来自 Tushare 文档，但当前仓库尚未使用真实 Token 执行认证调用。因此以下事实仍未被仓库验证：

- 当前账号是否有各端点权限；
- 实际历史覆盖、空值语义和字段值；
- API 速率、额度和数据许可；
- 供应商历史数据是否足以支持 point-in-time 研究。

## 已实现的安全入口

`labs/lab_10_live_tushare_health_check.py` 默认只打印安全提示，**不发送请求**。真实只读检查必须同时满足：

1. 你在本机进程环境中设置 `TUSHARE_TOKEN`；
2. 你手动添加 `--live`；
3. 若使用 Tushare 当前文档/客户端所示的 HTTP endpoint，你另外手动添加 `--allow-insecure-http`。

```bash
cd /Users/yadongzhai/MyWork/量化/05_实验代码
source .venv/bin/activate
python labs/lab_10_live_tushare_health_check.py

# 仅在你核对 Tushare 条款、数据权限和 HTTP 传输风险后：
python labs/lab_10_live_tushare_health_check.py --live --allow-insecure-http
```

该检查只读取一个小范围的 `daily` 响应，并比对字段 schema。它不是批量下载，不证明历史完整性，也不能打开真实交易功能。

## 验收记录模板

完成真实调用后，把以下内容写入独立的、不可含 Token 的数据卡：

- 检查日期和时区；
- endpoint、参数范围、行数和 observed fields；
- 权限/额度观察结果；
- 结果是否符合设计契约；
- 原始快照 manifest 位置；
- 数据完整性、PIT、许可和规则中仍未解决的事项。
