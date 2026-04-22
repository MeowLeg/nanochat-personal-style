#!/bin/bash
# 完整安装脚本 - Apple Silicon + MLX

echo "🚀 NanoChat 风格改写系统 - MLX 版本安装"
echo ""

# 1. 创建 conda 环境
echo "📦 创建 Python 3.11 conda 环境..."
conda create -n nanochat python=3.11 -y
if [ $? -ne 0 ]; then
    echo "❌ 创建环境失败"
    exit 1
fi

# 2. 激活环境
echo "✅ 环境创建成功"
echo ""
echo "🔧 现在执行以下命令完成安装："
echo ""
echo "   conda activate nanochat"
echo "   cd backend"
echo "   pip install -r requirements-apple.txt"
echo "   python -m app.main"
echo ""
echo "或者运行 ./install-complete.sh 继续"