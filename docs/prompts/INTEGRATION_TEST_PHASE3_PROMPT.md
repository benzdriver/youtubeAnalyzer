# Phase 3 系统测试 - Sub-Session Prompt

## 项目背景

你正在为YouTube视频分析工具执行Phase 3系统测试。此时Task 8(分析编排器)、Task 9(结果展示)、Task 10(部署配置)已完成，需要验证完整系统的端到端功能。

## 必读文档

在开始任务前，请仔细阅读以下文档：

### 核心协调文档
- `docs/TASK_COORDINATION.md` - 了解整体项目协调和测试策略
- `docs/ARCHITECTURE_OVERVIEW.md` - 理解完整系统架构
- `docs/API_SPECIFICATIONS.md` - 掌握所有API接口规范

### 系统集成文档
- `docs/tasks/TASK_08_ANALYSIS_ORCHESTRATOR.md` - 分析编排器
- `docs/tasks/TASK_09_RESULT_DISPLAY.md` - 结果展示界面
- `docs/tasks/TASK_10_DEPLOYMENT.md` - 部署配置

### 接口契约
- `docs/contracts/orchestrator_contract.md` - 编排器接口契约
- `docs/contracts/result_display_contract.md` - 结果展示接口契约

### 测试基础
- `tests/integration/phase1/PHASE1_TEST_REPORT.md` - Phase 1测试结果
- `tests/integration/phase2/PHASE2_TEST_REPORT.md` - Phase 2测试结果

## 测试目标

验证完整YouTube视频分析系统的端到端功能，确保用户可以从输入YouTube链接到获得完整分析结果的整个流程正常运行。

## 具体测试要求

### 1. 端到端用户流程测试

**完整用户场景**:
```
用户输入 → 视频分析 → 实时进度 → 结果展示 → 导出功能
```

**测试步骤**:
1. 用户在前端界面输入YouTube链接
2. 系统开始分析并显示实时进度
3. 分析完成后展示结构化结果
4. 用户可以查看、筛选、导出结果

**验证项目**:
- [ ] 前端界面响应正常
- [ ] YouTube链接验证正确
- [ ] 分析任务正确创建和执行
- [ ] 实时进度更新准确
- [ ] 结果展示完整和美观
- [ ] 导出功能正常工作
- [ ] 错误处理用户友好

### 2. 真实性能测试

**负载测试场景**:
```python
PERFORMANCE_TEST_SCENARIOS = [
    {
        "name": "单用户测试",
        "concurrent_users": 1,
        "videos_per_user": 5,
        "video_types": ["short", "medium", "long"]
    },
    {
        "name": "多用户测试", 
        "concurrent_users": 10,
        "videos_per_user": 2,
        "video_types": ["short", "medium"]
    },
    {
        "name": "高负载测试",
        "concurrent_users": 50,
        "videos_per_user": 1,
        "video_types": ["short"]
    }
]
```

**验证项目**:
- [ ] 系统在负载下保持稳定
- [ ] 响应时间在可接受范围内
- [ ] 资源使用合理
- [ ] 无内存泄漏
- [ ] 数据库连接池正常
- [ ] 任务队列不积压

### 3. 真实部署验证

**Docker生产环境测试**:
```bash
# 生产环境部署
docker-compose -f docker-compose.prod.yml up -d

# 健康检查
curl http://localhost/health
curl http://localhost/api/v1/health
```

**验证项目**:
- [ ] 所有容器正常启动
- [ ] 服务发现和负载均衡正常
- [ ] 数据持久化正确
- [ ] 日志聚合正常
- [ ] 监控指标收集正常
- [ ] 备份和恢复机制正常

### 4. 真实监控验证

**监控系统测试**:
- [ ] Prometheus指标收集正常
- [ ] Grafana仪表板显示正确
- [ ] 日志聚合到ELK/Loki
- [ ] 告警规则正确触发
- [ ] 性能指标准确
- [ ] 错误率监控正常

## 测试脚本要求

创建 `tests/system/phase3/` 目录，包含：

### test_end_to_end_flow.py
```python
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestEndToEndFlow:
    def setup_method(self):
        self.driver = webdriver.Chrome()
        self.driver.get("http://localhost:3000")
    
    def teardown_method(self):
        self.driver.quit()
    
    def test_complete_analysis_flow(self):
        # 1. 输入YouTube链接
        url_input = self.driver.find_element(By.ID, "youtube-url-input")
        url_input.send_keys("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        # 2. 点击分析按钮
        analyze_button = self.driver.find_element(By.ID, "analyze-button")
        analyze_button.click()
        
        # 3. 等待进度显示
        progress_bar = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "progress-bar"))
        )
        assert progress_bar.is_displayed()
        
        # 4. 等待分析完成
        results_section = WebDriverWait(self.driver, 300).until(
            EC.presence_of_element_located((By.ID, "analysis-results"))
        )
        assert results_section.is_displayed()
        
        # 5. 验证结果内容
        summary = self.driver.find_element(By.ID, "content-summary")
        assert summary.text
        
        key_points = self.driver.find_element(By.ID, "key-points")
        assert key_points.text
        
        comments_analysis = self.driver.find_element(By.ID, "comments-analysis")
        assert comments_analysis.text
        
        # 6. 测试导出功能
        export_button = self.driver.find_element(By.ID, "export-button")
        export_button.click()
        
        # 验证下载开始
        WebDriverWait(self.driver, 10).until(
            lambda driver: len(driver.window_handles) > 1 or 
            driver.execute_script("return document.readyState") == "complete"
        )
```

### test_performance_load.py
```python
import pytest
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

class TestPerformanceLoad:
    @pytest.mark.asyncio
    async def test_concurrent_analysis(self):
        """测试并发分析性能"""
        async def analyze_video(session, video_url):
            start_time = time.time()
            async with session.post("/api/v1/analyze", json={"video_url": video_url}) as resp:
                task_data = await resp.json()
                task_id = task_data["task_id"]
            
            # 轮询任务状态
            while True:
                async with session.get(f"/api/v1/tasks/{task_id}") as resp:
                    status_data = await resp.json()
                    if status_data["status"] in ["completed", "failed"]:
                        break
                await asyncio.sleep(5)
            
            end_time = time.time()
            return end_time - start_time, status_data["status"]
        
        # 并发测试
        async with aiohttp.ClientSession("http://localhost:8000") as session:
            tasks = []
            test_videos = [
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "https://www.youtube.com/watch?v=9bZkp7q19f0",
                "https://www.youtube.com/watch?v=fJ9rUzIMcZQ"
            ] * 10  # 30个并发任务
            
            for video_url in test_videos:
                task = analyze_video(session, video_url)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # 验证结果
            completion_times = [r[0] for r in results]
            statuses = [r[1] for r in results]
            
            assert all(status == "completed" for status in statuses)
            assert max(completion_times) < 600  # 10分钟内完成
            assert sum(completion_times) / len(completion_times) < 300  # 平均5分钟
```

### test_deployment_verification.py
```python
import pytest
import docker
import requests
import time

class TestDeploymentVerification:
    def setup_method(self):
        self.docker_client = docker.from_env()
    
    def test_container_health(self):
        """测试容器健康状态"""
        containers = self.docker_client.containers.list()
        
        required_services = [
            "youtube-analyzer-frontend",
            "youtube-analyzer-backend", 
            "youtube-analyzer-redis",
            "youtube-analyzer-postgres",
            "youtube-analyzer-celery"
        ]
        
        running_services = [c.name for c in containers if c.status == "running"]
        
        for service in required_services:
            assert service in running_services
    
    def test_service_endpoints(self):
        """测试服务端点"""
        # 前端健康检查
        frontend_response = requests.get("http://localhost:3000")
        assert frontend_response.status_code == 200
        
        # 后端健康检查
        backend_response = requests.get("http://localhost:8000/health")
        assert backend_response.status_code == 200
        
        # API健康检查
        api_response = requests.get("http://localhost:8000/api/v1/health")
        assert api_response.status_code == 200
        assert api_response.json()["status"] == "healthy"
```

## 用户验收测试

### 1. 功能验收清单
- [ ] 用户可以输入任意有效的YouTube链接
- [ ] 系统显示清晰的分析进度
- [ ] 分析结果结构化且易于理解
- [ ] 评论分析突出显示主播回复
- [ ] 结果可以导出为PDF/JSON格式
- [ ] 错误信息用户友好
- [ ] 界面响应速度快

### 2. 用户体验验收
- [ ] 界面设计美观直观
- [ ] 操作流程简单明了
- [ ] 加载状态清晰可见
- [ ] 错误恢复机制友好
- [ ] 移动端适配良好
- [ ] 无障碍访问支持

### 3. 性能验收标准
- [ ] 页面首次加载 < 3秒
- [ ] 短视频分析 < 5分钟
- [ ] 中等视频分析 < 15分钟
- [ ] 长视频分析 < 30分钟
- [ ] 并发10用户无性能退化
- [ ] 系统可用性 > 99%

## 监控和告警验证

### 1. 关键指标监控
```yaml
metrics_to_verify:
  - name: "API响应时间"
    threshold: "< 200ms"
  - name: "任务完成率"
    threshold: "> 95%"
  - name: "错误率"
    threshold: "< 1%"
  - name: "系统资源使用"
    threshold: "< 80%"
  - name: "数据库连接数"
    threshold: "< 100"
```

### 2. 告警规则验证
- [ ] API响应时间超过阈值时告警
- [ ] 任务失败率过高时告警
- [ ] 系统资源使用过高时告警
- [ ] 服务不可用时告警
- [ ] 数据库连接异常时告警

## 交付物

1. **系统测试报告**: `tests/system/phase3/PHASE3_SYSTEM_TEST_REPORT.md`
2. **性能测试报告**: 详细的负载测试和性能分析
3. **用户验收报告**: 用户体验和功能验收结果
4. **部署验证报告**: 生产环境部署验证
5. **监控验证报告**: 监控系统和告警验证
6. **最终发布清单**: 系统发布前的最终检查清单

## 发布准备

系统测试通过后的发布准备：
1. 更新 `docs/PROGRESS_TRACKER.md` 标记项目完成
2. 创建发布标签和版本说明
3. 准备用户文档和使用指南
4. 配置生产环境监控
5. 准备运维手册和故障排除指南

## 注意事项

- 所有测试在真实生产环境配置下进行
- 性能测试要模拟真实用户行为
- 用户验收测试要邀请真实用户参与
- 监控验证要覆盖所有关键业务指标
- 发布前要进行完整的回归测试
