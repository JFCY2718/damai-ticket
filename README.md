# 大麦网自动抢票脚本

基于 uiautomator2 的大麦网 App 自动抢票工具，适用于 Android 手机。

## 功能

- NTP 时间同步，精准卡点抢票
- 自动点击购买按钮，支持多次重试
- 支持选择票档和购买数量
- 自动确认订单

## 环境要求

- Python 3.8+
- Android 手机（已开启 USB 调试）
- 数据线连接电脑

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

1. 手机通过 USB 连接电脑，开启 USB 调试
2. 打开大麦 App，登录账号，进入目标演出详情页
3. 运行脚本：

```bash
# 默认 19:00 开抢，第一档票，1张
python damai_ticket.py

# 自定义参数
python damai_ticket.py --time "20:00:00" --ticket-index 0 --count 2

# 提前 1 秒开始点击
python damai_ticket.py --time "19:00:00" --advance 1.0
```

## 参数说明

| 参数 | 缩写 | 默认值 | 说明 |
|------|------|--------|------|
| `--time` | `-t` | 19:00:00 | 抢票时间（HH:MM:SS） |
| `--ticket-index` | `-i` | 0 | 票档索引（0=第一档） |
| `--count` | `-c` | 1 | 购买张数 |
| `--advance` | `-a` | 0.5 | 提前开始点击的秒数 |

## 提高成功率的建议

- 确保手机性能足够，关闭后台无关应用
- 使用稳定的网络（WiFi 或 5G）
- 提前打开演出详情页，让页面完全加载
- 适当增大 `--advance` 参数

## 免责声明

本项目仅供学习交流使用，请遵守大麦网用户协议及相关法律法规。使用本脚本产生的一切后果由使用者自行承担。

## License

MIT
