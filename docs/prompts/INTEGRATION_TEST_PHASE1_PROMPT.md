# Phase 1 集成测试 - Sub-Session Prompt

## 项目背景

你正在为YouTube视频分析工具执行Phase 1集成测试。此时Task 1(项目设置)、Task 2(后端API框架)、Task 3(前端UI框架)已完成，需要验证基础架构的集成。

## 必读文档

在开始任务前，请仔细阅读以下文档：

### 核心协调文档
- `docs/TASK_COORDINATION.md` - 了解整体项目协调和测试策略
- `docs/ARCHITECTURE_OVERVIEW.md` - 理解系统架构和组件交互
- `docs/API_SPECIFICATIONS.md` - 掌握API接口规范

### 测试相关文档
- `docs/DEVELOPMENT_SETUP.md` - 开发环境配置
- `docs/CODING_STANDARDS.md` - 代码质量标准

### 接口契约
- `docs/contracts/api_framework_contract.md` - API框架接口契约
- `docs/contracts/frontend_framework_contract.md` - 前端框架接口契约
- `docs/contracts/project_config_contract.md` - 项目配置契约

## 测试目标

验证基础架构组件的集成，确保API框架、前端框架和基础配置正确协作。

## 具体测试要求

### 1. API-Frontend集成测试 (真实环境)

```bash
# 启动后端服务
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000

# 启动前端服务  
cd frontend && npm run dev
```

**验证项目**:
- [ ] 前端能成功连接到后端API
- [ ] WebSocket连接建立正常
- [ ] 实时通信功能正常
- [ ] CORS配置正确
- [ ] API响应格式符合规范

### 2. 配置管理集成测试

**验证项目**:
- [ ] 环境变量在前后端正确传递
- [ ] 数据库连接配置正确
- [ ] Redis连接配置正确
- [ ] API密钥配置正确传递
- [ ] 日志配置在各组件中一致

### 3. Docker集成测试

```bash
# 构建和启动容器
docker-compose up --build
```

**验证项目**:
- [ ] 所有容器正常启动
- [ ] 容器间网络通信正常
- [ ] 服务发现机制工作正常
- [ ] 数据卷挂载正确
- [ ] 健康检查通过

### 4. 数据库集成测试

**验证项目**:
- [ ] API与数据库连接成功
- [ ] 基本CRUD操作正常
- [ ] 数据库迁移正确执行
- [ ] 连接池配置正确
- [ ] 事务处理正常

## 测试脚本要求

创建 `tests/integration/phase1/` 目录，包含：

### test_api_frontend_integration.py
```python
import pytest
import requests
import websocket
from selenium import webdriver

class TestAPIFrontendIntegration:
    def test_api_connection(self):
        # 测试前端到API的HTTP连接
        pass
    
    def test_websocket_connection(self):
        # 测试WebSocket实时通信
        pass
    
    def test_cors_configuration(self):
        # 测试跨域配置
        pass
```

### test_configuration_integration.py
```python
import pytest
import os
from backend.config import settings
from frontend.config import config

class TestConfigurationIntegration:
    def test_environment_variables(self):
        # 测试环境变量传递
        pass
    
    def test_database_config(self):
        # 测试数据库配置
        pass
```

### test_docker_integration.py
```python
import pytest
import docker
import requests

class TestDockerIntegration:
    def test_container_startup(self):
        # 测试容器启动
        pass
    
    def test_service_discovery(self):
        # 测试服务发现
        pass
```

## 验收标准

### 功能验收
- [ ] 所有集成测试用例通过
- [ ] 前端能正常访问并显示基础界面
- [ ] API健康检查端点返回正常
- [ ] WebSocket连接稳定
- [ ] Docker容器编排正常运行

### 性能验收
- [ ] API响应时间 < 200ms
- [ ] 前端页面加载时间 < 3s
- [ ] WebSocket连接延迟 < 100ms
- [ ] 容器启动时间 < 30s

### 质量验收
- [ ] 测试覆盖率 > 80%
- [ ] 无严重安全漏洞
- [ ] 日志记录完整
- [ ] 错误处理机制正常

## 测试环境要求

### 真实服务配置
- 使用真实的PostgreSQL/MySQL数据库
- 使用真实的Redis实例
- 配置真实的API密钥（测试环境）
- 使用真实的Docker网络

### 测试数据
- 准备测试用户数据
- 准备基础配置数据
- 确保测试环境隔离

## 交付物

1. **测试报告**: `tests/integration/phase1/PHASE1_TEST_REPORT.md`
2. **测试脚本**: 完整的自动化测试套件
3. **问题清单**: 发现的问题和解决方案
4. **性能报告**: 基础性能指标
5. **部署验证**: Docker环境验证报告

## 后续步骤

Phase 1集成测试通过后：
1. 更新 `docs/PROGRESS_TRACKER.md` 中的Phase 1状态
2. 通知协调者可以开始Phase 2任务
3. 将测试环境保持运行状态供Phase 2使用

## 注意事项

- 所有测试必须使用真实服务，不使用Mock
- 测试失败时必须提供详细的错误日志
- 性能问题必须记录并提供优化建议
- 安全配置必须符合生产环境标准
