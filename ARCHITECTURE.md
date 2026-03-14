# 📋 项目架构完整分析

## 🏗️ 项目概览

**项目名称：** To Watch/Read List  
**用途：** 个人链接收藏工具（整合 YouTube、普通网页）  
**部署平台：** Heroku + PostgreSQL  
**开发栈：** FastAPI + SQLAlchemy + Jinja2  

---

## 📐 架构设计

### 分层架构

```
┌─────────────────────────────────────────┐
│         Frontend (HTML/Jinja2)          │
│  - index.html      (主页面)             │
│  - login.html      (登录)               │
│  - register.html   (注册)               │
│  - forgot_password (找回密码)           │
│  - reset_password  (重置密码)           │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      API Layer (FastAPI Routes)         │
│  GET  /                                 │
│  GET  /login, /register                 │
│  POST /api/register, /api/login         │
│  POST /api/items/add                    │
│  GET  /api/items                        │
│  etc...                                 │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Business Logic (Services)            │
│  - auth.py        (会话/认证)           │
│  - scraper.py     (网页/YouTube 爬虫)   │
│  - email.py       (邮件发送)            │
│  - models.py      (数据模型)            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Data Layer (SQLAlchemy ORM)         │
│  - User           (用户表)              │
│  - Item           (链接表)              │
│  - PasswordReset  (密码重置令牌)        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Database (SQLite/PostgreSQL)         │
│  - 本地：SQLite                         │
│  - 生产：PostgreSQL (Heroku)            │
└─────────────────────────────────────────┘
```

### 代码模块详解

| 模块 | 职责 | 关键功能 |
|------|------|--------|
| **main.py** | 应用入口和路由 | FastAPI 实例、所有 URL 路由 |
| **auth.py** | 用户认证 | Session 生成/验证、密码加密、用户登录 |
| **models.py** | 数据模型 | SQLAlchemy ORM 定义（User、Item、PasswordReset） |
| **schemas.py** | API 数据格式 | Pydantic 验证模型（请求/响应） |
| **database.py** | 数据库连接 | 数据库 URL 配置、数据库初始化 |
| **services/scraper.py** | 网页爬虫 | YouTube API、网页元数据抓取、Mock 模式 |
| **services/email.py** | 邮件服务 | SendGrid 集成、本地开发邮件打印 |
| **config.py** | 配置管理 | 统一环境变量读取和验证 |

---

## 🔄 核心业务流程

### 1. 用户注册和认证

```
用户请求注册
    ↓
main.py: POST /api/register
    ↓
auth.py: create_user()
    ↓
models.User: 创建新用户记录
    ↓
database: SQLite/PostgreSQL 存储
    ↓
auth.py: create_session()
    ↓
响应: 自动登录 + Set-Cookie
```

**关键文件：**
- [app/main.py](app/main.py) - `/api/register` 路由
- [app/auth.py](app/auth.py) - `create_user()` 和 `hash_password()`
- [app/models.py](app/models.py) - User 表定义

---

### 2. 密码重置流程

```
用户输入邮箱
    ↓
main.py: POST /api/forgot-password
    ↓
auth.py: 生成重置令牌
    ↓
models.PasswordReset: 存储令牌（1小时过期）
    ↓
email.py: 发送邮件
    ├─ 生产（Heroku）: SendGrid API 发送
    └─ 开发（本地）: 打印到终端
    ↓
用户点击邮件中的链接
    ↓
main.py: GET /reset-password?token=...
    ↓
auth.py: verify_reset_token()
    ↓
用户设置新密码
    ↓
完成
```

**关键文件：**
- [app/main.py](app/main.py) - `/api/forgot-password` 和 `/reset-password` 路由
- [app/services/email.py](app/services/email.py) - 邮件发送逻辑
- [app/auth.py](app/auth.py) - 令牌验证

---

### 3. 添加链接和元数据抓取

```
用户输入 URL
    ↓
main.py: POST /api/items/add
    ↓
scraper.py: scrape_url(url)
    ├─ 是 YouTube？
    │  ├─ 有 API Key？
    │  │  ├─ 是: fetch_youtube_data_api()
    │  │  └─ 否: 
    │  │      └─ Mock 模式? → [Mock] 数据
    │  └─ 降级: fetch_youtube_metadata() (oEmbed)
    │
    └─ 普通网页？
       └─ extract_metadata() (网页抓取)
    ↓
models.Item: 保存链接 + 元数据
    ↓
响应: 项目信息
```

**关键文件：**
- [app/main.py](app/main.py) - POST `/api/items/add`
- [app/services/scraper.py](app/services/scraper.py) - 爬虫逻辑

**Mock 机制：**
```python
# 当无 YouTube API Key 且 USE_MOCK_EXTERNAL=true
return {
    "title": "[Mock] Sample YouTube Video Title",
    "description": "[Mock] This is a sample...",
    "source_type": "youtube"
}
```

---

## 🗄️ 数据库设计

### 用户表 (User)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 用户 ID |
| email | String | UNIQUE | 电子邮件 |
| hashed_password | String | NOT NULL | bcrypt 密码哈希 |
| created_at | DateTime | DEFAULT NOW | 创建时间 |
| items | Relationship | - | 关联的链接列表 |

### 链接表 (Item)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 链接 ID |
| user_id | Integer | FK | 所有者 ID |
| url | String | NOT NULL | 原始 URL |
| title | String | - | 自动抓取的标题 |
| description | String | - | 自动抓取的描述 |
| source_type | String | - | youtube/article/other |
| completed | Boolean | DEFAULT FALSE | 是否已看/读 |
| created_at | DateTime | DEFAULT NOW | 添加时间 |
| updated_at | DateTime | DEFAULT NOW | 更新时间 |

### 密码重置表 (PasswordReset)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | String | PK | UUID |
| user_id | Integer | FK | 用户 ID |
| token | String | UNIQUE | 签名令牌 |
| created_at | DateTime | DEFAULT NOW | 创建时间 |
| expires_at | DateTime | ~1小时后 | 过期时间 |

**关键文件：**
- [app/models.py](app/models.py) - 所有表定义
- [app/database.py](app/database.py) - 数据库连接管理

---

## 🔐 安全措施

### 1. 密码加密

```python
# auth.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)  # bcrypt 单向哈希

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)  # 验证匹配
```

### 2. Session 管理

```python
# auth.py - 使用签名令牌，防止伪造
serializer = URLSafeTimedSerializer(SECRET_KEY, salt="auth")

def create_session(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id, "timestamp": ...})

def verify_session(token: str) -> Optional[dict]:
    try:
        return serializer.loads(token, max_age=7_days)
    except (BadSignature, SignatureExpired):
        return None
```

### 3. CSRF 防护

```python
# 使用 HTTP-only Cookie 存储 Session
set_session_cookie(response, token)  # HttpOnly + Secure

# 前端通过 Cookie 自动传递，不需要手动处理
```

### 4. 密码重置令牌

```python
# 令牌自动过期（1 小时）
reset_token = create_reset_token(user)  # itsdangerous 签名
verify_reset_token(token)  # 过期检查
```

---

## 🌐 对外连接

### 依赖的第三方服务

| 服务 | 用途 | 本地开发 | 生产环境 |
|------|------|--------|--------|
| **YouTube Data API** | 获取视频信息 | Mock 数据 | 真实 API |
| **SendGrid** | 发送邮件 | 终端打印 | 真实邮件 |
| **PostgreSQL** | 数据存储 | SQLite | Heroku 托管 |
| **Heroku** | 部署 | N/A | 完整部署 |

---

## ⚙️ 配置管理

### 环境变量

```bash
# .env 文件
ENV=development                  # development/production
USE_MOCK_EXTERNAL=true          # 本地用 Mock API
SECRET_KEY=...                  # 会话和加密密钥
DATABASE_URL=sqlite:///app.db   # 本地：SQLite
YOUTUBE_API_KEY=                # 留空 → Mock
SENDGRID_API_KEY=               # 留空 → 打印
FROM_EMAIL=noreply@example.com  # 邮件发件人
ALLOWED_ORIGINS=localhost:8000  # CORS 白名单
```

**关键文件：** [app/config.py](app/config.py)

---

## 🚀 部署流程

### 本地开发（Mock 模式）

```bash
# 1. 准备环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. 配置 .env
USE_MOCK_EXTERNAL=true
YOUTUBE_API_KEY=  # 留空
SENDGRID_API_KEY=  # 留空

# 3. 运行
uvicorn app.main:app --reload

# 结果：完全可用，外部 API 返回 Mock 数据
```

### 生产环境（Heroku）

```bash
# 1. 部署代码
git push heroku main

# 2. 设置环境变量
heroku config:set ENV=production
heroku config:set YOUTUBE_API_KEY=real_key
heroku config:set SENDGRID_API_KEY=real_key

# 3. 数据库迁移
heroku run init_db

# 结果：PostgreSQL + 真实 API，完全生产就绪
```

**关键文件：**
- [Procfile](Procfile) - Heroku 进程配置
- [runtime.txt](runtime.txt) - Python 版本
- [requirements.txt](requirements.txt) - 依赖列表

---

## 🧪 测试方案

### 单元测试

```bash
# 需要创建 tests/ 目录
pytest tests/test_auth.py          # 认证测试
pytest tests/test_scraper.py       # 爬虫测试
pytest tests/test_models.py        # 模型测试
pytest --cov=app                   # 覆盖率报告
```

### 集成测试

```python
# 测试完整流程：注册 → 登录 → 密码重置 → 添加链接
def test_user_flow():
    # 1. 注册
    register_response = client.post("/api/register", ...)
    # 2. 登录
    login_response = client.post("/api/login", ...)
    # 3. 添加链接
    add_response = client.post("/api/items/add", ...)
```

---

## 📊 项目健康度检查清单

- ✅ 代码组织清晰（分层架构）
- ✅ 安全措施完善（密码加密、Session 管理）
- ✅ 数据库设计合理（3 个表，关系明确）
- ✅ 本地开发支持（Mock 模式）
- ✅ 文档齐全（README + TESTING + IMPROVEMENTS）
- ⚠️ 缺少自动化测试（pytest 框架已添加，需编写用例）
- ⚠️ 缺少数据库迁移工具（Alembic）
- ⚠️ 缺少日志系统
- ⚠️ 缺少错误监控（Sentry）

---

## 🎯 优化方向

### 短期（1-2 周）
1. 添加单元测试（pytest）
2. 添加日志系统（logging）
3. 添加输入验证加强
4. 编写 API 文档 (Swagger)

### 中期（1-2 月）
5. 添加数据库迁移工具 (Alembic)
6. 配置 CI/CD (GitHub Actions)
7. 添加缓存 (Redis)
8. 性能监控

### 长期（3+ 月）
9. 容器化 (Docker)
10. 多用户支持优化
11. 前端框架升级 (React/Vue)
12. 移动端适配

---

**最后审核：2026-03-14**  
**项目版本：2.0.0（本地开发版）**
