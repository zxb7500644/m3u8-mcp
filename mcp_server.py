import os
import re
import requests
import asyncio
import anyio
import shutil
import time
import json
import uvicorn
from fastapi import FastAPI, Request, Response, Depends, HTTPException, Header
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from sse_starlette.sse import EventSourceResponse
from fastapi.middleware.cors import CORSMiddleware
from multiprocessing import Pool
from tqdm import tqdm
from Crypto.Cipher import AES
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import uuid

from mcp.server import FastMCP
from mcp.server.sse import SseServerTransport

# 从环境变量获取API密钥，如果未设置则使用默认值
API_KEY = os.environ.get("API_KEY", None)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# 创建MCP服务器
server_name = "MCP M3U8 Video Server"
server_description = "一个用于下载、解密和合并m3u8视频的服务器"

# 创建SSE传输
sse_transport = SseServerTransport("/messages/")

# 创建MCP服务器
mcp = FastMCP(
    name=server_name,
    instructions=server_description
)

# 临时文件夹路径
TEMP_DIR = 'ts_files/'
# 数据存储目录
DATA_DIR = os.environ.get("DATA_DIR", "data/")

# 确保临时文件夹和数据目录存在
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# API认证验证
async def get_api_key(api_key_header: str = Depends(api_key_header)):
    if API_KEY is None:
        # 如果未配置API密钥，则不需要验证
        return True
    if api_key_header == API_KEY:
        return True
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="认证失败，无效的API密钥"
    )

# 创建FastAPI应用
app = FastAPI(title="MCP M3U8 Video Server")

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建带有重试机制的会话
def create_request_session(retries=3, backoff_factor=0.3):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(500, 502, 503, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# 通用请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive'
}

# 解析m3u8文本内容
def parse_m3u8_text(m3u8_text, m3u8_url):
    m3u8_text = m3u8_text.split('\n')
    
    # 提取加密信息
    encode_info = [line for line in m3u8_text if line.startswith('#EXT-X-KEY:')]
    if encode_info:
        encode_info = encode_info[0]
        pattern = r"#EXT-X-KEY:METHOD=(.*),URI=\"(.*)\""
        match = re.search(pattern, encode_info)
        if match:
            method = match.group(1)
            key_url = match.group(2)
            
            # 处理相对URL路径
            if not key_url.startswith(('http://', 'https://')):
                base_url = '/'.join(m3u8_url.split('/')[:-1]) + '/'
                key_url = base_url + key_url
        else:
            raise Exception('解析加密信息失败')
    else:
        # 无加密
        method = None
        key_url = None
    
    # 提取ts文件URL
    ts_list = []
    for line in m3u8_text:
        if line and not line.startswith('#'):
            ts_url = line.strip()
            # 检查是否是ts文件或带有auth_key参数的URL
            if ts_url.endswith('.ts') or ('ts?' in ts_url and 'auth_key=' in ts_url):
                # 处理相对URL路径
                if not ts_url.startswith(('http://', 'https://')):
                    base_url = '/'.join(m3u8_url.split('/')[:-1]) + '/'
                    ts_url = base_url + ts_url
                ts_list.append(ts_url)
    
    if not ts_list:
        raise Exception('未找到任何ts文件链接')
        
    return method, key_url, ts_list

# 下载并解密ts文件
def process_one_url(args):
    ts_url, key, iv, index, base_session = args
    session = create_request_session() if base_session is None else base_session
    
    try:
        filename = f"{TEMP_DIR}{index:05d}.ts"
        response = session.get(ts_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        content = response.content
        
        if key:
            # 支持AES-128-CBC模式
            if iv:
                decrypter = AES.new(key, AES.MODE_CBC, iv=iv)
            else:
                # 如果没有提供IV，使用全零IV（某些流媒体使用）
                decrypter = AES.new(key, AES.MODE_CBC, iv=b'\x00' * 16)
                
            # 处理填充问题
            decrypted_content = decrypter.decrypt(content)
            with open(filename, mode='wb') as f:
                f.write(decrypted_content)
        else:
            # 无加密，直接保存
            with open(filename, mode='wb') as f:
                f.write(content)
        
        return filename
    except requests.exceptions.RequestException as e:
        return f"下载失败: {ts_url}, 错误: {str(e)}"
    except Exception as e:
        return f"处理失败: {ts_url}, 错误: {str(e)}"

# 合并ts文件为mp4
def merge_ts_to_mp4(filename, ts_file_list):
    try:
        with open(filename, mode='wb') as f1:
            for ts_file in ts_file_list:
                if os.path.exists(ts_file) and isinstance(ts_file, str) and ts_file.endswith('.ts'):
                    with open(ts_file, mode='rb') as f2:
                        f1.write(f2.read())
        
        # 检查文件是否创建成功
        if not os.path.exists(filename):
            raise Exception(f"文件合并失败: {filename}")
            
        # 检查文件大小是否合理
        if os.path.getsize(filename) < 1024:  # 至少1KB
            raise Exception(f"合并的文件大小异常: {os.path.getsize(filename)} 字节")
        
        return True
    except Exception as e:
        raise Exception(f"合并文件时出错: {str(e)}")

# 检查磁盘空间
def check_disk_space(path, required_space_mb=1000):
    """检查指定路径是否有足够的磁盘空间"""
    try:
        total, used, free = shutil.disk_usage(os.path.dirname(os.path.abspath(path)))
        free_mb = free / (1024 * 1024)  # 转换为MB
        
        if free_mb < required_space_mb:
            return False, f"磁盘空间不足: 只有 {free_mb:.2f}MB 可用，需要至少 {required_space_mb}MB"
        return True, f"磁盘空间充足: {free_mb:.2f}MB 可用"
    except Exception as e:
        return False, f"检查磁盘空间失败: {str(e)}"

# MCP提示模板数据
PROMPTS = {
    "download_video": {
        "id": "download_video",
        "name": "下载视频",
        "description": "从m3u8链接下载视频的提示模板",
        "content": "请帮我下载以下m3u8链接的视频：{url}，保存到{output_path}。"
    },
    "analyze_video": {
        "id": "analyze_video",
        "name": "分析视频",
        "description": "分析m3u8视频的提示模板",
        "content": "请分析以下m3u8链接的内容：{url}，并告诉我视频的基本信息。"
    }
}

# MCP资源数据
RESOURCES = {
    "readme": {
        "uri": "readme",
        "content": """
# MCP M3U8 视频下载服务

这是一个用于下载、解密和合并m3u8视频的服务器，支持以下功能：

1. 分析m3u8文件内容
2. 下载并解密m3u8视频
3. 检查下载状态
4. 清理临时文件

## 使用方法

1. 使用`analyze_m3u8`工具分析视频信息
2. 使用`download_m3u8_video`工具下载视频
3. 使用`check_download_status`工具检查下载状态
4. 使用`clean_temp_files`工具清理临时文件
        """
    },
    "usage_example": {
        "uri": "usage_example",
        "content": """
# 使用示例

以下是在n8n中使用MCP客户端连接到此服务器的示例：

1. 在n8n中添加MCP客户端节点
2. 选择SSE连接方式
3. 设置SSE URL为`http://<host>:3001/sse`
4. 如果配置了API密钥，添加Header: `X-API-Key: <your-api-key>`
5. 选择操作（如Execute Tool）
6. 选择要执行的工具（如analyze_m3u8）
7. 设置参数并执行
        """
    }
}

# 注册MCP提示模板
for prompt_id, prompt_data in PROMPTS.items():
    # 为每个提示模板创建唯一的函数
    def create_prompt_func(p_id):
        @mcp.prompt(name=PROMPTS[p_id]["id"], description=PROMPTS[p_id]["description"])
        def prompt_func():
            """返回提示模板内容"""
            return [{"role": "user", "content": PROMPTS[p_id]["content"]}]
        return prompt_func
    
    # 立即执行函数以避免闭包问题
    create_prompt_func(prompt_id)

# 注册MCP资源
for res_uri, res_data in RESOURCES.items():
    # 为每个资源创建唯一的函数
    def create_resource_func(uri):
        @mcp.resource(uri=f"resource://{uri}", name=uri, description=uri)
        def resource_func():
            """返回资源内容"""
            return RESOURCES[uri]["content"]
        return resource_func
    
    # 立即执行函数以避免闭包问题
    create_resource_func(res_uri)

# 添加MCP工具：列出提示模板
@mcp.tool()
async def list_prompts() -> str:
    """
    列出所有可用的提示模板
    
    Returns:
        提示模板列表信息
    """
    result = "可用提示模板：\n\n"
    for prompt_id, prompt in PROMPTS.items():
        result += f"ID: {prompt['id']}\n"
        result += f"名称: {prompt['name']}\n"
        result += f"描述: {prompt['description']}\n\n"
    
    return result

# 添加MCP工具：获取提示模板
@mcp.tool()
async def get_prompt(prompt_id: str) -> str:
    """
    获取指定的提示模板
    
    Args:
        prompt_id: 提示模板的ID
    
    Returns:
        提示模板内容
    """
    if prompt_id not in PROMPTS:
        return f"错误：未找到ID为 {prompt_id} 的提示模板"
    
    prompt = PROMPTS[prompt_id]
    result = f"ID: {prompt['id']}\n"
    result += f"名称: {prompt['name']}\n"
    result += f"描述: {prompt['description']}\n"
    result += f"内容: {prompt['content']}\n"
    
    return result

# 添加MCP工具：列出资源
@mcp.tool()
async def list_resources() -> str:
    """
    列出所有可用的资源
    
    Returns:
        资源列表信息
    """
    result = "可用资源：\n\n"
    for uri, resource in RESOURCES.items():
        result += f"URI: {resource['uri']}\n"
    
    return result

# 添加MCP工具：读取资源
@mcp.tool()
async def read_resource(uri: str) -> str:
    """
    读取指定的资源
    
    Args:
        uri: 资源的URI
    
    Returns:
        资源内容
    """
    if uri not in RESOURCES:
        return f"错误：未找到URI为 {uri} 的资源"
    
    return RESOURCES[uri]['content']

# MCP工具：分析m3u8文件
@mcp.tool()
async def analyze_m3u8(m3u8_url: str) -> str:
    """
    分析m3u8文件，获取基本信息
    
    Args:
        m3u8_url: m3u8文件的URL地址
    
    Returns:
        m3u8文件的基本信息
    """
    try:
        session = create_request_session()
        response = session.get(m3u8_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        m3u8_content = response.text
        
        # 解析m3u8内容
        method, key_url, ts_list = parse_m3u8_text(m3u8_content, m3u8_url)
        
        info = {
            "加密方式": method if method else "无加密",
            "ts文件数量": len(ts_list),
            "预估大小(MB)": len(ts_list) * 2,  # 粗略估计，假设每个ts文件平均2MB
            "第一个ts文件": ts_list[0] if ts_list else "无",
            "密钥地址": key_url if key_url else "无"
        }
        
        result = "m3u8文件分析结果:\n"
        for key, value in info.items():
            result += f"{key}: {value}\n"
            
        return result
        
    except Exception as e:
        return f"分析失败: {str(e)}"

# MCP工具：下载并处理m3u8视频
@mcp.tool()
async def download_m3u8_video(m3u8_url: str, output_path: str, processes: int = 4, max_retries: int = 3) -> str:
    """
    从m3u8链接下载视频，解密并合并为mp4文件
    
    Args:
        m3u8_url: m3u8文件的URL地址
        output_path: 输出mp4文件的本地保存路径
        processes: 并行下载的进程数，默认为4
        max_retries: 失败片段的最大重试次数，默认为3
    
    Returns:
        输出文件的完整路径
    """
    start_time = time.time()
    
    try:
        # 创建输出目录（如果不存在）
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 检查磁盘空间
        space_ok, space_msg = check_disk_space(output_path)
        if not space_ok:
            return space_msg
        
        # 下载m3u8文件内容
        session = create_request_session()
        response = session.get(m3u8_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        m3u8_content = response.text
        
        # 解析m3u8内容
        method, key_url, ts_list = parse_m3u8_text(m3u8_content, m3u8_url)
        
        # 如果有加密，获取密钥
        key = None
        iv = None
        if method and key_url:
            if method.upper() != 'AES-128':
                return f"不支持的加密方法: {method}，目前仅支持AES-128"
                
            key_response = session.get(key_url, headers=HEADERS, timeout=10)
            key_response.raise_for_status()
            key = key_response.content
            
            # 尝试提取IV（初始化向量）
            iv_match = re.search(r"IV=0x([0-9a-fA-F]+)", m3u8_content)
            if iv_match:
                iv_hex = iv_match.group(1)
                iv = bytes.fromhex(iv_hex)
        
        # 清空临时目录
        for file in os.listdir(TEMP_DIR):
            try:
                os.remove(os.path.join(TEMP_DIR, file))
            except:
                pass
        
        # 使用多进程下载和处理ts文件
        ts_file_list = []
        total_files = len(ts_list)
        
        print(f"开始下载 {total_files} 个ts文件...")
        
        with Pool(processes=processes) as pool:
            args_list = [(ts_url, key, iv, i, None) for i, ts_url in enumerate(ts_list)]
            
            # 使用imap处理结果，可以实时显示进度
            failed_downloads = []
            for i, result in enumerate(tqdm(
                pool.imap_unordered(process_one_url, args_list),
                total=total_files,
                desc="下载并解密TS文件"
            )):
                if isinstance(result, str) and result.endswith('.ts'):
                    ts_file_list.append(result)
                else:
                    failed_downloads.append((i, result))
        
        # 重试逻辑：处理失败的片段
        retry_count = 0
        while failed_downloads and retry_count < max_retries:
            retry_count += 1
            print(f"\n第{retry_count}次重试下载 {len(failed_downloads)} 个失败片段...")
            
            # 准备重试参数
            retry_args_list = []
            for i, error_msg in failed_downloads:
                # 错误信息中提取原始URL (从 "下载失败: URL, 错误: ..." 或 "处理失败: URL, 错误: ...")
                parts = error_msg.split(", 错误:")
                if len(parts) > 0:
                    url_part = parts[0]
                    ts_url = url_part.replace("下载失败: ", "").replace("处理失败: ", "")
                    retry_args_list.append((ts_url, key, iv, i, None))
            
            # 清空上一轮的失败记录，准备记录这一轮的失败
            still_failed = []
            
            # 执行重试
            for args in tqdm(retry_args_list, desc=f"重试下载失败片段 (第{retry_count}次)"):
                result = process_one_url(args)
                if isinstance(result, str) and result.endswith('.ts'):
                    ts_file_list.append(result)
                else:
                    still_failed.append((args[3], result))  # args[3] 是索引 i
            
            # 更新失败列表
            failed_downloads = still_failed
            
            # 如果全部下载成功，退出循环
            if not failed_downloads:
                print(f"重试成功，所有片段均已下载")
                break
        
        # 重试后仍有失败的文件
        if failed_downloads:
            failed_msgs = [msg for _, msg in failed_downloads]
            return f"下载完成，但有 {len(failed_downloads)} 个文件下载失败 (已重试{retry_count}次):\n" + "\n".join(failed_msgs[:5]) + (
                f"\n... 和其他 {len(failed_msgs) - 5} 个文件" if len(failed_msgs) > 5 else ""
            )
        
        # 排序ts文件（确保顺序正确）
        ts_file_list.sort()
        
        # 合并为mp4文件
        print(f"开始合并 {len(ts_file_list)} 个ts文件为mp4...")
        merge_ts_to_mp4(output_path, ts_file_list)
        
        # 清理临时文件
        for ts_file in ts_file_list:
            try:
                os.remove(ts_file)
            except:
                pass
        
        # 计算处理时间
        elapsed_time = time.time() - start_time
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        
        return f"视频已成功下载并保存到: {output_path}\n" \
               f"文件大小: {file_size_mb:.2f}MB\n" \
               f"处理时间: {elapsed_time:.2f}秒\n" \
               f"下载速度: {file_size_mb/elapsed_time:.2f}MB/s"
    
    except Exception as e:
        return f"处理失败: {str(e)}"

# MCP工具：检查视频下载状态
@mcp.tool()
async def check_download_status() -> str:
    """
    检查当前下载状态和临时文件夹信息
    
    Returns:
        当前下载状态和临时文件信息
    """
    try:
        if not os.path.exists(TEMP_DIR):
            return "临时目录不存在"
        
        files = os.listdir(TEMP_DIR)
        if not files:
            return "临时目录为空，当前没有下载任务或已完成"
            
        ts_files = [f for f in files if f.endswith('.ts')]
        total_size_mb = sum(os.path.getsize(os.path.join(TEMP_DIR, f)) for f in files) / (1024 * 1024)
        
        return f"临时目录中有 {len(ts_files)} 个ts文件\n" \
               f"总大小: {total_size_mb:.2f}MB"
    
    except Exception as e:
        return f"检查状态失败: {str(e)}"

# MCP工具：清理临时文件
@mcp.tool()
async def clean_temp_files() -> str:
    """
    清理下载过程中产生的临时文件
    
    Returns:
        清理结果信息
    """
    try:
        count = 0
        total_size_mb = 0
        
        if os.path.exists(TEMP_DIR):
            for file in os.listdir(TEMP_DIR):
                try:
                    file_path = os.path.join(TEMP_DIR, file)
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    total_size_mb += size_mb
                    os.remove(file_path)
                    count += 1
                except:
                    pass
        
        return f"已清理 {count} 个临时文件，释放了 {total_size_mb:.2f}MB 磁盘空间"
    
    except Exception as e:
        return f"清理失败: {str(e)}"

# 获取FastMCP创建的ASGI应用
# mcp_app = mcp.sse_app()  # 不使用这种方式

# 将MCP的SSE和消息处理集成到FastAPI
@app.get("/sse")
async def sse_route(request: Request, authenticated: bool = Depends(get_api_key)):
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp._mcp_server.run(
            streams[0], streams[1], mcp._mcp_server.create_initialization_options()
        )

# 将消息路由挂载到FastAPI
from starlette.routing import Mount

# 直接使用SseServerTransport的消息处理器
app.routes.append(Mount("/messages/", app=sse_transport.handle_post_message))

# 添加健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy", "server": server_name}

# 添加根路径信息
@app.get("/")
async def root():
    return {
        "name": server_name,
        "description": server_description,
        "tools": [t.name for t in await mcp._mcp_server.list_tools()],
        "prompts": [p.name for p in await mcp._mcp_server.list_prompts()],
        "resources": [r.uri for r in await mcp._mcp_server.list_resources()]
    }

if __name__ == "__main__":
    import sys
    
    # 使用MCP客户端连接而不是自行实现SSE
    print(f"启动 MCP M3U8 视频下载服务器...")
    print(f"服务器名称: {server_name}")
    print(f"服务器说明: {server_description}")
    print(f"SSE端点: http://localhost:3001/sse")
    
    # 打印API认证状态
    if API_KEY:
        print("API认证: 已启用")
    else:
        print("API认证: 未启用")
    
    # 启动服务器
    uvicorn.run(app, host="0.0.0.0", port=3001) 