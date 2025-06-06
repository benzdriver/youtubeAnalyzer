# YouTube分析工具 - 开发环境配置指南

## 概述

本文档提供YouTube分析工具的完整开发环境配置指南，包括依赖安装、环境变量配置、Docker设置和本地测试流程。

## 系统要求

### 硬件要求

- **CPU**: 4核心以上（推荐8核心）
- **内存**: 8GB以上（推荐16GB）
- **存储**: 20GB可用空间
- **GPU**: 可选，用于加速Whisper转录（NVIDIA GPU with CUDA支持）

### 软件要求

- **操作系统**: Ubuntu 20.04+, macOS 12+, Windows 10+ (WSL2)
- **Python**: 3.9-3.12
- **Node.js**: 18.0+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/benzdriver/youtubeAnalyzer.git
cd youtubeAnalyzer
```

### 2. 环境变量配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

### 3. Docker快速启动

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 验证安装

```bash
# 检查后端API
curl http://localhost:8000/health

# 检查前端
curl http://localhost:3000

# 检查数据库连接
docker-compose exec backend python -c "from app.database import test_connection; test_connection()"
```

## 详细配置指南

### 环境变量配置

#### 必需环境变量

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/youtube_analyzer

# Redis配置
REDIS_URL=redis://localhost:6379

# API密钥
OPENAI_API_KEY=your_openai_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here

# 安全配置
SECRET_KEY=your_very_long_secret_key_here_at_least_32_characters

# 前端配置
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

#### 可选环境变量

```bash
# 应用配置
DEBUG=false
ENVIRONMENT=development
LOG_LEVEL=INFO

# 性能配置
CELERY_WORKER_CONCURRENCY=4
WHISPER_MODEL_SIZE=base
MAX_CONCURRENT_ANALYSES=5

# 功能开关
ENABLE_ANALYTICS=true
ENABLE_EXPORT=true
ENABLE_CACHING=true

# 外部服务
SENTRY_DSN=your_sentry_dsn_here
REDIS_CACHE_TTL=3600
```

### API密钥获取指南

#### OpenAI API密钥

1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册/登录账户
3. 导航到 API Keys 页面
4. 点击 "Create new secret key"
5. 复制密钥并保存到 `.env` 文件

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### YouTube Data API密钥

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 YouTube Data API v3
4. 创建凭据 (API Key)
5. 复制API密钥

```bash
YOUTUBE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 本地开发配置

#### 后端开发环境

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发环境

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
# 或使用 yarn
yarn install
# 或使用 pnpm
pnpm install

# 启动开发服务器
npm run dev
# 或
yarn dev
# 或
pnpm dev
```

#### Celery工作进程

```bash
# 在后端目录中启动Celery worker
cd backend
celery -A app.core.celery_app worker --loglevel=info

# 启动Celery监控 (可选)
celery -A app.core.celery_app flower
```

### Docker开发环境

#### Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 后端API服务
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - /app/venv
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/youtube_analyzer
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000

  # Celery工作进程
  celery:
    build: ./backend
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/youtube_analyzer
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    command: celery -A app.core.celery_app worker --loglevel=info

  # PostgreSQL数据库
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: youtube_analyzer
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

#### 开发用Dockerfile

**后端Dockerfile.dev**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 安装开发依赖
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 开发命令
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
```

**前端Dockerfile.dev**:
```dockerfile
FROM node:18-alpine

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 3000

# 开发命令
CMD ["npm", "run", "dev"]
```

### 数据库配置

#### PostgreSQL设置

```bash
# 使用Docker启动PostgreSQL
docker run -d \
  --name youtube-analyzer-postgres \
  -e POSTGRES_DB=youtube_analyzer \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15

# 连接到数据库
psql -h localhost -U postgres -d youtube_analyzer
```

#### 数据库迁移

```bash
# 创建迁移文件
cd backend
alembic revision --autogenerate -m "Initial migration"

# 应用迁移
alembic upgrade head

# 查看迁移历史
alembic history

# 回滚迁移
alembic downgrade -1
```

### 测试环境配置

#### 后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_youtube_extractor.py

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 运行集成测试
pytest tests/integration/

# 运行性能测试
pytest tests/performance/ -v
```

#### 前端测试

```bash
cd frontend

# 运行单元测试
npm test

# 运行测试并监听变化
npm test -- --watch

# 运行E2E测试
npm run test:e2e

# 生成测试覆盖率报告
npm run test:coverage
```

#### 测试数据库配置

```bash
# 创建测试数据库
createdb youtube_analyzer_test

# 设置测试环境变量
export DATABASE_URL=postgresql://postgres:password@localhost:5432/youtube_analyzer_test
export REDIS_URL=redis://localhost:6379/1
```

### 代码质量工具

#### Python代码质量

```bash
cd backend

# 代码格式化
black app/ tests/

# 导入排序
isort app/ tests/

# 代码检查
flake8 app/ tests/

# 类型检查
mypy app/

# 安全检查
bandit -r app/
```

#### JavaScript/TypeScript代码质量

```bash
cd frontend

# 代码检查
npm run lint

# 代码格式化
npm run format

# 类型检查
npm run type-check

# 修复可修复的问题
npm run lint:fix
```

#### 预提交钩子配置

```bash
# 安装pre-commit
pip install pre-commit

# 安装钩子
pre-commit install

# 手动运行所有钩子
pre-commit run --all-files
```

**.pre-commit-config.yaml**:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

### 性能优化配置

#### Whisper模型优化

```bash
# 设置模型大小 (tiny, base, small, medium, large)
export WHISPER_MODEL_SIZE=base

# 启用GPU加速 (需要CUDA)
export WHISPER_DEVICE=cuda

# 设置批处理大小
export WHISPER_BATCH_SIZE=16
```

#### Redis缓存配置

```bash
# Redis配置文件 redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### Celery优化

```bash
# 设置工作进程数
export CELERY_WORKER_CONCURRENCY=4

# 设置任务路由
export CELERY_TASK_ROUTES='{"app.tasks.transcribe": {"queue": "transcription"}}'

# 启动专用队列
celery -A app.core.celery_app worker -Q transcription --loglevel=info
```

### 监控和日志配置

#### 日志配置

```python
# app/core/logging.py
import logging
import sys
from pathlib import Path

def setup_logging():
    """配置应用日志"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # 文件处理器
    log_file = Path("logs/app.log")
    log_file.parent.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
```

#### 健康检查端点

```python
# app/api/v1/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.redis import redis_client

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """系统健康检查"""
    checks = {
        "database": False,
        "redis": False,
        "celery": False
    }
    
    # 数据库检查
    try:
        await db.execute("SELECT 1")
        checks["database"] = True
    except Exception:
        pass
    
    # Redis检查
    try:
        await redis_client.ping()
        checks["redis"] = True
    except Exception:
        pass
    
    # Celery检查
    try:
        from app.core.celery_app import celery_app
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        checks["celery"] = bool(stats)
    except Exception:
        pass
    
    all_healthy = all(checks.values())
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 故障排除

#### 常见问题

**1. Docker容器启动失败**
```bash
# 查看容器日志
docker-compose logs backend

# 重建容器
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**2. 数据库连接失败**
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 重置数据库
docker-compose down -v
docker-compose up -d postgres
```

**3. Whisper模型下载失败**
```bash
# 手动下载模型
python -c "import whisper; whisper.load_model('base')"

# 设置代理 (如果需要)
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

**4. 前端构建失败**
```bash
# 清理node_modules
rm -rf node_modules package-lock.json
npm install

# 检查Node.js版本
node --version  # 应该是18+
```

#### 调试技巧

**后端调试**:
```python
# 启用调试模式
import pdb; pdb.set_trace()

# 或使用ipdb
import ipdb; ipdb.set_trace()

# 远程调试
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

**前端调试**:
```typescript
// 浏览器调试
console.log('Debug info:', data);
debugger;

// React DevTools
// 安装浏览器扩展并在开发者工具中使用
```

### 部署准备

#### 生产环境变量

```bash
# 生产环境配置
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your_production_secret_key

# 数据库配置
DATABASE_URL=postgresql://user:password@prod-db:5432/youtube_analyzer

# 外部服务
SENTRY_DSN=your_production_sentry_dsn
```

#### 构建生产镜像

```bash
# 构建后端生产镜像
docker build -f backend/Dockerfile.prod -t youtube-analyzer-backend:latest ./backend

# 构建前端生产镜像
docker build -f frontend/Dockerfile.prod -t youtube-analyzer-frontend:latest ./frontend
```

## 开发工作流

### 1. 功能开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发和测试
# ... 编写代码 ...

# 3. 运行测试
npm test  # 前端
pytest   # 后端

# 4. 代码检查
npm run lint  # 前端
flake8 app/   # 后端

# 5. 提交代码
git add .
git commit -m "feat: add new feature"

# 6. 推送分支
git push origin feature/new-feature

# 7. 创建Pull Request
```

### 2. 代码审查清单

- [ ] 代码符合项目编码规范
- [ ] 所有测试通过
- [ ] 代码覆盖率满足要求
- [ ] 文档已更新
- [ ] 性能影响已评估
- [ ] 安全性已考虑

### 3. 发布流程

```bash
# 1. 更新版本号
npm version patch  # 或 minor, major

# 2. 更新CHANGELOG
# ... 编辑CHANGELOG.md ...

# 3. 创建发布标签
git tag -a v1.0.0 -m "Release v1.0.0"

# 4. 推送标签
git push origin v1.0.0

# 5. 构建和部署
# ... CI/CD流程自动执行 ...
```

## 支持和帮助

### 文档资源

- [API文档](./API_SPECIFICATIONS.md)
- [架构概览](./ARCHITECTURE_OVERVIEW.md)
- [编码规范](./CODING_STANDARDS.md)
- [任务协调](./TASK_COORDINATION.md)

### 社区支持

- **GitHub Issues**: 报告bug和功能请求
- **Discussions**: 技术讨论和问答
- **Wiki**: 详细文档和教程

### 联系方式

- **项目维护者**: benzdriver
- **邮箱**: benz92124@gmail.com
- **GitHub**: https://github.com/benzdriver/youtubeAnalyzer

---

**最后更新**: 2025-06-06  
**文档版本**: 1.0.0
