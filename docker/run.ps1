# 确保目录结构正确
if (!(Test-Path -Path "../data")) {
    New-Item -ItemType Directory -Path "../data" -Force
}

# 检查.env文件，如果不存在，从.env.example复制
if (!(Test-Path -Path ".env")) {
    if (Test-Path -Path ".env.example") {
        Write-Host "找不到.env文件，从.env.example创建..."
        Copy-Item ".env.example" ".env"
        Write-Host "请编辑.env文件配置您的环境变量"
    } else {
        Write-Host "警告：找不到.env.example文件，将使用默认配置"
    }
}

# 启动服务
Write-Host "构建并启动MCP服务..."
docker-compose up -d

# 检查服务是否成功启动
Write-Host "正在检查服务状态..."
Start-Sleep -Seconds 3
docker-compose ps

Write-Host "MCP服务已启动，访问 http://localhost:3001 查看服务信息"
Write-Host "使用n8n-nodes-mcp通过SSE连接：http://localhost:3001/sse" 