# MCP M3U8 视频服务

这是一个基于MCP（Model Context Protocol）的m3u8视频处理服务，支持下载、解密和合并m3u8视频。该服务通过SSE（Server-Sent Events）传输协议提供接口，可与n8n工作流等工具无缝集成。

## 功能特点

- **支持SSE传输协议**：在端口3001上运行，符合MCP Protocol规范
- **API认证**：支持通过API密钥保护服务
- **环境变量配置**：通过环境变量管理服务配置
- **数据持久化**：使用目录映射保存下载的视频数据
- **并行下载**：支持多进程并行下载ts文件片段，提高下载速度
- **解密支持**：支持AES-128-CBC加密的m3u8视频解密

## 提供的工具

- **analyze_m3u8**: 分析m3u8文件，获取基本信息
- **download_m3u8_video**: 从m3u8链接下载视频，解密并合并为mp4文件
- **check_download_status**: 检查当前下载状态和临时文件夹信息
- **clean_temp_files**: 清理下载过程中产生的临时文件
- **list_prompts**: 列出所有可用的提示模板
- **get_prompt**: 获取指定的提示模板
- **list_resources**: 列出所有可用的资源
- **read_resource**: 读取指定的资源

## 运行方式

### 直接运行（需要Python 3.10+）

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行服务：
```bash
python mcp_server.py
```

### 使用Docker部署

#### 使用项目中的构建脚本

1. 进入docker目录：
```bash
cd docker
```

2. 构建Docker镜像：

**Linux/Mac**：
```bash
./build.sh
```

**Windows**：
```powershell
.\build.ps1
```

3. 启动服务：

**Linux/Mac**：
```bash
./run.sh
```

**Windows**：
```powershell
.\run.ps1
```

#### 手动构建和启动

1. 在项目根目录构建镜像：
```bash
docker build -t mcp-m3u8-server -f docker/Dockerfile .
```

2. 运行容器：
```bash
docker run -d -p 3001:3001 -e API_KEY=your-secret-key -v ./data:/app/data --name mcp-server mcp-m3u8-server
```

### 配置API密钥（可选）

设置环境变量`API_KEY`以启用API密钥验证：

```bash
# Linux/Mac
export API_KEY=your-secret-key
python mcp_server.py

# Windows (PowerShell)
$env:API_KEY="your-secret-key"
python mcp_server.py
```

## 使用方式

### 1. 访问服务信息

```
http://localhost:3001
```

### 2. 与n8n集成

1. 在n8n中添加MCP Client节点
2. 选择SSE连接方式
3. 设置SSE URL为`http://localhost:3001/sse`
4. 如果配置了API密钥，添加Header: `X-API-Key: <your-api-key>`
5. 选择操作（如Execute Tool）
6. 选择要执行的工具（如analyze_m3u8）
7. 设置参数并执行

### 3. 分析m3u8视频

使用`analyze_m3u8`工具分析m3u8链接，获取加密方式、ts文件数量等基本信息。

### 4. 下载m3u8视频

使用`download_m3u8_video`工具下载视频，参数说明：
- m3u8_url: m3u8文件的URL地址
- output_path: 输出mp4文件的保存路径，如`/app/data/video.mp4`
- processes: 并行下载的进程数，默认为4
- max_retries: 失败片段的最大重试次数，默认为3

### 5. 查看下载状态

使用`check_download_status`工具查看当前下载任务状态。

### 6. 清理临时文件

使用`clean_temp_files`工具清理下载过程中产生的临时文件。

## 目录结构

```
├── docker/                # Docker相关文件
│   ├── Dockerfile         # 构建Docker镜像的配置
│   ├── docker-compose.yml # Docker Compose配置
│   ├── .env.example       # 环境变量示例
│   ├── build.sh           # Linux/Mac构建脚本
│   ├── build.ps1          # Windows构建脚本
│   ├── run.sh             # Linux/Mac启动脚本
│   ├── run.ps1            # Windows启动脚本
│   └── README.md          # Docker部署指南
├── mcp_server.py          # MCP服务源代码
├── requirements.txt       # Python依赖项
├── ts_files/              # ts文件临时存储目录
├── data/                  # 下载视频保存目录
└── README.md              # 项目说明文档
```

## 注意事项

1. 确保有足够的磁盘空间用于下载和处理视频
2. 默认情况下，下载的视频将保存在`data/`目录
3. 临时ts文件将保存在`ts_files/`目录，处理完成后会自动清理
4. 如需更改数据保存位置，可通过环境变量`DATA_DIR`指定

## 参考资料

- [n8n-nodes-mcp NPM包](https://www.npmjs.com/package/n8n-nodes-mcp)
- [Model Context Protocol文档](https://modelcontextprotocol.github.io/)
- [MCP SSE传输规范](https://github.com/modelcontextprotocol/protocol) 