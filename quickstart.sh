#!/bin/bash
# 🚀 快速开始脚本

set -e  # 遇到错误就停止

echo "🎯 Watchlist 项目 - 快速开始"
echo "=================================="
echo ""

# 1. 创建 .env
if [ ! -f .env ]; then
    echo "📝 创建 .env 文件..."
    cp .env.example .env
    echo "✅ .env 已创建，请检查配置"
else
    echo "✅ .env 已存在"
fi

# 2. 创建虚拟环境
if [ ! -d venv ]; then
    echo ""
    echo "🐍 创建虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境已创建"
fi

# 3. 激活虚拟环境
echo ""
echo "🔌 激活虚拟环境..."
source venv/bin/activate

# 4. 安装依赖
echo ""
echo "📦 安装依赖..."
pip install --upgrade -r requirements.txt
echo "✅ 依赖已安装"

# 5. 提示用户配置
echo ""
echo "=================================="
echo "✨ 设置完成！"
echo "=================================="
echo ""
echo "📋 下一步（选择一个）："
echo ""
echo "1️⃣  启动开发服务器："
echo "   uvicorn app.main:app --reload"
echo ""
echo "2️⃣  查看完整测试指南："
echo "   cat TESTING.md"
echo ""
echo "3️⃣  首次运行，请先配置 SECRET_KEY："
echo "   python3 -c \"import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))\" >> .env"
echo ""
echo "=================================="
echo "🌐 本地服务器地址："
echo "   http://localhost:8000"
echo "=================================="
