# Task 1: 项目配置管理 - Sub-Session Prompt

## 项目背景

你正在为一个YouTube视频分析工具建立项目基础配置。这是一个多模块系统，包括：
- FastAPI后端服务
- Next.js前端界面  
- Celery异步任务处理
- PostgreSQL数据库
- Redis缓存
- Docker容器化部署

## 任务目标

建立完整的项目配置管理系统，包括环境变量管理、项目目录结构、Docker配置和依赖管理。

## 具体要求

### 1. 项目目录结构
创建标准化的项目目录结构：
```
youtubeAnalyzer/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── utils/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── store/
│   ├── package.json
│   └── Dockerfile
├── docs/
├── docker-compose.yml
└── .env.example
```

### 2. 环境变量管理
参考 <ref_file file="/home/ubuntu/repos/generic-ai-agent/src/config/env_manager.py" /> 的配置管理模式，创建：

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 应用配置
    app_name: str = "YouTube Analyzer"
    debug: bool = False
    environment: str = "development"
    
    # 数据库配置
    database_url: str
    
    # Redis配置
    redis_url: str = "redis://localhost:6379"
    
    # 外部API配置
    openai_api_key: str
    youtube_api_key: str
    
    # 安全配置
    secret_key: str
    allowed_origins: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### 3. Docker配置
创建开发和生产环境的Docker配置：

#### 开发环境 (docker-compose.yml)
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/youtube_analyzer
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: youtube_analyzer
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    
volumes:
  postgres_data:
```

### 4. 依赖管理

#### 后端依赖 (backend/requirements.txt)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
asyncpg==0.29.0
redis==5.0.1
celery==5.3.4
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
yt-dlp==2023.11.16
openai==1.3.7
whisper==1.1.10
pytest==7.4.3
pytest-asyncio==0.21.1
```

#### 前端依赖 (frontend/package.json)
参考 <ref_file file="/home/ubuntu/repos/thinkforward-devin/frontend/package.json" /> 的依赖模式：
```json
{
  "name": "youtube-analyzer-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest"
  },
  "dependencies": {
    "next": "14.0.3",
    "react": "^18",
    "react-dom": "^18",
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.0.1",
    "postcss": "^8",
    "zustand": "^4.4.6",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "eslint": "^8",
    "eslint-config-next": "14.0.3",
    "jest": "^29.7.0",
    "@testing-library/react": "^13.4.0",
    "@testing-library/jest-dom": "^6.1.4"
  }
}
```

## 代码规范参考

遵循 <ref_file file="/home/ubuntu/repos/youtubeAnalyzer/docs/CODING_STANDARDS.md" /> 中定义的编码标准。

## 验收标准

### 功能验收
- [ ] 项目目录结构完整且符合标准
- [ ] 环境变量管理系统正常工作
- [ ] Docker开发环境可以正常启动
- [ ] 所有服务间通信正常
- [ ] 配置文件模板完整

### 技术验收
- [ ] 服务启动时间 < 30秒
- [ ] 配置热重载正常工作
- [ ] 环境变量验证机制有效
- [ ] Docker镜像构建成功
- [ ] 依赖安装无冲突

### 质量验收
- [ ] 配置文件有详细注释
- [ ] 环境变量有默认值和验证
- [ ] Docker配置优化合理
- [ ] 文档完整准确
- [ ] 代码遵循项目规范

## 测试要求

### 配置测试
```python
# tests/test_config.py
import pytest
from app.core.config import Settings

def test_config_loading():
    """测试配置加载"""
    settings = Settings()
    assert settings.app_name == "YouTube Analyzer"
    assert settings.database_url is not None

def test_environment_validation():
    """测试环境变量验证"""
    # 测试必需环境变量
    with pytest.raises(ValueError):
        Settings(database_url="")
```

### Docker测试
```bash
# 测试Docker构建
docker-compose build
docker-compose up -d

# 健康检查
curl http://localhost:8000/health
curl http://localhost:3000

# 清理
docker-compose down
```

## 交付物清单

- [ ] 完整的项目目录结构
- [ ] 环境变量管理系统 (backend/app/core/config.py)
- [ ] Docker开发环境配置 (docker-compose.yml)
- [ ] 后端Dockerfile (backend/Dockerfile)
- [ ] 前端Dockerfile (frontend/Dockerfile)
- [ ] 依赖文件 (requirements.txt, package.json)
- [ ] 环境变量模板 (.env.example)
- [ ] 配置测试文件
- [ ] 项目README更新

## 关键接口

完成此任务后，需要为后续任务提供：
- 标准化的项目结构
- 可靠的配置管理系统
- 开发环境Docker配置
- 依赖管理机制

## 预估时间

- 开发时间: 1-2天
- 测试时间: 0.5天
- 文档时间: 0.5天
- 总计: 2-3天

## 注意事项

1. 确保所有敏感信息都通过环境变量管理
2. Docker配置要考虑开发和生产环境的差异
3. 依赖版本要固定，避免兼容性问题
4. 配置要有合理的默认值和验证机制
5. 项目结构要为后续模块预留空间

## 完成标准

当你完成此任务时，其他开发者应该能够：
1. 克隆项目后立即运行 `docker-compose up` 启动开发环境
2. 通过修改 `.env` 文件轻松配置不同环境
3. 理解项目结构并知道在哪里添加新功能
4. 运行测试验证配置正确性

这是整个YouTube分析工具的基础，请确保配置的稳定性和可扩展性。
