# Task 10: 部署配置

## 任务概述

配置YouTube分析工具的生产环境部署，包括Docker容器化、CI/CD流水线、环境配置、监控告警和文档完善。确保系统能够稳定、安全地在生产环境中运行。

## 目标

- 配置生产环境的Docker部署
- 建立CI/CD自动化流水线
- 实现环境配置和密钥管理
- 配置监控、日志和告警系统
- 编写部署和运维文档

## 可交付成果

### 1. 生产环境Docker配置

#### Docker Compose生产配置
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

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=https://api.youtubeanalyzer.com
      - NEXT_PUBLIC_WS_URL=wss://api.youtubeanalyzer.com
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - storage_data:/app/storage
      - logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    command: celery -A app.main worker --loglevel=info --concurrency=4
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
    volumes:
      - storage_data:/app/storage
      - logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2

  postgres:
    image: postgres:15-alpine
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
  storage_data:
  static_files:
  logs:

networks:
  default:
    driver: bridge
```

#### 生产环境Dockerfile优化
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim as base

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

FROM base as development
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base as production
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /app/storage /app/logs \
    && chown -R app:app /app

COPY . .
RUN chown -R app:app /app

USER app

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 2. CI/CD流水线配置

#### GitHub Actions工作流
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

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
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install backend dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run backend tests
      run: |
        cd backend
        pytest --cov=app --cov-report=xml
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
        REDIS_URL: redis://localhost:6379
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install frontend dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run frontend tests
      run: |
        cd frontend
        npm run test
        npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to production
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.PROD_HOST }}
        username: ${{ secrets.PROD_USER }}
        key: ${{ secrets.PROD_SSH_KEY }}
        script: |
          cd /opt/youtube-analyzer
          git pull origin main
          docker-compose -f docker-compose.prod.yml pull
          docker-compose -f docker-compose.prod.yml up -d
          docker system prune -f
    
    - name: Health check
      run: |
        sleep 30
        curl -f ${{ secrets.PROD_URL }}/health || exit 1
```

### 3. 环境配置和密钥管理

#### 环境变量模板
```bash
# .env.prod.example
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secret-key-here
ALLOWED_ORIGINS=https://youtubeanalyzer.com

DATABASE_URL=postgresql://username:password@postgres:5432/youtube_analyzer
POSTGRES_DB=youtube_analyzer
POSTGRES_USER=youtube_user
POSTGRES_PASSWORD=secure-password

REDIS_URL=redis://:password@redis:6379/0
REDIS_PASSWORD=redis-password

OPENAI_API_KEY=sk-your-openai-api-key
YOUTUBE_API_KEY=your-youtube-api-key

SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem
```

#### Nginx配置
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

    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        listen 80;
        server_name youtubeanalyzer.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name youtubeanalyzer.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;

        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }

        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

### 4. 监控和日志配置

#### 应用监控配置
```python
# backend/app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
import logging

# 定义监控指标
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_TASKS = Gauge('active_analysis_tasks', 'Number of active analysis tasks')
TASK_COMPLETION_TIME = Histogram('task_completion_seconds', 'Task completion time', ['task_type'])

class MonitoringMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            # 包装send函数来捕获响应状态
            status_code = 200
            async def wrapped_send(message):
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                await send(message)
            
            await self.app(scope, receive, wrapped_send)
            
            # 记录指标
            duration = time.time() - start_time
            method = scope["method"]
            path = scope["path"]
            
            REQUEST_COUNT.labels(method=method, endpoint=path, status=status_code).inc()
            REQUEST_DURATION.observe(duration)
        else:
            await self.app(scope, receive, send)

def get_metrics():
    """返回Prometheus格式的指标"""
    return generate_latest()
```

#### 日志配置
```python
# backend/app/core/logging_config.py
import logging
import logging.config
from pathlib import Path

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'json',
            'filename': '/app/logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'json',
            'filename': '/app/logs/error.log',
            'maxBytes': 10485760,
            'backupCount': 5
        }
    },
    'loggers': {
        'app': {
            'level': 'DEBUG',
            'handlers': ['console', 'file', 'error_file'],
            'propagate': False
        },
        'uvicorn': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}

def setup_logging():
    """配置日志系统"""
    # 确保日志目录存在
    Path('/app/logs').mkdir(exist_ok=True)
    
    logging.config.dictConfig(LOGGING_CONFIG)
```

### 5. 部署脚本和文档

#### 部署脚本
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

echo "🚀 开始部署YouTube分析工具..."

# 检查环境变量
if [ ! -f .env.prod ]; then
    echo "❌ 错误: .env.prod 文件不存在"
    exit 1
fi

# 备份当前版本
echo "📦 备份当前版本..."
docker-compose -f docker-compose.prod.yml down
docker tag youtubeanalyzer_backend:latest youtubeanalyzer_backend:backup-$(date +%Y%m%d-%H%M%S) || true
docker tag youtubeanalyzer_frontend:latest youtubeanalyzer_frontend:backup-$(date +%Y%m%d-%H%M%S) || true

# 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 构建新镜像
echo "🔨 构建Docker镜像..."
docker-compose -f docker-compose.prod.yml build

# 数据库迁移
echo "🗄️ 执行数据库迁移..."
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# 启动服务
echo "🚀 启动服务..."
docker-compose -f docker-compose.prod.yml up -d

# 健康检查
echo "🔍 执行健康检查..."
sleep 30

if curl -f http://localhost/health; then
    echo "✅ 部署成功！"
    
    # 清理旧镜像
    echo "🧹 清理旧镜像..."
    docker system prune -f
else
    echo "❌ 健康检查失败，回滚到备份版本..."
    docker-compose -f docker-compose.prod.yml down
    
    # 回滚逻辑
    BACKUP_BACKEND=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep youtubeanalyzer_backend:backup | head -1)
    BACKUP_FRONTEND=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep youtubeanalyzer_frontend:backup | head -1)
    
    if [ ! -z "$BACKUP_BACKEND" ] && [ ! -z "$BACKUP_FRONTEND" ]; then
        docker tag $BACKUP_BACKEND youtubeanalyzer_backend:latest
        docker tag $BACKUP_FRONTEND youtubeanalyzer_frontend:latest
        docker-compose -f docker-compose.prod.yml up -d
        echo "🔄 已回滚到备份版本"
    fi
    
    exit 1
fi

echo "🎉 部署完成！"
```

#### 运维文档
```markdown
# YouTube分析工具运维手册

## 服务管理

### 启动服务
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 停止服务
```bash
docker-compose -f docker-compose.prod.yml down
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f worker
```

### 扩容Worker
```bash
docker-compose -f docker-compose.prod.yml up -d --scale worker=4
```

## 监控和告警

### 关键指标
- HTTP请求响应时间
- 错误率
- 活跃任务数量
- 数据库连接数
- 内存和CPU使用率

### 告警阈值
- 响应时间 > 2秒
- 错误率 > 5%
- 内存使用率 > 90%
- 磁盘使用率 > 85%

## 故障排查

### 常见问题

1. **服务无法启动**
   - 检查环境变量配置
   - 查看Docker日志
   - 验证端口占用情况

2. **分析任务失败**
   - 检查API密钥配置
   - 查看Worker日志
   - 验证网络连接

3. **数据库连接问题**
   - 检查数据库服务状态
   - 验证连接字符串
   - 查看连接池状态

### 性能优化

1. **数据库优化**
   - 定期执行VACUUM
   - 监控慢查询
   - 优化索引

2. **缓存优化**
   - 监控Redis内存使用
   - 调整缓存过期时间
   - 优化缓存键设计

## 备份和恢复

### 数据库备份
```bash
# 创建备份
docker exec postgres pg_dump -U youtube_user youtube_analyzer > backup_$(date +%Y%m%d).sql

# 恢复备份
docker exec -i postgres psql -U youtube_user youtube_analyzer < backup_20240101.sql
```

### 文件备份
```bash
# 备份存储文件
tar -czf storage_backup_$(date +%Y%m%d).tar.gz /opt/youtube-analyzer/storage
```
```

## 依赖关系

### 前置条件
- Task 1: 项目配置管理（必须完成）
- Task 2: 后端API框架（必须完成）
- Task 3: 前端UI框架（必须完成）
- Task 4-9: 所有功能模块（必须完成）

### 阻塞任务
- 无（这是最后的部署任务）

## 验收标准

### 功能验收
- [ ] Docker容器化配置正确
- [ ] CI/CD流水线正常工作
- [ ] 生产环境部署成功
- [ ] 监控和告警系统正常
- [ ] 日志收集和分析正常
- [ ] 备份和恢复流程正常

### 技术验收
- [ ] 服务启动时间 < 2分钟
- [ ] 系统可用性 ≥ 99.5%
- [ ] 自动扩容机制正常
- [ ] 安全配置符合标准
- [ ] 性能监控覆盖全面

### 质量验收
- [ ] 部署文档完整准确
- [ ] 运维手册详细实用
- [ ] 故障排查指南有效
- [ ] 安全审计通过
- [ ] 性能测试通过

## 测试要求

### 部署测试
```bash
# 测试脚本
#!/bin/bash
# tests/deployment_test.sh

echo "🧪 开始部署测试..."

# 测试Docker构建
docker-compose -f docker-compose.prod.yml build
if [ $? -ne 0 ]; then
    echo "❌ Docker构建失败"
    exit 1
fi

# 测试服务启动
docker-compose -f docker-compose.prod.yml up -d
sleep 60

# 健康检查
if curl -f http://localhost/health; then
    echo "✅ 健康检查通过"
else
    echo "❌ 健康检查失败"
    exit 1
fi

# 功能测试
python tests/integration_test.py

# 清理
docker-compose -f docker-compose.prod.yml down

echo "✅ 部署测试完成"
```

## 预估工作量

- **Docker配置**: 1天
- **CI/CD配置**: 1.5天
- **监控配置**: 1天
- **部署脚本**: 0.5天
- **文档编写**: 1天
- **测试验证**: 1天
- **总计**: 6天

## 关键路径

此任务是整个项目的最后一步，完成后系统即可投入生产使用。

## 交付检查清单

- [ ] Docker生产配置已完成
- [ ] CI/CD流水线已配置
- [ ] 环境变量管理已实现
- [ ] Nginx反向代理已配置
- [ ] 监控和日志系统已部署
- [ ] 部署脚本已编写
- [ ] 运维文档已完成
- [ ] 安全配置已实施
- [ ] 备份策略已制定
- [ ] 部署测试通过
- [ ] 性能测试通过
- [ ] 安全审计通过

## 后续维护

完成此任务后，系统将具备：
- 自动化部署能力
- 完整的监控体系
- 标准化的运维流程
- 可靠的备份恢复机制
- 详细的故障排查指南

这为YouTube分析工具的长期稳定运行提供了坚实的基础。
