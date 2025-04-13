#!/usr/bin/env pwsh

# 切换到项目根目录
Set-Location -Path ..

# 构建Docker镜像
docker build -t zxb7501262/m3u8-mcp-server -f docker/Dockerfile .

Write-Host "Docker镜像构建完成: zxb7501262/m3u8-mcp-server" -ForegroundColor Green 