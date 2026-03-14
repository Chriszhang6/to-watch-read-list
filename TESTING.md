# 🧪 本地开发和测试指南

## 问题：为什么某些功能只在 Heroku 上有？

你的应用依赖外部服务：
- **YouTube API** - 需要 API Key 获取视频信息
- **SendGrid 邮件** - 需要 API Key 发送密码重置邮件
- **PostgreSQL** - Heroku 提供，本地用 SQLite

**解决方案：使用 Mock 模式本地完全模拟这些服务！**

---

## 🚀 快速开始

### 1. 配置本地环境

```bash
# 进入项目目录
cd /Users/yangzhang/Downloads/to_watch_read_list

# 创建 .env 文件（从模板复制）
cp .env.example .env

# 确保 .env 包含：
# ENV=development
# USE_MOCK_EXTERNAL=true  # 启用 Mock 模式
# SECRET_KEY=你的随机密钥
# DATABASE_URL=sqlite:///./app.db
```

### 2. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装包
pip install -r requirements.txt
```

### 3. 启动本地服务器

```bash
# 方式 1：直接运行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式 2：使用 Python
python -m uvicorn app.main:app --reload
```

访问：http://localhost:8000

---

## 📋 完整测试清单

### ✅ 用户认证流程

#### 注册 (Register)
```bash
# 进入 http://localhost:8000/login
# 点击 "Register" 或访问 http://localhost:8000/register

# 测试数据：
- Email: test@example.com
- Password: SecurePass123!

# 预期结果：
✓ 用户创建成功
✓ 自动登录跳转到首页
```

#### 密码重置 (Password Reset)
```bash
# 1. 访问 http://localhost:8000/forgot-password
# 2. 输入注册邮箱
# 3. 查看终端输出（本地模式不发邮件）

# 预期结果（在终端看到）：
================================================================================
🔐 PASSWORD RESET EMAIL (Development Mode - Not Sent)
================================================================================
To: test@example.com
Reset Link: http://localhost:8000/reset-password?token=...
Token expires in: 1 hour
================================================================================

# 4. 复制 reset link 在浏览器中打开
# 5. 输入新密码
# 6. 用新密码登录
```

### ✅ 添加链接功能

#### YouTube 视频
```bash
# 添加 YouTube 链接
https://www.youtube.com/watch?v=dQw4w9WgXcQ

# 预期结果：
✓ 标题自动填充：[Mock] Sample YouTube Video Title
✓ 描述自动填充：[Mock] This is a sample video description...
✓ 显示 "[MOCK]" 前缀表示本地模拟
```

#### 普通网页
```bash
# 添加任何网页 URL
https://www.python.org

# 预期结果：
✓ 标题从网页 og:title/meta title 提取
✓ 描述从 og:description/meta description 提取
✓ 实际从网页抓取元数据（不需要 API Key）
```

### ✅ 数据库功能

#### SQLite（本地）
```bash
# app.db 自动创建在项目根目录
ls -la app.db

# 查看数据库内容（需要 sqlite3）：
sqlite3 app.db ".tables"
sqlite3 app.db "SELECT * FROM user;"
```

#### 切换到 PostgreSQL（可选）
```bash
# 1. 安装 PostgreSQL
brew install postgresql  # macOS
# 或 apt install postgresql  # Linux

# 2. 创建本地数据库
createdb watchlist_dev

# 3. 更新 .env
DATABASE_URL=postgresql://localhost/watchlist_dev

# 4. 重启服务器
# SQLAlchemy 会自动迁移表结构
```

---

## 🔧 配置详解

### .env 文件参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `ENV` | `development` | 开发模式 |
| `USE_MOCK_EXTERNAL` | `true` | 使用 Mock API（不发真实请求） |
| `SECRET_KEY` | 任意字符串 | 会话和密码加密密钥 |
| `DATABASE_URL` | `sqlite:///./app.db` | SQLite 本地数据库 |
| `YOUTUBE_API_KEY` | 留空 | 留空时本地用 Mock 数据 |
| `SENDGRID_API_KEY` | 留空 | 留空时本地打印重置链接 |

### 生成 SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 输出示例：
# esDVk5XpnZ8L9mK2jQ3rT4uV5wX6yZ7aBcDeF_ghI

# 复制到 .env 中的 SECRET_KEY
```

---

## 🎯 不同场景下的配置

### 场景 1：完全本地测试（推荐）
```bash
ENV=development
USE_MOCK_EXTERNAL=true
YOUTUBE_API_KEY=  # 留空，用 Mock
SENDGRID_API_KEY=  # 留空，打印到终端
DATABASE_URL=sqlite:///./app.db
```

### 场景 2：测试真实 YouTube API
```bash
# 获取 API Key：https://console.cloud.google.com
ENV=development
USE_MOCK_EXTERNAL=false
YOUTUBE_API_KEY=YOUR_ACTUAL_KEY
SENDGRID_API_KEY=  # 保持留空
DATABASE_URL=sqlite:///./app.db
```

### 场景 3：测试邮件功能
```bash
# 获取 SendGrid 免费账户：https://sendgrid.com
ENV=development
SENDGRID_API_KEY=SG.xxxxx...
FROM_EMAIL=noreply@yourdomain.com
DATABASE_URL=sqlite:///./app.db
```

### 场景 4：预部署到 Heroku
```bash
ENV=production
USE_MOCK_EXTERNAL=false
YOUTUBE_API_KEY=YOUR_ACTUAL_KEY
SENDGRID_API_KEY=SG.xxxxx...
DATABASE_URL=postgresql://...  # Heroku 自动设置
```

---

## 🐛 常见问题排查

### ❌ "Secret key not configured"
```bash
# 解决：检查 .env 中 SECRET_KEY 是否存在
cat .env | grep SECRET_KEY

# 如果缺失，生成一个：
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
```

### ❌ "Module not found: sendgrid"
```bash
# 解决：重新安装依赖
pip install --upgrade -r requirements.txt
```

### ❌ 密码重置邮件没有发送
```bash
# 这是正确的！本地模式不发邮件，而是打印到终端：
# 查看终端输出找到重置链接

# 如果什么都没看到，检查：
echo $SENDGRID_API_KEY  # 应该是空的
cat .env | grep "SENDGRID"  # 应该为空
```

### ❌ YouTube 视频信息显示 [Mock]
```bash
# 这也是正确的！本地模式使用模拟数据
# 要用真实数据，需要配置 YOUTUBE_API_KEY

# Heroku 上自动使用真实 API（你在部署时设置的键）
```

### ❌ 连不上 http://localhost:8000
```bash
# 检查服务器是否运行
# 终端应该显示：
# Uvicorn running on http://0.0.0.0:8000

# 如果没有，确认：
1. Python 版本 >= 3.8
2. requirements.txt 全部安装
3. 没有其他服务占用 8000 端口
```

---

## 📊 本地 vs Heroku 行为对比

| 功能 | 本地开发 | Heroku |
|------|--------|--------|
| 数据库 | SQLite（app.db） | PostgreSQL |
| YouTube 元数据 | Mock 数据 | 真实 API |
| 密码重置邮件 | 打印到终端 | SendGrid 发送 |
| 日志 | 终端输出 | Heroku 日志 |
| CORS | 仅允许 localhost | 部署后自动更新 |

---

## ✨ 自动化测试（可选）

项目已添加 `pytest` 和 `pytest-asyncio`。

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_auth.py

# 查看覆盖率
pytest --cov=app
```

---

## 🚀 部署到 Heroku

### 前置要求
```bash
# 安装 Heroku CLI
brew install heroku

# 登录
heroku login
```

### 部署步骤
```bash
# 1. 创建 Heroku 应用
heroku create your-app-name

# 2. 设置环境变量
heroku config:set ENV=production
heroku config:set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
heroku config:set YOUTUBE_API_KEY=your_key_here
heroku config:set SENDGRID_API_KEY=your_key_here

# 3. 添加 PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# 4. 推送代码
git push heroku main

# 5. 查看日志
heroku logs --tail
```

---

## 📚 相关链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [SendGrid 文档](https://docs.sendgrid.com/)
- [Heroku PostgreSQL](https://devcenter.heroku.com/articles/heroku-postgresql)

---

**最后更新：2026-03-14**
