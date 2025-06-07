# YouTube Analyzer - 部署指南

## 概述

本指南详细说明了如何在生产环境中部署YouTube分析工具。系统采用Docker容器化部署，包含完整的CI/CD流水线、监控系统和运维工具。

## 系统架构

### 服务组件
- **Nginx**: 反向代理和负载均衡器
- **Frontend**: Next.js前端应用
- **Backend**: FastAPI后端服务
- **Celery Worker**: 异步任务处理器
- **Celery Beat**: 定时任务调度器
- **PostgreSQL**: 主数据库
- **Redis**: 缓存和消息队列

### 网络架构
```
Internet → Nginx (80/443) → Frontend (3000) / Backend (8000)
                          ↓
                    PostgreSQL (5432) + Redis (6379)
                          ↓
                    Celery Workers + Beat
```

## 部署前准备

### 1. 服务器要求

#### 最低配置
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 50GB SSD
- **网络**: 100Mbps带宽

#### 推荐配置
- **CPU**: 8核心
- **内存**: 16GB RAM
- **存储**: 100GB SSD
- **网络**: 1Gbps带宽

### 2. 软件依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 安装Git
sudo apt install git -y

# 安装其他工具
sudo apt install curl wget htop nginx-utils -y
```

### 3. 域名和SSL证书

#### 域名配置
1. 购买域名（例如：youtubeanalyzer.com）
2. 配置DNS A记录指向服务器IP
3. 配置CNAME记录（www.youtubeanalyzer.com → youtubeanalyzer.com）

#### SSL证书获取
```bash
# 安装Certbot
sudo apt install certbot -y

# 获取Let's Encrypt证书
sudo certbot certonly --standalone -d youtubeanalyzer.com -d www.youtubeanalyzer.com

# 证书文件位置
# /etc/letsencrypt/live/youtubeanalyzer.com/fullchain.pem
# /etc/letsencrypt/live/youtubeanalyzer.com/privkey.pem
```

## 部署步骤

### 1. 克隆代码库

```bash
# 创建部署目录
sudo mkdir -p /opt/youtube-analyzer
sudo chown $USER:$USER /opt/youtube-analyzer

# 克隆代码
cd /opt/youtube-analyzer
git clone https://github.com/benzdriver/youtubeAnalyzer.git .
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.prod.example .env.prod

# 编辑环境变量
nano .env.prod
```

#### 必需配置项
```bash
# 应用配置
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-secret-key-minimum-32-characters-long
ALLOWED_ORIGINS=https://youtubeanalyzer.com,https://www.youtubeanalyzer.com

# 数据库配置
DATABASE_URL=postgresql://youtube_user:secure_password@postgres:5432/youtube_analyzer
POSTGRES_DB=youtube_analyzer
POSTGRES_USER=youtube_user
POSTGRES_PASSWORD=secure_database_password_change_this

# Redis配置
REDIS_URL=redis://:redis_password@redis:6379/0
REDIS_PASSWORD=secure_redis_password_change_this

# API密钥
OPENAI_API_KEY=sk-your-production-openai-api-key-here
YOUTUBE_API_KEY=your-production-youtube-api-key-here

# 前端配置
NEXT_PUBLIC_API_URL=https://youtubeanalyzer.com
NEXT_PUBLIC_WS_URL=wss://youtubeanalyzer.com
```

### 3. 配置SSL证书

```bash
# 创建SSL目录
mkdir -p nginx/ssl

# 复制证书文件
sudo cp /etc/letsencrypt/live/youtubeanalyzer.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/youtubeanalyzer.com/privkey.pem nginx/ssl/key.pem
sudo chown $USER:$USER nginx/ssl/*
```

### 4. 执行部署

```bash
# 使用部署脚本
./scripts/deploy.sh

# 或手动部署
docker-compose -f docker-compose.prod.yml up -d
```

### 5. 验证部署

```bash
# 检查服务状态
docker-compose -f docker-compose.prod.yml ps

# 检查健康状态
curl -f https://youtubeanalyzer.com/health

# 检查API
curl -f https://youtubeanalyzer.com/api/v1/health

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

## CI/CD配置

### 1. GitHub Secrets配置

在GitHub仓库设置中添加以下Secrets：

```
PROD_HOST=your-production-server-ip
PROD_USER=deploy
PROD_SSH_KEY=your-ssh-private-key
PROD_SSH_PORT=22
PROD_URL=https://youtubeanalyzer.com
SLACK_WEBHOOK=your-slack-webhook-url-for-notifications
```

### 2. SSH密钥配置

```bash
# 在服务器上创建部署用户
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG docker deploy

# 配置SSH密钥
sudo -u deploy mkdir -p /home/deploy/.ssh
sudo -u deploy ssh-keygen -t rsa -b 4096 -f /home/deploy/.ssh/id_rsa

# 将公钥添加到authorized_keys
sudo -u deploy cp /home/deploy/.ssh/id_rsa.pub /home/deploy/.ssh/authorized_keys
sudo -u deploy chmod 600 /home/deploy/.ssh/authorized_keys

# 将私钥添加到GitHub Secrets (PROD_SSH_KEY)
sudo cat /home/deploy/.ssh/id_rsa
```

### 3. 自动部署流程

1. 代码推送到main分支
2. GitHub Actions触发CI/CD流水线
3. 运行测试和安全扫描
4. 构建Docker镜像
5. 部署到生产服务器
6. 执行健康检查
7. 发送通知

## 监控和日志

### 1. 系统监控

#### Prometheus指标
- HTTP请求数量和延迟
- 活跃任务数量
- 数据库连接数
- 内存和CPU使用率

#### 访问指标端点
```bash
curl https://youtubeanalyzer.com/metrics
```

### 2. 日志管理

#### 日志位置
```bash
# 应用日志
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs celery_worker

# 系统日志
/opt/youtube-analyzer/logs/
```

#### 日志轮转
```bash
# 配置logrotate
sudo nano /etc/logrotate.d/youtube-analyzer

/opt/youtube-analyzer/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 deploy deploy
    postrotate
        docker-compose -f /opt/youtube-analyzer/docker-compose.prod.yml restart backend celery_worker
    endscript
}
```

### 3. 告警配置

#### 健康检查脚本
```bash
#!/bin/bash
# /opt/youtube-analyzer/scripts/health_check.sh

HEALTH_URL="https://youtubeanalyzer.com/health"
SLACK_WEBHOOK="your-slack-webhook-url"

if ! curl -f --max-time 10 "$HEALTH_URL" >/dev/null 2>&1; then
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"🚨 YouTube Analyzer health check failed!"}' \
        "$SLACK_WEBHOOK"
fi
```

#### Crontab配置
```bash
# 每5分钟检查一次
*/5 * * * * /opt/youtube-analyzer/scripts/health_check.sh
```

## 备份和恢复

### 1. 数据库备份

#### 自动备份脚本
```bash
#!/bin/bash
# /opt/youtube-analyzer/scripts/backup.sh

BACKUP_DIR="/opt/youtube-analyzer/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# 数据库备份
docker-compose -f /opt/youtube-analyzer/docker-compose.prod.yml exec -T postgres \
    pg_dump -U youtube_user youtube_analyzer > "$BACKUP_DIR/db_backup_$DATE.sql"

# 压缩备份
gzip "$BACKUP_DIR/db_backup_$DATE.sql"

# 清理旧备份（保留30天）
find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -mtime +30 -delete
```

#### 定时备份
```bash
# 每天凌晨2点备份
0 2 * * * /opt/youtube-analyzer/scripts/backup.sh
```

### 2. 数据恢复

```bash
# 停止服务
docker-compose -f docker-compose.prod.yml down

# 恢复数据库
gunzip -c /opt/youtube-analyzer/backups/db_backup_YYYYMMDD_HHMMSS.sql.gz | \
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U youtube_user -d youtube_analyzer

# 重启服务
docker-compose -f docker-compose.prod.yml up -d
```

## 性能优化

### 1. 数据库优化

```sql
-- 创建索引
CREATE INDEX CONCURRENTLY idx_analysis_tasks_status ON analysis_tasks(status);
CREATE INDEX CONCURRENTLY idx_analysis_tasks_created_at ON analysis_tasks(created_at);

-- 配置参数
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

### 2. Redis优化

```bash
# 在docker-compose.prod.yml中配置
command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD} --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### 3. Nginx优化

```nginx
# 在nginx.conf中已包含的优化配置
worker_connections 1024;
gzip on;
keepalive_timeout 65;
client_max_body_size 100M;
```

## 安全配置

### 1. 防火墙设置

```bash
# 安装ufw
sudo apt install ufw -y

# 配置防火墙规则
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable
```

### 2. 系统安全

```bash
# 禁用root登录
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# 配置fail2ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. 容器安全

- 使用非root用户运行容器
- 定期更新基础镜像
- 扫描镜像漏洞
- 限制容器资源使用

## 故障排查

### 1. 常见问题

#### 服务无法启动
```bash
# 检查Docker状态
sudo systemctl status docker

# 检查容器日志
docker-compose -f docker-compose.prod.yml logs

# 检查端口占用
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

#### 数据库连接失败
```bash
# 检查数据库状态
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# 检查连接字符串
docker-compose -f docker-compose.prod.yml exec backend env | grep DATABASE_URL
```

#### SSL证书问题
```bash
# 检查证书有效期
openssl x509 -in nginx/ssl/cert.pem -text -noout | grep "Not After"

# 更新证书
sudo certbot renew
```

### 2. 性能问题

#### 高CPU使用率
```bash
# 查看容器资源使用
docker stats

# 查看系统负载
htop
```

#### 高内存使用率
```bash
# 查看内存使用
free -h

# 查看容器内存使用
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### 3. 日志分析

```bash
# 查看错误日志
docker-compose -f docker-compose.prod.yml logs | grep ERROR

# 查看访问日志
docker-compose -f docker-compose.prod.yml logs nginx | grep "GET\|POST"

# 实时监控日志
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

## 维护操作

### 1. 系统更新

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 更新Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 重启服务
sudo reboot
```

### 2. 应用更新

```bash
# 使用部署脚本更新
./scripts/deploy.sh

# 或手动更新
git pull origin main
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### 3. 数据库维护

```bash
# 数据库清理
docker-compose -f docker-compose.prod.yml exec postgres psql -U youtube_user -d youtube_analyzer -c "VACUUM ANALYZE;"

# 重建索引
docker-compose -f docker-compose.prod.yml exec postgres psql -U youtube_user -d youtube_analyzer -c "REINDEX DATABASE youtube_analyzer;"
```

## 扩容指南

### 1. 垂直扩容

```bash
# 增加服务器资源后，调整容器资源限制
# 在docker-compose.prod.yml中修改：
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
```

### 2. 水平扩容

```bash
# 增加Worker实例
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=4

# 使用负载均衡器分发请求
# 配置多个后端实例
```

### 3. 数据库扩容

```bash
# 配置读写分离
# 配置数据库集群
# 使用连接池
```

## 联系支持

如果遇到部署问题，请：

1. 查看本文档的故障排查部分
2. 检查GitHub Issues
3. 联系技术支持团队

---

**注意**: 本指南假设您具备基本的Linux系统管理和Docker使用经验。在生产环境部署前，请务必在测试环境中验证所有配置。
