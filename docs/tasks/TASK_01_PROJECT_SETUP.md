# Task 1: 项目配置管理

## 任务概述

建立YouTube分析工具的基础项目配置，包括环境变量管理、项目目录结构、Docker配置和依赖管理。这是所有其他任务的基础，必须首先完成。

## 目标

- 建立标准化的项目目录结构
- 实现环境变量和配置管理系统
- 配置Docker开发和生产环境
- 设置依赖管理和包管理工具
- 建立基础的日志和监控配置

## 可交付成果

### 1. 项目目录结构
```
youtubeAnalyzer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   └── utils/
│   ├── tests/
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── store/
│   │   └── types/
│   ├── public/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── .env.local.example
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── .gitignore
├── .env.example
└── README.md
```

### 2. 配置管理系统
基于 <ref_file file="/home/ubuntu/repos/generic-ai-agent/src/config/env_manager.py" /> 的模式实现：

```python
# backend/app/core/config.py
from pydantic import BaseSettings, Field
from typing import Optional, List
import os

class Settings(BaseSettings):
    # 应用配置
    app_name: str = Field("YouTube Analyzer", env="APP_NAME")
    debug: bool = Field(False, env="DEBUG")
    version: str = Field("1.0.0", env="VERSION")
    
    # 服务器配置
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    
    # 数据库配置
    database_url: str = Field("sqlite:///./app.db", env="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    
    # 外部API配置
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4", env="OPENAI_MODEL")
    youtube_api_key: Optional[str] = Field(None, env="YOUTUBE_API_KEY")
    
    # 安全配置
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS配置
    allowed_origins: List[str] = Field(["*"], env="ALLOWED_ORIGINS")
    
    # 文件存储配置
    storage_path: str = Field("./storage", env="STORAGE_PATH")
    max_file_size: int = Field(2 * 1024 * 1024 * 1024, env="MAX_FILE_SIZE")  # 2GB
    
    # 任务队列配置
    celery_broker_url: str = Field("redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field("redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### 3. Docker配置文件

#### 后端Dockerfile
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 前端Dockerfile
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS base

# 安装依赖阶段
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# 构建阶段
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# 运行阶段
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

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

### 4. 依赖管理配置

#### 后端依赖 (requirements.txt)
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.23
alembic==1.13.0
asyncpg==0.29.0
redis==5.0.1
celery==5.3.4
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.25.2
aiofiles==23.2.1
python-dotenv==1.0.0
openai==1.3.7
yt-dlp==2023.11.16
whisper==1.1.10
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1
```

#### 前端依赖 (package.json)
基于 <ref_file file="/home/ubuntu/repos/thinkforward-devin/frontend/package.json" /> 的模式：

```json
{
  "name": "youtube-analyzer-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "format": "prettier --write .",
    "format:check": "prettier --check ."
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.2.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "zustand": "^4.4.0",
    "@tanstack/react-query": "^5.0.0",
    "zod": "^3.22.0",
    "react-hook-form": "^7.47.0",
    "@hookform/resolvers": "^3.3.0",
    "lucide-react": "^0.292.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0"
  },
  "devDependencies": {
    "eslint": "^8.52.0",
    "eslint-config-next": "^14.0.0",
    "@typescript-eslint/eslint-plugin": "^6.9.0",
    "@typescript-eslint/parser": "^6.9.0",
    "prettier": "^3.0.0",
    "prettier-plugin-tailwindcss": "^0.5.0",
    "@types/node": "^20.8.0"
  }
}
```

### 5. 环境变量模板

#### .env.example
```env
# 应用配置
APP_NAME=YouTube Analyzer
DEBUG=false
VERSION=1.0.0
SECRET_KEY=your-secret-key-here

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./app.db
REDIS_URL=redis://localhost:6379

# 外部API配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
YOUTUBE_API_KEY=your-youtube-api-key

# 文件存储
STORAGE_PATH=./storage
MAX_FILE_SIZE=2147483648

# 任务队列
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# CORS配置
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### 6. Docker Compose配置

#### docker-compose.dev.yml
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
      - DATABASE_URL=sqlite:///./dev.db
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend:/app
      - ./storage:/app/storage
    depends_on:
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    environment:
      - DEBUG=true
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend:/app
      - ./storage:/app/storage
    depends_on:
      - redis
    command: celery -A app.main worker --loglevel=info --concurrency=2

volumes:
  redis_data:
```

## 依赖关系

### 前置条件
- 无（这是第一个任务）

### 阻塞任务
- Task 2: 后端API框架
- Task 3: 前端UI框架
- Task 4: YouTube数据提取
- Task 5: 音频转录服务
- Task 6: 内容分析模块
- Task 7: 评论分析模块

## 验收标准

### 功能验收
- [ ] 项目目录结构完整且符合规范
- [ ] 配置管理系统正常工作，能够读取环境变量
- [ ] Docker容器能够成功构建和运行
- [ ] 开发环境能够通过docker-compose启动
- [ ] 所有依赖包能够正确安装
- [ ] 环境变量验证和错误处理正常工作

### 技术验收
- [ ] 配置类遵循Pydantic BaseSettings模式
- [ ] Docker镜像大小合理（后端 < 1GB，前端 < 500MB）
- [ ] 容器启动时间 < 30秒
- [ ] 配置热重载在开发环境中正常工作
- [ ] 日志输出格式正确且包含必要信息

### 质量验收
- [ ] 代码遵循项目编码规范
- [ ] 所有配置文件有适当的注释
- [ ] 敏感信息不包含在代码仓库中
- [ ] Docker镜像使用非root用户运行
- [ ] 安全扫描通过（无高危漏洞）

## 测试要求

### 单元测试
```python
# tests/test_config.py
import pytest
import os
from app.core.config import Settings

def test_config_loading():
    """测试配置加载"""
    settings = Settings()
    assert settings.app_name == "YouTube Analyzer"
    assert settings.port == 8000

def test_config_validation():
    """测试配置验证"""
    with pytest.raises(ValueError):
        Settings(secret_key="")  # 空密钥应该失败

def test_environment_override():
    """测试环境变量覆盖"""
    os.environ["APP_NAME"] = "Test App"
    settings = Settings()
    assert settings.app_name == "Test App"
    del os.environ["APP_NAME"]
```

### 集成测试
```python
# tests/test_docker.py
import subprocess
import time
import requests

def test_docker_build():
    """测试Docker镜像构建"""
    result = subprocess.run(
        ["docker", "build", "-t", "youtube-analyzer-backend", "./backend"],
        capture_output=True
    )
    assert result.returncode == 0

def test_docker_compose_up():
    """测试Docker Compose启动"""
    subprocess.run(["docker-compose", "-f", "docker-compose.dev.yml", "up", "-d"])
    time.sleep(30)  # 等待服务启动
    
    # 测试后端健康检查
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    
    # 测试前端访问
    response = requests.get("http://localhost:3000")
    assert response.status_code == 200
    
    subprocess.run(["docker-compose", "-f", "docker-compose.dev.yml", "down"])
```

## 实施指南

### 开发步骤
1. **创建项目目录结构**
   - 按照规范创建所有必要的目录
   - 添加空的 `__init__.py` 文件

2. **实现配置管理系统**
   - 参考 <ref_snippet file="/home/ubuntu/repos/generic-ai-agent/src/config/env_manager.py" lines="103-123" /> 的模式
   - 实现配置验证和错误处理

3. **创建Docker配置**
   - 编写多阶段构建的Dockerfile
   - 配置开发和生产环境的差异

4. **设置依赖管理**
   - 创建requirements.txt和package.json
   - 确保版本兼容性

5. **配置开发环境**
   - 设置docker-compose.dev.yml
   - 配置热重载和调试功能

### 最佳实践
- 使用多阶段Docker构建减少镜像大小
- 配置文件使用类型注解和验证
- 敏感信息通过环境变量管理
- 开发和生产环境配置分离
- 使用非root用户运行容器

### 常见问题
1. **配置加载失败**
   - 检查.env文件路径和格式
   - 验证环境变量名称拼写

2. **Docker构建失败**
   - 检查Dockerfile语法
   - 确认基础镜像可用性

3. **依赖安装失败**
   - 检查网络连接
   - 验证包版本兼容性

## 预估工作量

- **开发时间**: 1-2天
- **测试时间**: 0.5天
- **文档时间**: 0.5天
- **总计**: 2-3天

## 关键路径

此任务是关键路径上的第一个任务，必须在其他所有任务之前完成。任何延期都会影响整个项目进度。

## 交付检查清单

- [ ] 所有目录和文件已创建
- [ ] 配置管理系统已实现并测试
- [ ] Docker配置已完成并验证
- [ ] 依赖管理已设置
- [ ] 开发环境可以正常启动
- [ ] 单元测试和集成测试通过
- [ ] 文档已更新
- [ ] 代码已提交到版本控制系统

## 后续任务接口

完成此任务后，为后续任务提供：
- 标准化的项目结构
- 配置管理接口
- Docker化的开发环境
- 依赖管理规范
- 环境变量模板

这些将被Task 2（后端API框架）和Task 3（前端UI框架）直接使用。
