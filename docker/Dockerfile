FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY mcp_server.py .

# 创建数据和临时文件夹
RUN mkdir -p /app/data /app/ts_files

# 设置环境变量
ENV PORT=3001
ENV HOST=0.0.0.0
ENV DATA_DIR=/app/data

# 暴露端口
EXPOSE 3001

# 启动服务
CMD ["python", "mcp_server.py"] 