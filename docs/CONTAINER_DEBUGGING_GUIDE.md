# Container Debugging Guide

## 概述

本指南提供了YouTube Analyzer项目中Docker容器调试的最佳实践和工具。

## 日志配置

### 结构化日志

所有服务都配置了JSON格式的结构化日志，包含以下字段：
- `timestamp`: ISO格式时间戳
- `service`: 服务名称 (backend, frontend, celery_worker, celery_beat)
- `container_id`: 容器ID (通常是hostname)
- `environment`: 运行环境 (development, production)
- `level`: 日志级别 (DEBUG, INFO, WARNING, ERROR)
- `message`: 日志消息
- `funcName`: 函数名
- `lineno`: 行号

### 日志级别配置

开发环境默认使用DEBUG级别，生产环境建议使用INFO级别：

```yaml
environment:
  - LOG_LEVEL=DEBUG  # 开发环境
  - LOG_LEVEL=INFO   # 生产环境
```

## 容器调试命令

### 查看容器日志

```bash
# 查看特定服务的日志
docker logs youtubeanalyzer-backend-1
docker logs youtubeanalyzer-frontend-1
docker logs youtubeanalyzer-celery_worker-1
docker logs youtubeanalyzer-celery_beat-1

# 实时跟踪日志
docker logs -f youtubeanalyzer-backend-1

# 查看最近的日志条目
docker logs --tail 100 youtubeanalyzer-backend-1

# 查看特定时间范围的日志
docker logs --since "2025-06-06T10:00:00" youtubeanalyzer-backend-1
```

### 容器状态检查

```bash
# 查看所有容器状态
docker-compose ps

# 查看容器详细信息
docker inspect youtubeanalyzer-backend-1

# 查看容器资源使用情况
docker stats

# 查看容器健康检查状态
docker inspect --format='{{.State.Health.Status}}' youtubeanalyzer-backend-1
```

### 进入容器调试

```bash
# 进入运行中的容器
docker exec -it youtubeanalyzer-backend-1 /bin/bash

# 在容器中运行特定命令
docker exec youtubeanalyzer-backend-1 ps aux
docker exec youtubeanalyzer-backend-1 ls -la /app

# 检查容器内的环境变量
docker exec youtubeanalyzer-backend-1 env
```

## 常见问题调试

### 1. 容器启动失败

**症状**: 容器不断重启或启动后立即退出

**调试步骤**:
```bash
# 查看容器退出代码
docker-compose ps

# 查看详细错误日志
docker logs youtubeanalyzer-[service]-1

# 检查容器配置
docker inspect youtubeanalyzer-[service]-1
```

**常见原因**:
- 环境变量配置错误
- 依赖服务未启动
- 端口冲突
- 文件权限问题

### 2. 权限问题

**症状**: `Permission denied` 错误

**调试步骤**:
```bash
# 检查文件权限
docker exec youtubeanalyzer-frontend-1 ls -la /app/.next
docker exec youtubeanalyzer-celery_beat-1 ls -la /tmp/celerybeat-schedule

# 检查用户ID
docker exec youtubeanalyzer-frontend-1 id
docker exec youtubeanalyzer-frontend-1 whoami
```

**解决方案**:
- 使用tmpfs挂载临时文件
- 配置正确的用户权限
- 使用命名卷而非绑定挂载

### 3. 网络连接问题

**症状**: 服务间无法通信

**调试步骤**:
```bash
# 检查网络配置
docker network ls
docker network inspect youtubeanalyzer_youtube_analyzer_network

# 测试服务间连接
docker exec youtubeanalyzer-backend-1 ping postgres
docker exec youtubeanalyzer-backend-1 curl -f http://redis:6379

# 检查端口监听
docker exec youtubeanalyzer-backend-1 netstat -tlnp
```

### 4. 数据库连接问题

**症状**: 数据库连接失败

**调试步骤**:
```bash
# 检查PostgreSQL状态
docker exec youtubeanalyzer-postgres-1 pg_isready -U user -d youtube_analyzer

# 查看数据库日志
docker logs youtubeanalyzer-postgres-1

# 测试数据库连接
docker exec youtubeanalyzer-backend-1 python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://user:password@postgres:5432/youtube_analyzer')
    print('Connected successfully')
    await conn.close()
asyncio.run(test())
"
```

### 5. Redis连接问题

**症状**: Redis缓存或Celery任务失败

**调试步骤**:
```bash
# 检查Redis状态
docker exec youtubeanalyzer-redis-1 redis-cli ping

# 查看Redis日志
docker logs youtubeanalyzer-redis-1

# 检查Redis连接
docker exec youtubeanalyzer-backend-1 python -c "
import redis
r = redis.Redis(host='redis', port=6379, db=0)
print(r.ping())
"
```

## 性能调试

### 监控容器资源

```bash
# 实时监控所有容器资源使用
docker stats

# 监控特定容器
docker stats youtubeanalyzer-backend-1

# 查看容器进程
docker exec youtubeanalyzer-backend-1 top
```

### 分析日志性能

```bash
# 分析API响应时间
docker logs youtubeanalyzer-backend-1 | grep "duration_ms" | tail -20

# 查看数据库查询日志 (如果启用)
docker logs youtubeanalyzer-backend-1 | grep "SQL"
```

## 日志聚合和分析

### 使用jq分析JSON日志

```bash
# 过滤特定级别的日志
docker logs youtubeanalyzer-backend-1 | jq 'select(.levelname == "ERROR")'

# 分析API请求
docker logs youtubeanalyzer-backend-1 | jq 'select(.name == "api.requests")'

# 统计错误类型
docker logs youtubeanalyzer-backend-1 | jq -r 'select(.levelname == "ERROR") | .message' | sort | uniq -c
```

### 导出日志到文件

```bash
# 导出所有服务日志
docker-compose logs > all_services.log

# 导出特定服务日志
docker logs youtubeanalyzer-backend-1 > backend.log 2>&1
```

## 健康检查调试

### 手动执行健康检查

```bash
# Backend健康检查
docker exec youtubeanalyzer-backend-1 curl -f http://localhost:8000/health

# PostgreSQL健康检查
docker exec youtubeanalyzer-postgres-1 pg_isready -U user -d youtube_analyzer

# Redis健康检查
docker exec youtubeanalyzer-redis-1 redis-cli ping
```

### 自定义健康检查

在docker-compose.yml中配置更详细的健康检查：

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## 开发环境调试技巧

### 1. 热重载调试

```bash
# 确保代码变更能触发重载
docker logs -f youtubeanalyzer-backend-1 | grep "Reloading"
```

### 2. 调试模式

```bash
# 启用详细调试输出
docker-compose up --build
```

### 3. 临时修改配置

```bash
# 临时修改环境变量
docker exec youtubeanalyzer-backend-1 env LOG_LEVEL=DEBUG python -m app.main
```

## 生产环境调试注意事项

1. **日志级别**: 生产环境使用INFO或WARNING级别
2. **敏感信息**: 确保不记录密码、API密钥等敏感信息
3. **日志轮转**: 配置适当的日志文件大小和保留策略
4. **监控告警**: 设置关键错误的监控告警

## 故障排除清单

- [ ] 检查所有容器是否正常运行
- [ ] 验证环境变量配置
- [ ] 确认网络连接正常
- [ ] 检查文件权限设置
- [ ] 验证数据库和Redis连接
- [ ] 查看应用程序日志
- [ ] 检查资源使用情况
- [ ] 验证健康检查状态

## 相关文档

- [Docker Compose文档](https://docs.docker.com/compose/)
- [Docker日志驱动](https://docs.docker.com/config/containers/logging/)
- [容器健康检查](https://docs.docker.com/engine/reference/builder/#healthcheck)
