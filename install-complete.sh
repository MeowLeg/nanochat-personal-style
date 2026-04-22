#!/bin/bash
# 继续安装 - 在 conda 环境中运行

echo "📦 安装 MLX 版本依赖..."
cd backend

# 更新 pip
pip install --upgrade pip

# 安装 requirements-apple.txt
pip install -r requirements-apple.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 安装完成！"
    echo ""
    echo "🚀 现在启动后端："
    echo "   python -m app.main"
    echo ""
    echo "📱 然后在新终端启动前端："
    echo "   cd frontend"
    echo "   npm install"
    echo "   npm run dev"
else
    echo "❌ 安装失败"
    exit 1
fi