#!/usr/bin/env python
"""
MCP M3U8视频下载服务器启动脚本
"""

import sys
from mcp_server import mcp, server_name, server_description
from mcp import stdio_server

def main():
    print(f"启动 MCP M3U8 视频下载服务器...")
    print(f"服务器名称: {server_name}")
    print(f"服务器说明: {server_description}")
    print("可用工具:")
    print(" - analyze_m3u8: 分析m3u8文件，获取基本信息")
    print(" - download_m3u8_video: 从m3u8链接下载视频，解密并合并为mp4文件")
    print(" - check_download_status: 检查当前下载状态和临时文件夹信息")
    print(" - clean_temp_files: 清理下载过程中产生的临时文件")
    print("\n使用Claude Desktop或其他MCP客户端连接到此服务器")
    
    # 使用stdio作为通信通道启动服务器
    try:
        stdio_server(mcp)
    except KeyboardInterrupt:
        print("\n服务器已停止")
        sys.exit(0)

if __name__ == "__main__":
    main() 