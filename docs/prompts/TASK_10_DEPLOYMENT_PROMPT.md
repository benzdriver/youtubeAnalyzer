# Task 10: 部署配置 - Sub-Session Prompt

## 必读文档

**重要提示**: 开始此任务前，你必须阅读并理解以下文档：

### 核心协调文档
- `docs/TASK_COORDINATION.md` - 整体任务依赖关系和项目结构
- `docs/ARCHITECTURE_OVERVIEW.md` - 系统架构和技术栈
- `docs/CODING_STANDARDS.md` - 代码格式、命名规范和最佳实践
- `docs/API_SPECIFICATIONS.md` - 完整API接口定义

### 任务专用文档
- `docs/tasks/TASK_10_DEPLOYMENT.md` - 详细任务要求和验收标准
- `docs/contracts/deployment_contract.md` - 部署配置接口规范

### 参考文档
- `docs/DEVELOPMENT_SETUP.md` - 开发环境配置
- `docs/PROGRESS_TRACKER.md` - 进度跟踪和任务状态更新

### 依赖关系
- 所有前置任务 (Task 1-9) 必须先完成
- 查看所有相关的contract文档了解各模块接口
- 确保系统集成测试通过后再进行部署配置

## 项目背景

你正在为YouTube视频分析工具构建部署配置。这个任务需要：
- 配置Docker容器化部署
- 建立CI/CD流水线
- 设置生产环境配置
- 实现监控和日志系统
- 确保系统的稳定性和安全性

## 任务目标

实现完整的部署配置，包括Docker配置、CI/CD流水线、环境管理、监控系统和运维文档。

## 具体要求

### 1. Docker生产环境配置

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - static_files:/var/www/static
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    volumes:
      - static_files:/app/static
      - media_files:/app/media
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.core.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
    volumes:
      - media_files:/app/media
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  static_files:
  media_files:
```

### 2. GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'

    - name: Install Python dependencies
      run: |
        cd backend
        pip install -r requirements.txt

    - name: Install Node.js dependencies
      run: |
        cd frontend
        npm ci

    - name: Run Python tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379
      run: |
        cd backend
        pytest

    - name: Run Node.js tests
      run: |
        cd frontend
        npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Deploy to production
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /opt/youtube-analyzer
          git pull origin main
          docker-compose -f docker-compose.prod.yml up -d --build
          docker system prune -f

    - name: Health check
      run: |
        sleep 30
        curl -f ${{ secrets.PRODUCTION_URL }}/health || exit 1
```

### 3. 生产环境Dockerfile

```dockerfile
# backend/Dockerfile.prod
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "app.main:app"]
```

```dockerfile
# frontend/Dockerfile.prod
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# 生产镜像
FROM node:18-alpine AS runner

WORKDIR /app

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

### 4. Nginx配置

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name youtubeanalyzer.com;
        
        # 重定向到HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name youtubeanalyzer.com;

        # SSL配置
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;

        # 安全头
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # 前端路由
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API路由
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 300s;
        }

        # WebSocket路由
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }

        # 健康检查
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }
    }
}
```

### 5. 环境变量配置

```bash
# .env.prod.example
# 数据库配置
DATABASE_URL=postgresql://username:password@postgres:5432/youtube_analyzer
POSTGRES_DB=youtube_analyzer
POSTGRES_USER=username
POSTGRES_PASSWORD=strong_password

# Redis配置
REDIS_URL=redis://:redis_password@redis:6379
REDIS_PASSWORD=strong_redis_password

# API密钥
OPENAI_API_KEY=your_openai_api_key
YOUTUBE_API_KEY=your_youtube_api_key

# 应用配置
SECRET_KEY=your_very_long_secret_key
API_URL=https://yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com

# 部署配置
HOST=your_server_ip
USERNAME=deploy_user
PRODUCTION_URL=https://yourdomain.com
```

### 6. 部署脚本

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 开始部署YouTube分析工具..."

# 检查环境变量
if [ ! -f .env.prod ]; then
    echo "❌ 缺少 .env.prod 文件"
    exit 1
fi

# 备份数据库
echo "📦 备份数据库..."
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup_$(date +%Y%m%d_%H%M%S).sql

# 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 构建和启动服务
echo "🔨 构建和启动服务..."
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 运行数据库迁移
echo "🗃️ 运行数据库迁移..."
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 健康检查
echo "🏥 健康检查..."
sleep 30
if curl -f http://localhost/health; then
    echo "✅ 部署成功！"
else
    echo "❌ 健康检查失败"
    exit 1
fi

# 清理旧镜像
echo "🧹 清理旧镜像..."
docker system prune -f

echo "🎉 部署完成！"
```

## 验收标准

### 功能验收
- [ ] Docker容器正常启动
- [ ] CI/CD流水线正常工作
- [ ] 生产环境配置正确
- [ ] SSL证书配置正确
- [ ] 健康检查正常
- [ ] 数据库迁移正常

### 技术验收
- [ ] 服务启动时间 < 2分钟
- [ ] 负载均衡正常工作
- [ ] 自动重启机制有效
- [ ] 资源使用合理
- [ ] 日志记录完整

### 质量验收
- [ ] 安全配置符合最佳实践
- [ ] 监控和告警正常
- [ ] 备份和恢复流程完整
- [ ] 文档完整准确
- [ ] 部署流程可重复

## 测试要求

### 部署测试
```bash
# 测试部署脚本
./deploy.sh

# 测试健康检查
curl -f http://localhost/health

# 测试API端点
curl -f http://localhost/api/v1/health

# 测试WebSocket连接
wscat -c ws://localhost/ws/test

# 测试数据库连接
docker-compose -f docker-compose.prod.yml exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"
```

### 性能测试
```bash
# 负载测试
ab -n 1000 -c 10 http://localhost/api/v1/health

# 内存使用监控
docker stats

# 磁盘使用检查
df -h
```

## 交付物清单

- [ ] 生产环境Docker配置 (docker-compose.prod.yml)
- [ ] 生产环境Dockerfile (backend/Dockerfile.prod, frontend/Dockerfile.prod)
- [ ] Nginx配置 (nginx/nginx.conf)
- [ ] CI/CD流水线 (.github/workflows/deploy.yml)
- [ ] 环境变量模板 (.env.prod.example)
- [ ] 部署脚本 (deploy.sh)
- [ ] 监控配置 (monitoring/)
- [ ] SSL证书配置
- [ ] 备份和恢复脚本
- [ ] 运维文档

## 关键接口

完成此任务后，需要为后续任务提供：
- 稳定的生产环境
- 自动化部署流程
- 监控和告警系统
- 运维管理工具

## 预估时间

- 开发时间: 2-3天
- 测试时间: 1天
- 文档编写: 0.5天
- 部署调试: 1天
- 总计: 4.5-5.5天

## 注意事项

1. 确保所有敏感信息都通过环境变量管理
2. 实现合理的资源限制和监控
3. 配置适当的安全策略和防火墙规则
4. 建立完整的备份和恢复流程
5. 提供详细的运维文档和故障排除指南

这是整个系统的部署基础，请确保配置的安全性和稳定性。
