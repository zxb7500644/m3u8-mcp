# MCP M3U8 视频服务 Docker部署指南

本指南将帮助您通过Docker容器部署MCP M3U8视频服务。该服务支持下载、解密和合并m3u8视频，并通过SSE传输协议提供接口。

## 先决条件

- Docker Engine (20.10+)
- Docker Compose (可选，用于使用docker-compose.yml)

## 部署步骤

### 1. 使用提供的构建脚本

我们提供了简便的构建和运行脚本：

#### Linux/Mac用户

构建镜像：
```bash
./build.sh
```

运行服务：
```bash
./run.sh
```

#### Windows用户

构建镜像：
```powershell
.\build.ps1
```

运行服务：
```powershell
.\run.ps1
```

### 2. 手动构建和启动

#### 使用Docker命令

1. 在项目根目录构建镜像：
```bash
cd ..
docker build -t mcp-m3u8-server -f docker/Dockerfile .
```

2. 运行容器：
```bash
docker run -d -p 3001:3001 -v ./data:/app/data --name mcp-server mcp-m3u8-server
```

#### 使用Docker Compose

1. 编辑环境变量（可选）：
```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

2. 启动服务：
```bash
docker-compose up -d
```

## 环境变量配置

您可以通过以下环境变量配置服务：

| 变量名 | 说明 | 默认值 |
|-------|------|-------|
| API_KEY | API密钥，用于认证 | 无 (不启用认证) |
| PORT | 服务端口 | 3001 |
| HOST | 监听地址 | 0.0.0.0 |
| DATA_DIR | 数据存储目录 | /app/data |

配置方式：

```bash
# Linux/Mac
export API_KEY=your-secret-key
docker-compose up -d

# Windows (PowerShell)
$env:API_KEY="your-secret-key"
docker-compose up -d
```

或者在`.env`文件中设置：

```
API_KEY=your-secret-key
PORT=3001
```

## 数据持久化

服务使用Docker卷将数据持久化存储：

- 下载的视频保存在主机的`./data`目录（映射到容器的`/app/data`）
- ts文件临时存储在容器内的`/app/ts_files`目录

如需更改数据保存位置，可以在运行容器时修改卷映射：

```bash
docker run -d -p 3001:3001 -v /your/custom/path:/app/data --name mcp-server mcp-m3u8-server
```

## 与n8n集成

1. 在n8n中添加MCP Client节点
2. 选择SSE连接方式
3. 设置SSE URL为`http://localhost:3001/sse`
4. 如果配置了API密钥，添加Header: `X-API-Key: <your-api-key>`
5. 选择操作（如Execute Tool）
6. 选择要执行的工具（如analyze_m3u8）
7. 设置参数并执行

## 可用工具

- **analyze_m3u8**: 分析m3u8文件，获取基本信息
- **download_m3u8_video**: 从m3u8链接下载视频，解密并合并为mp4文件
- **check_download_status**: 检查当前下载状态和临时文件夹信息
- **clean_temp_files**: 清理下载过程中产生的临时文件
- **list_prompts**: 列出所有可用的提示模板
- **get_prompt**: 获取指定的提示模板
- **list_resources**: 列出所有可用的资源
- **read_resource**: 读取指定的资源

## 故障排除

- **服务无法启动**:
  - 检查日志：`docker logs mcp-server`
  - 确保端口3001未被占用：`netstat -ano | findstr 3001`

- **无法连接到服务**:
  - 确认容器正在运行：`docker ps`
  - 检查防火墙设置是否允许端口3001

- **下载视频失败**:
  - 检查m3u8链接是否有效
  - 确保有足够的磁盘空间
  - 查看下载状态：使用`check_download_status`工具

- **无法清理临时文件**:
  - 重启容器：`docker restart mcp-server`

## 重启和更新

重启服务：
```bash
docker restart mcp-server
```

更新到最新版本：
```bash
# 拉取最新代码
git pull

# 重新构建镜像
cd docker
./build.sh  # 或 .\build.ps1 (Windows)

# 停止并删除旧容器
docker stop mcp-server
docker rm mcp-server

# 启动新容器
./run.sh  # 或 .\run.ps1 (Windows)
``` 