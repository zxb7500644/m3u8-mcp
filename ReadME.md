# MCP M3U8 视频下载服务器

这是一个基于Model Context Protocol (MCP)的服务器，用于下载、解密和合并m3u8视频。该服务器能够接收m3u8地址和本地存储路径，自动下载解析m3u8文件中的ts片段，解密并合并成mp4文件，最终保存至指定路径。

## 功能特点

- 解析m3u8文件，支持加密和非加密的视频流
- 使用多进程并行下载ts文件片段，提高下载速度
- 支持AES-128解密
- 将所有ts文件按顺序合并为mp4文件
- 提供下载状态检查和临时文件清理功能

## 系统要求

- Python 3.8+
- 依赖包：mcp, pycryptodome, requests, tqdm

## 安装方法

1. 克隆或下载本项目
2. 安装依赖包：

```bash
pip install mcp pycryptodome requests tqdm
```

## 使用方法

### 启动服务器

```bash
python mcp_server.py
```

服务器将在本地启动，默认使用标准I/O(stdio)作为通信通道，可以与支持MCP的客户端（如Claude Desktop）进行连接。

### 提供的工具

1. **download_m3u8_video** - 从m3u8链接下载视频，解密并合并为mp4文件
   - 参数：
     - m3u8_url: m3u8文件的URL地址
     - output_path: 输出mp4文件的本地保存路径
     - processes: 并行下载的进程数，默认为4
   - 返回：输出文件的完整路径

2. **check_download_status** - 检查当前下载状态和临时文件夹信息
   - 返回：当前下载状态和临时文件信息

3. **clean_temp_files** - 清理下载过程中产生的临时文件
   - 返回：清理结果信息

### 在Claude Desktop中使用

1. 启动服务器
2. 在Claude Desktop中连接到本地服务器
3. 向Claude询问关于下载m3u8视频的任务，例如：
   - "请帮我下载这个m3u8视频：[URL]，并保存到 D:/videos/output.mp4"
   - "检查当前的下载状态"
   - "清理所有的临时文件"

## 实现细节

- 服务器使用MCP (Model Context Protocol) SDK创建，提供标准化的工具接口
- 使用Python的multiprocessing模块实现多进程并行下载
- 使用pycryptodome库处理AES-128加密的视频流
- 通过tqdm显示下载进度
- 临时文件保存在ts_files/目录下，下载完成后自动清理

## 异常处理

- 网络连接失败时，会返回对应的错误信息
- 解析m3u8文件失败时，会提供详细的错误提示
- 文件操作异常时，会捕获并返回友好的错误消息

## 注意事项

- 请确保有足够的磁盘空间用于存储临时文件和最终视频
- 部分网站可能需要特定的headers才能正常下载，可以根据需要修改代码中的请求头
- 本工具仅用于合法用途，请遵守相关法律法规和视频网站的使用条款

## 许可证

MIT License