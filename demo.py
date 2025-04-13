#!/usr/bin/env python
"""
MCP M3U8视频下载服务器演示脚本
此脚本直接调用下载功能，无需通过MCP协议
"""

import os
import asyncio
import argparse
import sys
from mcp_server import analyze_m3u8, download_m3u8_video, check_download_status, clean_temp_files, server_name, server_description

async def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description=f'{server_name}: {server_description}')
    parser.add_argument('--url', help='m3u8文件的URL地址')
    parser.add_argument('--output', default='output.mp4', help='输出mp4文件的本地保存路径')
    parser.add_argument('--processes', type=int, default=4, help='并行下载的进程数')
    parser.add_argument('--analyze', action='store_true', help='仅分析m3u8文件，不下载')
    parser.add_argument('--clean', action='store_true', help='清理临时文件')
    parser.add_argument('--status', action='store_true', help='检查下载状态')
    
    args = parser.parse_args()
    
    # 检查下载状态
    if args.status:
        result = await check_download_status()
        print(result)
        return
        
    # 清理临时文件
    if args.clean:
        result = await clean_temp_files()
        print(result)
        return
    
    # 验证必要参数
    if not args.url and not (args.status or args.clean):
        parser.error('请提供m3u8 URL参数 (--url)')
        return
    
    # 仅分析m3u8文件
    if args.analyze:
        result = await analyze_m3u8(args.url)
        print(result)
        return
    
    # 下载视频
    print(f"正在从 {args.url} 下载视频...")
    print(f"输出文件: {args.output}")
    print(f"并行进程数: {args.processes}")
    
    # 确保输出目录存在
    output_dir = os.path.dirname(os.path.abspath(args.output))
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 执行下载
    result = await download_m3u8_video(args.url, args.output, args.processes)
    print(result)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n下载已取消")
        sys.exit(0) 