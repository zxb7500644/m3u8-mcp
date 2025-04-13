# MCP服务 Docker部署指南

本指南将帮助您通过Docker容器部署MCP服务。该服务支持SSE传输协议，并在端口3001上运行。

## 先决条件

- Docker Engine
- Docker Compose

## 部署步骤

1. 确保已安装Docker和Docker Compose
2. 进入docker目录：`cd docker`
3. 构建并启动容器：`docker-compose up -d`
4. 访问服务：`http://localhost:3001`

## 环境变量配置

您可以通过环境变量配置服务的行为：

```bash
# Linux/Mac
export API_KEY=your-api-key
docker-compose up -d

# Windows (PowerShell)
$env:API_KEY="your-api-key"
docker-compose up -d
```

或者创建`.env`文件在docker目录中：

```
API_KEY=your-api-key
```

## 与n8n集成

1. 在n8n中添加MCP Client节点
2. 选择SSE连接方式
3. 设置SSE URL为`http://localhost:3001/sse`
4. 如果配置了API密钥，添加Header: `X-API-Key: <your-api-key>`
5. 选择操作（如Execute Tool）
6. 选择要执行的工具
7. 设置参数并执行

## 可用工具

- `analyze_m3u8`: 分析m3u8文件，获取基本信息
- `download_m3u8_video`: 从m3u8链接下载视频，解密并合并为mp4文件
- `check_download_status`: 检查当前下载状态和临时文件夹信息
- `clean_temp_files`: 清理下载过程中产生的临时文件
- `list_prompts`: 列出所有可用的提示模板
- `get_prompt`: 获取指定的提示模板
- `list_resources`: 列出所有可用的资源
- `read_resource`: 读取指定的资源

## 数据持久化

服务使用Docker卷将数据持久化存储在主机上：

- 数据文件保存在：`./data`目录

## 故障排除

- 如果服务无法启动，检查日志：`docker-compose logs`
- 如果无法连接，确保端口3001未被占用：`docker-compose ps`
- 如需重新启动服务：`docker-compose restart` 