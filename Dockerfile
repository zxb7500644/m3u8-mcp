FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY mcp_server.py .

# 创建必要的目录
RUN mkdir -p ts_files
RUN mkdir -p output

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 使用stdin/stdout
CMD ["python", "-u", "mcp_server.py"]