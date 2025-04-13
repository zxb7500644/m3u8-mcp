# MCP M3U8 视频下载器

这是一个基于Model Context Protocol (MCP)的m3u8视频下载服务器，可以分析、下载、解密和合并m3u8视频。

## 功能特点

- 分析m3u8文件，获取基本信息
- 下载并解密m3u8视频，合并为mp4
- 多进程并行下载，提高下载速度
- 支持各种加密方式，包括AES-128
- 自动重试下载失败的片段
- 清理临时文件

## 安装方法

使用npx直接运行（无需安装）：

```bash
npx m3u8-downloader-mcp
```

或者全局安装：

```bash
npm install -g m3u8-downloader-mcp
```

## 前置要求

- Node.js 14+
- Python 3.6+
- pip（Python包管理器）

## 在Cursor中配置

1. 打开Cursor
2. 进入设置
3. 找到MCP服务器配置部分
4. 添加以下配置：

```json
{
  "mcpServers": {
    "m3u8-downloader": {
      "command": "npx",
      "args": [
        "-y",
        "m3u8-downloader-mcp"
      ]
    }
  }
}
```

## 可用工具

- `analyze_m3u8`: 分析m3u8文件，获取基本信息
- `download_m3u8_video`: 从m3u8链接下载视频，解密并合并为mp4文件
- `check_download_status`: 检查当前下载状态和临时文件夹信息
- `clean_temp_files`: 清理下载过程中产生的临时文件

## 使用示例

在Cursor的AI会话中使用以下命令：

```
请分析这个m3u8链接：https://example.com/video.m3u8
```

```
请将此m3u8视频下载到D:/videos/output.mp4：https://example.com/video.m3u8
```

## 常见问题

### 服务器启动失败
- 确保已安装Python 3.6+
- 安装所需的Python包：`pip install mcp pycryptodome requests tqdm flask`
- 在Windows上，可能需要以管理员权限运行

### 下载失败
- 检查m3u8链接是否有效
- 确保有足够的磁盘空间
- 检查目标目录的写入权限

## 许可证

MIT