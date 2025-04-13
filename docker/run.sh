#!/bin/bash

# 确保目录结构正确
mkdir -p ../data

# 检查.env文件，如果不存在，从.env.example复制
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "找不到.env文件，从.env.example创建..."
        cp .env.example .env
        echo "请编辑.env文件配置您的环境变量"
    else
        echo "警告：找不到.env.example文件，将使用默认配置"
    fi
fi

# 启动服务
echo "构建并启动MCP服务..."
docker-compose up -d

# 检查服务是否成功启动
echo "正在检查服务状态..."
sleep 3
docker-compose ps

echo "MCP服务已启动，访问 http://localhost:3001 查看服务信息"
echo "使用n8n-nodes-mcp通过SSE连接：http://localhost:3001/sse" 