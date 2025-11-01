# 📊 Web监控页面

Trading AI 提供了一个美观的Web监控页面，可以实时查看交易数据、分析结果和统计信息。

## 🌟 功能特性

### 1. **实时统计卡片**
- 📈 总交易次数
- 🎯 胜率（含胜负次数）
- 💹 盈亏比（平均盈利/平均亏损）
- 💰 净利润和ROI

### 2. **分析结果展示**
- 查看最近的AI分析结果
- 显示交易对、方向、入场价、止损、止盈
- 展示信心度和分析理由

### 3. **交易记录查看**
- 历史交易记录
- 盈亏情况
- 入场和出场价格

### 4. **多时间周期统计**
- 7天统计
- 30天统计
- 自定义周期

## 🚀 快速开始

### 方式一：启用Web监控（默认）

Web监控默认启用，只需正常启动程序：

```bash
python main.py
```

访问地址：**http://localhost:8080**

### 方式二：自定义端口

在 `.env` 文件中配置：

```env
WEB_ENABLED=true
WEB_PORT=8080
```

### 方式三：禁用Web监控

如果不需要Web监控，可以在 `.env` 中禁用：

```env
WEB_ENABLED=false
```

## 🎨 页面预览

### 主仪表板
- **顶部**: 4个统计卡片（交易次数、胜率、盈亏比、净利润）
- **中部**: 选项卡切换（分析结果、交易记录、7天统计）
- **底部**: 最后更新时间

### 分析结果标签页
每条分析记录显示：
- 交易对（如 BTCUSDT）
- 操作方向（做多/做空/观望）
- 入场价格
- 止损价格
- 止盈价格
- 信心度
- 分析时间
- 分析理由

### 交易记录标签页
每条交易记录显示：
- 交易对
- 盈亏金额
- 入场价格
- 出场价格
- 杠杆倍数
- 交易时间

### 7天统计标签页
- 交易次数
- 胜率
- 盈亏比
- 净利润
- 平均盈利
- 平均亏损

## 🔄 数据更新

### 自动刷新
页面每**30秒**自动刷新一次数据

### 手动刷新
点击右上角的 **🔄 刷新数据** 按钮

## 📡 API接口

Web服务器提供以下REST API：

### 1. 获取仪表板数据
```
GET /api/dashboard
```

**响应**:
```json
{
  "success": true,
  "data": {
    "recent_analysis": [...],
    "stats_7d": {...},
    "stats_30d": {...},
    "all_trades": [...]
  },
  "timestamp": "2025-11-01T12:00:00"
}
```

### 2. 获取统计数据
```
GET /api/stats?days=30
```

**参数**:
- `days`: 统计天数（默认30）

### 3. 获取分析结果
```
GET /api/analysis?limit=20
```

**参数**:
- `limit`: 返回数量（默认20）

### 4. 获取交易记录
```
GET /api/trades
```

### 5. 健康检查
```
GET /health
```

## 🐳 Docker部署

在Docker中使用，需要映射端口：

```yaml
# docker-compose.yml
services:
  trading-ai:
    ports:
      - "8080:8080"  # Web监控页面
    environment:
      - WEB_ENABLED=true
      - WEB_PORT=8080
```

启动后访问：**http://服务器IP:8080**

## 🔒 安全建议

### 1. **生产环境使用反向代理**

使用Nginx添加认证：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        auth_basic "Trading AI Monitor";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://localhost:8080;
    }
}
```

### 2. **限制访问IP**

在 `.env` 中只监听本地：

```env
# 仅本地访问
WEB_HOST=127.0.0.1
WEB_PORT=8080
```

### 3. **使用SSH隧道**

远程访问时使用SSH端口转发：

```bash
ssh -L 8080:localhost:8080 user@server
```

然后访问本地：**http://localhost:8080**

## 📊 数据存储

### 分析结果
存储在 `data/analysis/YYYYMMDD/*.json`

### 交易记录
存储在 `data/trades.json`

文件格式：
```json
[
  {
    "symbol": "BTCUSDT",
    "action": "LONG",
    "entry_price": 50000,
    "exit_price": 51000,
    "profit": 100,
    "leverage": 5,
    "timestamp": "2025-11-01T12:00:00"
  }
]
```

## 🎯 常见问题

### Q: Web页面无法访问？
A: 检查：
1. 程序是否正常运行
2. `.env` 中 `WEB_ENABLED=true`
3. 端口是否被占用
4. 防火墙是否开放端口

### Q: 数据不更新？
A: 
1. 检查 `data/` 目录是否有数据
2. 点击"刷新数据"按钮
3. 查看浏览器控制台错误

### Q: 如何在局域网访问？
A: 
1. 确保 `.env` 中未设置 `WEB_HOST`（默认0.0.0.0）
2. 使用服务器IP访问：`http://192.168.x.x:8080`
3. 确保防火墙开放端口

### Q: 可以自定义页面吗？
A: 可以！修改 `tradingai/web/templates/index.html`

### Q: 如何备份数据？
A: 定期备份 `data/` 目录：
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz data/
```

## 🛠️ 高级配置

### 自定义数据目录

在代码中修改：
```python
from tradingai.web import WebServer

web_server = WebServer(
    host="0.0.0.0",
    port=8080,
    data_dir="custom_data_path"  # 自定义数据目录
)
```

### 集成到其他系统

使用API接口获取数据：

```python
import requests

# 获取统计数据
response = requests.get('http://localhost:8080/api/stats?days=7')
stats = response.json()['data']

print(f"胜率: {stats['win_rate']}%")
print(f"盈亏比: {stats['profit_loss_ratio']}")
```

## 📱 移动端适配

页面已适配移动端，可以在手机浏览器访问：
- 响应式布局
- 触摸友好
- 自动适应屏幕

## 🔗 相关文档

- [交易功能](TRADING.md) - 交易系统说明
- [Docker部署](DOCKER.md) - 容器化部署
- [数据流程](DATA_FLOW.md) - 数据结构说明

---

**提示**: Web监控页面是观察系统运行状态的最佳方式，建议始终开启！

