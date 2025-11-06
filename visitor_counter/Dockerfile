FROM python:3.10-alpine

WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY main.py .
COPY start.py .
COPY visitor_service.py .
COPY config.py .

# 暴露端口
EXPOSE 8081

# 启动命令
CMD ["python", "start.py"]

