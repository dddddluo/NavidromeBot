# 使用 Docker Hub 官方 Python 镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 文件并安装依赖项
COPY Navidrome/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制其余的应用程序代码
COPY Navidrome /app/Navidrome

# 复制 config.json 文件到容器的 Navidrome 目录
COPY config.json /app/Navidrome/config.json

# 复制入口脚本
COPY Navidrome/entrypoint.sh .

# 使入口脚本可执行
RUN chmod +x entrypoint.sh

# 设置容器的入口点
ENTRYPOINT ["./entrypoint.sh"]
