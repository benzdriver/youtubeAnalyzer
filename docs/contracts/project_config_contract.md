# 项目配置接口契约

**提供方**: TASK_01 (项目配置管理)  
**使用方**: TASK_02 (后端API框架), TASK_03 (前端UI框架)  
**版本**: v1.0.0

## 概述

定义项目配置管理系统的接口规范，包括环境变量管理、项目结构、Docker配置和依赖管理。

## 目录结构契约

### 标准项目结构
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

### 必需文件清单
- `backend/app/core/config.py` - 配置管理模块
- `backend/requirements.txt` - Python依赖
- `frontend/package.json` - Node.js依赖
- `docker-compose.yml` - 开发环境配置
- `.env.example` - 环境变量模板

## 配置管理接口

### Python配置类 (backend/app/core/config.py)

```python
from pydantic_settings import BaseSettings
from typing import Optional, List

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
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 全局配置实例
settings = Settings()
```

### TypeScript配置接口 (frontend/src/config/index.ts)

```typescript
interface AppConfig {
  apiUrl: string;
  wsUrl: string;
  environment: 'development' | 'production' | 'test';
  features: {
    enableAnalytics: boolean;
    enableExport: boolean;
  };
}

export const config: AppConfig = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  environment: (process.env.NODE_ENV as any) || 'development',
  features: {
    enableAnalytics: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',
    enableExport: process.env.NEXT_PUBLIC_ENABLE_EXPORT !== 'false'
  }
};
```

## 环境变量契约

### 必需环境变量

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/youtube_analyzer

# Redis配置
REDIS_URL=redis://localhost:6379

# API密钥
OPENAI_API_KEY=your_openai_api_key
YOUTUBE_API_KEY=your_youtube_api_key

# 安全配置
SECRET_KEY=your_very_long_secret_key

# 前端配置
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 可选环境变量

```bash
# 应用配置
DEBUG=false
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# 功能开关
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_EXPORT=true

# 性能配置
CELERY_WORKER_CONCURRENCY=4
WHISPER_MODEL_SIZE=base
```

## Docker配置契约

### 开发环境服务定义

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/youtube_analyzer
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: youtube_analyzer
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
  
  redis:
    image: redis:7-alpine
```

### 健康检查接口

```python
# backend/app/api/v1/health.py
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.environment,
        "version": "1.0.0"
    }
```

## 依赖管理契约

### Python依赖 (backend/requirements.txt)

```txt
# 核心框架
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# 数据库
sqlalchemy==2.0.23
alembic==1.12.1
asyncpg==0.29.0

# 任务队列
celery==5.3.4
redis==5.0.1

# 外部服务
yt-dlp==2023.11.16
openai==1.3.7
whisper==1.1.10

# 测试
pytest==7.4.3
pytest-asyncio==0.21.1
```

### Node.js依赖 (frontend/package.json)

```json
{
  "dependencies": {
    "next": "14.0.3",
    "react": "^18",
    "react-dom": "^18",
    "typescript": "^5",
    "tailwindcss": "^3.3.0",
    "zustand": "^4.4.6",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "eslint": "^8",
    "eslint-config-next": "14.0.3",
    "jest": "^29.7.0",
    "@testing-library/react": "^13.4.0"
  }
}
```

## 验证规则

### 配置验证

```python
# 配置验证示例
def validate_config():
    """验证配置完整性"""
    required_vars = [
        'DATABASE_URL',
        'REDIS_URL', 
        'OPENAI_API_KEY',
        'YOUTUBE_API_KEY',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var.lower(), None):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
```

### 服务连接验证

```python
async def validate_services():
    """验证外部服务连接"""
    # 数据库连接测试
    try:
        await database.execute("SELECT 1")
    except Exception as e:
        raise ConnectionError(f"Database connection failed: {e}")
    
    # Redis连接测试
    try:
        await redis.ping()
    except Exception as e:
        raise ConnectionError(f"Redis connection failed: {e}")
```

## 错误处理

### 配置错误类型

```python
class ConfigurationError(Exception):
    """配置相关错误"""
    pass

class MissingEnvironmentVariable(ConfigurationError):
    """缺少环境变量"""
    pass

class InvalidConfigurationValue(ConfigurationError):
    """无效配置值"""
    pass
```

### 错误响应格式

```json
{
  "error": "configuration_error",
  "message": "Missing required environment variable: DATABASE_URL",
  "code": "MISSING_ENV_VAR",
  "details": {
    "variable": "DATABASE_URL",
    "required": true
  }
}
```

## 测试用例

### 配置加载测试

```python
def test_config_loading():
    """测试配置加载"""
    # 设置测试环境变量
    os.environ.update({
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
        'REDIS_URL': 'redis://localhost:6379',
        'OPENAI_API_KEY': 'test-key',
        'YOUTUBE_API_KEY': 'test-key',
        'SECRET_KEY': 'test-secret'
    })
    
    settings = Settings()
    assert settings.database_url == 'postgresql://test:test@localhost:5432/test'
    assert settings.app_name == 'YouTube Analyzer'
```

### Docker环境测试

```bash
# 测试Docker环境启动
docker-compose up -d
sleep 10

# 健康检查
curl -f http://localhost:8000/health
curl -f http://localhost:3000

# 清理
docker-compose down
```

## 向后兼容性

### 版本迁移指南

- **v1.0.0 → v1.1.0**: 新增可选配置项，保持现有配置不变
- **v1.1.0 → v2.0.0**: 重大变更需要更新配置文件

### 废弃策略

1. 标记废弃配置项
2. 提供迁移指南
3. 保留一个版本周期
4. 完全移除

## 使用示例

### 后端使用配置

```python
from app.core.config import settings

# 使用数据库配置
engine = create_async_engine(settings.database_url)

# 使用API密钥
openai.api_key = settings.openai_api_key
```

### 前端使用配置

```typescript
import { config } from '@/config';

// 使用API URL
const response = await fetch(`${config.apiUrl}/api/v1/analyze`);

// 使用功能开关
if (config.features.enableAnalytics) {
  // 启用分析功能
}
```
