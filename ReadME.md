# MCP M3U8 视频下载服务器

这是一个基于Model Context Protocol (MCP)的服务器，用于下载、解密和合并m3u8视频。该服务器能够接收m3u8地址和本地存储路径，自动下载解析m3u8文件中的ts片段，解密并合并成mp4文件，最终保存至指定路径。

## 功能特点

- 解析m3u8文件，支持加密和非加密的视频流
- 支持带有auth_key参数的视频片段URL
- 使用多进程并行下载ts文件片段，提高下载速度
- 支持AES-128解密
- 将所有ts文件按顺序合并为mp4文件
- 失败片段自动重试机制
- 提供下载状态检查和临时文件清理功能

## 系统要求

- Python 3.8+
- 依赖包：mcp, pycryptodome, requests, tqdm
- Docker (可选，用于容器化部署)

## 安装与部署

### 本地安装

1. 克隆或下载本项目
2. 安装依赖包：

```bash
pip install -r requirements.txt
```

### Docker部署

1. 构建并启动容器：

```bash
# 使用docker-compose
docker-compose up -d

# 或直接使用docker
docker build -t yourusername/mcp-m3u8-server .
docker run -d --rm -i yourusername/mcp-m3u8-server
```

## 使用方法

### 在VS Code中配置

在VS Code的`settings.json`中添加：

```json
{
  "mcp": {
    "inputs": [],
    "servers": {
      "mcp-m3u8-server": {
        "command": "docker",
        "args": [
          "run",
          "--rm",
          "-i",
          "yourusername/mcp-m3u8-server"
        ]
      }
    }
  }
}
```

### 在Claude Desktop中配置

在Claude Desktop的`claude_desktop_config.json`中添加：

```json
{
  "mcpServers": {
    "mcp-m3u8-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "yourusername/mcp-m3u8-server"
      ]
    }
  }
}
```

如果需要访问本地文件系统，可以添加卷挂载：

```json
{
  "mcpServers": {
    "mcp-m3u8-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v", "/path/to/local/output:/app/output",
        "-v", "/path/to/local/ts_files:/app/ts_files",
        "yourusername/mcp-m3u8-server"
      ]
    }
  }
}
```

### 使用示例

完成配置后，你可以在Claude中使用以下自然语言指令：

- "分析这个m3u8文件：https://example.com/video.m3u8"
- "下载这个m3u8视频：https://example.com/video.m3u8 并保存到D:/videos/output.mp4"
- "检查当前下载状态"
- "清理所有临时文件"

## 提供的工具

1. **analyze_m3u8** - 分析m3u8文件，获取基本信息
2. **download_m3u8_video** - 从m3u8链接下载视频，解密并合并为mp4文件
3. **check_download_status** - 检查当前下载状态和临时文件夹信息
4. **clean_temp_files** - 清理下载过程中产生的临时文件

## 实现细节

- 支持标准m3u8文件和带有auth_key参数的ts文件URL
- 使用Python的multiprocessing模块实现多进程并行下载
- 使用pycryptodome库处理AES-128加密的视频流
- 通过tqdm显示下载进度
- 临时文件保存在ts_files/目录下，下载完成后自动清理
- 失败片段自动重试机制，最大重试次数可配置

## 注意事项

- 请确保有足够的磁盘空间用于存储临时文件和最终视频
- 部分网站可能需要特定的headers才能正常下载，可以根据需要修改代码中的请求头
- 本工具仅用于合法用途，请遵守相关法律法规和视频网站的使用条款

## 许可证

MIT License