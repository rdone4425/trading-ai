# 📊 Web监控页面

Trading AI 提供了一个美观的Web监控页面，可以实时查看交易数据、分析结果和统计信息。

## 🌟 功能特性

### 1. **实时统计卡片** 📊
- 📈 总交易次数
- 🎯 胜率（含胜负次数）
- 💹 盈亏比（平均盈利/平均亏损）
- 💰 净利润和ROI
- 📉 最大回撤
- 🎲 夏普比率

### 2. **可视化图表** 📈
- **收益曲线图** - 每日盈亏和累计收益
- **胜率趋势图** - 每日胜率变化
- **交易对表现** - 各币种盈亏排行
- **交易分布** - 做多/做空/观望比例

### 3. **分析结果展示** 🔍
- 查看最近的AI分析结果
- 显示交易对、方向、入场价、止损、止盈
- 展示信心度和分析理由
- 实时筛选和搜索
- 按信心度/时间排序

### 4. **交易记录查看** 💼
- 历史交易记录
- 盈亏情况
- 入场和出场价格
- 持仓时长
- 交易标签

### 5. **多时间周期统计** ⏰
- 7天统计
- 30天统计
- 自定义周期
- 对比视图

### 6. **智能搜索过滤** 🔎
- 按交易对搜索
- 按方向筛选
- 按日期范围
- 按盈亏状态

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

### 主仪表板（概览）
- **顶部**: 6个统计卡片
  - 总交易次数
  - 胜率（动态颜色）
  - 盈亏比
  - 净利润（带涨跌标识）
  - 最大回撤
  - 夏普比率
- **中部**: 4个可视化图表
  - 收益曲线（折线图）
  - 胜率趋势（柱状图）
  - 交易对表现（排行榜）
  - 操作分布（饼图）
- **底部**: 最后更新时间

### 分析结果标签页
**功能增强**：
- 🔍 实时搜索框（按交易对搜索）
- 🎯 筛选器（做多/做空/观望）
- 📊 信心度排序
- ⏰ 时间排序

**每条记录显示**：
- 交易对（高亮显示）
- 操作方向（彩色标签）
- 入场/止损/止盈价格
- 信心度（进度条）
- 分析理由（折叠显示）
- 详细时间戳

### 交易记录标签页
**功能增强**：
- 📅 日期范围选择
- 💰 盈亏筛选（盈利/亏损）
- 📊 按收益排序
- 📈 统计汇总

**每条记录显示**：
- 交易对
- 盈亏金额（带颜色）
- 盈亏百分比
- 入场/出场价格
- 杠杆倍数
- 持仓时长
- 交易时间

### 统计标签页
**多周期对比**：
- 7天 vs 30天
- 月度对比
- 季度对比

**详细指标**：
- 总交易次数
- 胜率（带趋势）
- 盈亏比
- 净利润
- 平均盈利/亏损
- 最大单笔盈利/亏损
- 平均持仓时长
- 交易频率

### 图表标签页
**4个专业图表**：
1. **收益曲线** - 每日盈亏 + 累计收益
2. **胜率趋势** - 每日胜率变化
3. **交易对排行** - Top 10 表现
4. **时间分布** - 各时段交易频率

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

页面使用：
- **ECharts** - 专业图表库
- **响应式设计** - 自适应各种屏幕
- **纯HTML/CSS/JS** - 无需编译，直接修改即可

### Q: 图表不显示怎么办？
A: 检查：
1. 是否有交易数据（`data/trades.json`）
2. 浏览器控制台是否有错误
3. ECharts CDN是否加载成功
4. 尝试刷新页面

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

