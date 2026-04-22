#!/bin/bash

# 使用 conda nanochat 环境启动后端
echo "Activating nanochat conda environment..."
cd /Users/jinhao/Documents/GitHub/nanochat-personal-style/backend

echo "Starting backend with nanochat environment..."
conda run -n nanochat python -m app.main
