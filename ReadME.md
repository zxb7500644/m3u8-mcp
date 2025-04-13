# MCP M3U8 视频服务

这是一个基于Docker的MCP（Model Context Protocol）服务，通过SSE（Server-Sent Events）传输协议提供m3u8视频处理功能。该服务支持与n8n-nodes-mcp节点进行无缝集成，使您能够在n8n工作流中处理m3u8视频。

## 功能特点

- **支持SSE传输协议**：在端口3001上运行，符合MCP Protocol规范
- **API认证**：支持通过API密钥保护服务
- **环境变量配置**：通过环境变量管理敏感信息
- **数据持久化**：使用Docker卷保存数据

## 提供的工具

- **analyze_m3u8**: 分析m3u8文件，获取基本信息
- **download_m3u8_video**: 从m3u8链接下载视频，解密并合并为mp4文件
- **check_download_status**: 检查当前下载状态和临时文件夹信息
- **clean_temp_files**: 清理下载过程中产生的临时文件
- **list_prompts**: 列出所有可用的提示模板
- **get_prompt**: 获取指定的提示模板
- **list_resources**: 列出所有可用的资源
- **read_resource**: 读取指定的资源

## 部署指南

### 使用Docker部署

1. 进入docker目录：
```bash
cd docker
```

2. 配置环境变量：
```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

3. 构建并启动服务：

**Linux/Mac**：
```bash
./run.sh
```

**Windows**：
```powershell
./run.ps1
```

或手动启动：
```bash
docker-compose up -d
```

4. 访问服务：
```
http://localhost:3001
```

### 与n8n集成

1. 在n8n中添加MCP Client节点
2. 选择SSE连接方式
3. 设置SSE URL为`http://localhost:3001/sse`
4. 如果配置了API密钥，添加Header: `X-API-Key: <your-api-key>`
5. 选择操作（如Execute Tool）
6. 选择要执行的工具（如analyze_m3u8）
7. 设置参数并执行

## 目录结构

```
├── docker/                # Docker相关文件
│   ├── Dockerfile         # 构建Docker镜像的配置
│   ├── docker-compose.yml # Docker Compose配置
│   ├── requirements.txt   # Python依赖项
│   ├── .env.example       # 环境变量示例
│   ├── run.sh             # Linux/Mac启动脚本
│   ├── run.ps1            # Windows启动脚本
│   └── README.md          # Docker部署指南
├── mcp_server.py          # MCP服务源代码
├── data/                  # 数据持久化目录
└── README.md              # 项目说明文档
```

## 参考资料

- [n8n-nodes-mcp NPM包](https://www.npmjs.com/package/n8n-nodes-mcp)
- [Model Context Protocol文档](https://modelcontextprotocol.github.io/)
- [MCP SSE传输规范](https://github.com/modelcontextprotocol/protocol) 