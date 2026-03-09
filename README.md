# 待看/读清单 (To Watch/Read List)

一个简洁的个人工具，用于保存想要稍后观看/阅读的链接。自动获取 YouTube 视频信息或网页元数据。

## 功能特性

- 添加链接自动获取标题和描述
- YouTube 视频支持：通过 YouTube Data API 获取完整视频简介
- 普通网页：抓取页面 meta 信息
- 按日期分组展示
- 筛选：待看 / 已完成 / 全部
- 简单密码认证
- 响应式界面设计

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI | 现代、快速、自带 API 文档 |
| 数据库 | PostgreSQL / SQLite | 生产用 PostgreSQL，本地开发用 SQLite |
| ORM | SQLAlchemy | Python 成熟的 ORM |
| 前端 | Tailwind CSS + Alpine.js | 轻量级，无需构建工具 |
| 认证 | Cookie Session | 基于 itsdangerous 的安全签名 |
| 部署 | Heroku | 支持 PostgreSQL 和环境变量配置 |

## 项目结构

```
to-watch-read-list/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口和路由
│   ├── models.py            # SQLAlchemy 数据模型
│   ├── schemas.py           # Pydantic 请求/响应模型
│   ├── database.py          # 数据库连接配置
│   ├── auth.py              # 认证逻辑
│   ├── services/
│   │   ├── __init__.py
│   │   └── scraper.py       # 网页抓取和 YouTube API
│   └── templates/
│       ├── index.html       # 主页面
│       └── login.html       # 登录页面
├── requirements.txt         # Python 依赖
├── Procfile                 # Heroku 进程配置
├── runtime.txt              # Python 版本
├── .env.example             # 环境变量示例
└── README.md
```

## 核心实现

### 1. 数据模型

```python
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    title = Column(String)
    summary = Column(Text)           # 描述/简介
    source_type = Column(String)     # youtube / article / other
    captured_at = Column(DateTime)   # 捕获时间
    completed = Column(Boolean)      # 是否已完成
    completed_at = Column(DateTime)  # 完成时间
```

### 2. 链接抓取策略

**YouTube 视频：**
1. 优先使用 YouTube Data API v3 获取视频标题和完整描述
2. 降级使用 oEmbed API 获取标题（无描述）
3. 最后尝试 HTML 抓取

**普通网页：**
1. 抓取页面 HTML
2. 提取 og:title / og:description 等 meta 信息
3. 降级使用 title 标签和 meta description

### 3. 认证机制

- 密码存储在环境变量 `APP_PASSWORD`
- 登录成功后生成签名 Cookie（使用 itsdangerous）
- Cookie 有效期 7 天
- 所有 API 路由都需要验证 Cookie

### 4. 前端交互

使用 Alpine.js 实现前端交互：
- 添加链接（异步提交）
- 切换完成状态
- 删除条目
- 筛选列表（待看/已完成/全部）
- 按日期分组显示

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/login` | 登录 |
| POST | `/api/logout` | 登出 |
| POST | `/api/items` | 添加新条目 |
| GET | `/api/items` | 获取列表（支持 status 筛选） |
| PATCH | `/api/items/{id}` | 更新条目（标记完成） |
| DELETE | `/api/items/{id}` | 删除条目 |

## 本地开发

1. 克隆项目
```bash
git clone <your-repo-url>
cd to-watch-read-list
```

2. 创建虚拟环境并安装依赖
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 填入实际值
```

4. 启动开发服务器
```bash
uvicorn app.main:app --reload
```

5. 访问 http://localhost:8000

## 环境变量

| 变量名 | 必需 | 说明 |
|--------|------|------|
| `YOUTUBE_API_KEY` | 是 | YouTube Data API v3 密钥 |
| `APP_PASSWORD` | 是 | 应用登录密码 |
| `SECRET_KEY` | 是 | Cookie 签名密钥（随机字符串） |
| `DATABASE_URL` | 否 | 数据库连接（Heroku 自动提供） |

## 获取 YouTube API Key

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 **YouTube Data API v3**
4. 创建 **API Key** 凭据
5. 将 API Key 配置到环境变量

**注意**：YouTube Data API 每天有 10,000 单位免费配额，获取单个视频信息消耗约 1 单位，个人使用足够。

## 部署到 Heroku

1. 创建 Heroku 应用
```bash
heroku create your-app-name
```

2. 添加 PostgreSQL
```bash
heroku addons:create heroku-postgresql:essential-0
```

3. 设置环境变量
```bash
heroku config:set YOUTUBE_API_KEY=your_api_key
heroku config:set APP_PASSWORD=your_password
heroku config:set SECRET_KEY=$(openssl rand -hex 32)
```

4. 部署
```bash
git push heroku main
```

5. 打开应用
```bash
heroku open
```

## 后续更新

修改代码后重新部署：
```bash
git add .
git commit -m "Your commit message"
git push heroku main
```

## License

MIT
