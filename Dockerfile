# ==============================
# 第一阶段：编译前端 (Node.js)
# ==============================
FROM node:18 AS frontend-builder
WORKDIR /build-web

# 复制前端代码
COPY web/ .

# 安装依赖并构建
# 使用淘宝源加速
RUN npm config set registry https://registry.npmmirror.com && \
    npm install && \
    npm run build


# ==============================
# 第二阶段：构建运行镜像 (Python + Nginx)
# ==============================
FROM python:3.12-slim

# 1. 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

# 2. 安装系统依赖
# 注意：安装 libpq-dev 是为了支持 PostgreSQL
# 安装 nginx 用于托管前端
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    libpq-dev \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. 安装 Python 依赖
# 复制必要的文件
COPY pyproject.toml uv.lock README.md ./

# 安装构建依赖和项目依赖
# 先更新pip，然后安装构建工具，最后安装项目依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir hatchling && \
    pip install --no-cache-dir . && \
    pip install --no-cache-dir psycopg2-binary

# 4. 复制后端和挡板代码
COPY app/ ./app/
COPY config/ ./config/
# 复制环境变量模板
COPY .env.template .

# 5. 从第一阶段复制编译好的前端文件
# 将 dist 目录复制到容器内
COPY --from=frontend-builder /build-web/dist ./web/dist

# 6. 配置 Nginx 和 启动脚本
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh .
# 修复换行符并设置执行权限
RUN sed -i 's/\r$//' entrypoint.sh && \
    chmod +x entrypoint.sh

# 7. 创建日志文件目录
RUN touch /var/log/mock.log /var/log/backend.log && chmod 777 /var/log/*.log

# 8. 暴露端口 (只暴露 80)
EXPOSE 80

# 9. 启动
ENTRYPOINT ["./entrypoint.sh"]
