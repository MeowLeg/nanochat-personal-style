#!/bin/bash
# 快速启动脚本

USE_CONDA=false
if [ "$1" = "--conda" ] || [ "$1" = "-c" ]; then
    USE_CONDA=true
fi

echo "🚀 启动 NanoChat 风格改写系统"
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

# 检查后端目录
if [ ! -d "backend" ]; then
    echo "❌ 错误: 未找到 backend 目录"
    exit 1
fi

# 检查前端目录
if [ ! -d "frontend" ]; then
    echo "❌ 错误: 未找到 frontend 目录"
    exit 1
fi

echo "📦 检查后端依赖..."
cd backend

if [ "$USE_CONDA" = true ]; then
    echo "使用 conda nanochat 环境..."
    if ! conda info --envs | grep -q "nanochat"; then
        echo "❌ 错误: 未找到 conda nanochat 环境"
        exit 1
    fi
else
    echo "使用 venv 虚拟环境..."
    if [ ! -d "venv" ]; then
        echo "创建虚拟环境..."
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -q -r requirements.txt
fi

echo ""
echo "✅ 后端准备完成"
echo "启动后端服务 (端口 8000)..."

if [ "$USE_CONDA" = true ]; then
    conda run -n nanochat python -m app.main &
else
    python -m app.main &
fi
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

echo ""
echo "📦 检查前端依赖..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "安装 npm 依赖..."
    npm install
fi

echo ""
echo "✅ 前端准备完成"
echo "启动前端服务 (端口 3000)..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✨ 系统启动完成！"
echo "   前端: http://localhost:3000"
echo "   后端: http://localhost:8000"
echo "   API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获 Ctrl+C 清理进程
trap "echo '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

wait