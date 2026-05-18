# Polymarket Analytics

Polymarket 预测市场分析工具，数据洞察 + 交易辅助。

## 功能列表

- **市场扫描**：全市场实时价格/流动性排行
- **概率分析**：多维度球队/事件概率比较
- **历史数据**：价格走势图、成交量分析
- **套利机会**：检测跨市场套利空间
- **警报通知**：价格异动时自动通知

## 数据来源

- Polymarket Gamma API（免费公开）
- Polymarket CLOB API（需认证）

## 安装

```bash
pip install -r requirements.txt
python main.py
```

## 策略思路

- 流动性覆盖率：流动性高的市场滑点低
- 概率差检测：检测概率与基本面的偏差
- 资金流向：追踪大资金动向

⚠️ 风险提示：预测市场有风险，投资需谨慎。
