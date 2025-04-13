import os
import re
import requests
import asyncio
import shutil
import time
from multiprocessing import Pool
from tqdm import tqdm
from Crypto.Cipher import AES
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from mcp.server import FastMCP

# 创建MCP服务器
server_name = "MCP M3U8 Video Server"
server_description = "一个用于下载、解密和合并m3u8视频的服务器"

mcp = FastMCP(server_name)

# 临时文件夹路径
TEMP_DIR = 'ts_files/'

# 确保临时文件夹存在
os.makedirs(TEMP_DIR, exist_ok=True)

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
        # 检查磁盘空间
        space_ok, space_msg = check_disk_space(output_path)
        if not space_ok:
            return space_msg
            
        # 创建输出目录（如果不存在）
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
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

if __name__ == "__main__":
    # 运行MCP服务器
    from mcp import stdio_server
    
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
    stdio_server(mcp) 