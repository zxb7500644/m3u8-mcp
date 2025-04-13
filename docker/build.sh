#!/bin/bash

# 切换到项目根目录
cd ..

# 构建Docker镜像
docker build -t zxb7501262/m3u8-mcp-server -f docker/Dockerfile .

echo "Docker镜像构建完成: zxb7501262/m3u8-mcp-server" 