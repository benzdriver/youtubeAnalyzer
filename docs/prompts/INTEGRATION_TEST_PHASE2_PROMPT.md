# Phase 2 集成测试 - Sub-Session Prompt

## 项目背景

你正在为YouTube视频分析工具执行Phase 2集成测试。此时Task 4(YouTube数据提取)、Task 5(音频转录)、Task 6(内容分析)、Task 7(评论分析)已完成，需要验证核心分析流程的集成。

## 必读文档

在开始任务前，请仔细阅读以下文档：

### 核心协调文档
- `docs/TASK_COORDINATION.md` - 了解整体项目协调和测试策略
- `docs/ARCHITECTURE_OVERVIEW.md` - 理解系统架构和数据流
- `docs/API_SPECIFICATIONS.md` - 掌握API接口规范

### 模块相关文档
- `docs/tasks/TASK_04_YOUTUBE_EXTRACTION.md` - YouTube数据提取模块
- `docs/tasks/TASK_05_AUDIO_TRANSCRIPTION.md` - 音频转录模块
- `docs/tasks/TASK_06_CONTENT_ANALYSIS.md` - 内容分析模块
- `docs/tasks/TASK_07_COMMENT_ANALYSIS.md` - 评论分析模块

### 接口契约
- `docs/contracts/youtube_data_contract.md` - YouTube数据接口契约
- `docs/contracts/transcription_contract.md` - 转录服务接口契约
- `docs/contracts/content_analysis_contract.md` - 内容分析接口契约
- `docs/contracts/comment_analysis_contract.md` - 评论分析接口契约

## 测试目标

验证YouTube视频分析的完整数据流，确保从视频提取到最终分析结果的整个流程正确运行。

## 具体测试要求

### 1. 真实YouTube数据流测试

**测试视频集准备**:
```python
TEST_VIDEOS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # 短视频 (3分钟)
    "https://www.youtube.com/watch?v=9bZkp7q19f0",  # 中等视频 (15分钟)
    "https://www.youtube.com/watch?v=fJ9rUzIMcZQ",  # 长视频 (45分钟)
    "https://www.youtube.com/watch?v=jNQXAC9IVRw"   # 包含大量评论的视频
]
```

**验证项目**:
- [ ] YouTube API成功提取视频元数据
- [ ] 音频文件正确下载和处理
- [ ] Whisper转录生成准确文本
- [ ] LLM内容分析生成结构化结果
- [ ] 评论数据正确提取和分析
- [ ] 数据在各模块间正确传递

### 2. 真实任务队列集成测试

```bash
# 启动Redis和Celery
redis-server
celery -A backend.celery worker --loglevel=info
celery -A backend.celery flower  # 监控界面
```

**验证项目**:
- [ ] Celery任务正确排队和执行
- [ ] 任务状态实时更新
- [ ] 任务失败时正确重试
- [ ] 任务进度正确报告
- [ ] 并发任务处理正常

### 3. 真实API集成测试

**验证项目**:
- [ ] YouTube提取API返回正确数据格式
- [ ] 转录API接收和处理音频文件
- [ ] 内容分析API处理转录文本
- [ ] 评论分析API处理评论数据
- [ ] 各API间数据格式一致性
- [ ] API错误处理和响应正确

### 4. 真实错误处理集成测试

**测试场景**:
- [ ] YouTube视频不存在或私有
- [ ] 音频提取失败
- [ ] Whisper服务不可用
- [ ] LLM API配额耗尽
- [ ] 网络连接中断
- [ ] 数据库连接失败

## 测试脚本要求

创建 `tests/integration/phase2/` 目录，包含：

### test_youtube_data_flow.py
```python
import pytest
import asyncio
from backend.services.youtube_extractor import YouTubeExtractor
from backend.services.transcription import TranscriptionService
from backend.services.content_analyzer import ContentAnalyzer
from backend.services.comment_analyzer import CommentAnalyzer

class TestYouTubeDataFlow:
    @pytest.mark.asyncio
    async def test_complete_analysis_flow(self):
        # 测试完整的分析流程
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # 1. YouTube数据提取
        extractor = YouTubeExtractor()
        video_data = await extractor.extract(video_url)
        assert video_data.title
        assert video_data.audio_url
        
        # 2. 音频转录
        transcription_service = TranscriptionService()
        transcript = await transcription_service.transcribe(video_data.audio_url)
        assert transcript.text
        assert transcript.timestamps
        
        # 3. 内容分析
        content_analyzer = ContentAnalyzer()
        content_analysis = await content_analyzer.analyze(transcript.text)
        assert content_analysis.summary
        assert content_analysis.key_points
        
        # 4. 评论分析
        comment_analyzer = CommentAnalyzer()
        comment_analysis = await comment_analyzer.analyze(video_data.comments)
        assert comment_analysis.sentiment_distribution
        assert comment_analysis.host_replies
```

### test_celery_integration.py
```python
import pytest
from celery import Celery
from backend.tasks.analysis_tasks import analyze_video_task

class TestCeleryIntegration:
    def test_video_analysis_task(self):
        # 测试Celery任务执行
        result = analyze_video_task.delay("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result.task_id
        
        # 等待任务完成
        final_result = result.get(timeout=300)  # 5分钟超时
        assert final_result.status == "completed"
        assert final_result.content_analysis
        assert final_result.comment_analysis
```

### test_api_integration.py
```python
import pytest
import requests
from fastapi.testclient import TestClient
from backend.main import app

class TestAPIIntegration:
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_analysis_api_integration(self):
        # 测试分析API集成
        response = self.client.post("/api/v1/analyze", json={
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        })
        assert response.status_code == 200
        task_id = response.json()["task_id"]
        
        # 轮询任务状态
        while True:
            status_response = self.client.get(f"/api/v1/tasks/{task_id}")
            status = status_response.json()["status"]
            if status in ["completed", "failed"]:
                break
            time.sleep(5)
        
        assert status == "completed"
```

## 性能测试要求

### 1. 数据流性能测试
```python
class TestPerformance:
    def test_analysis_performance(self):
        # 短视频 (3分钟) 应在5分钟内完成
        # 中等视频 (15分钟) 应在15分钟内完成
        # 长视频 (45分钟) 应在30分钟内完成
        pass
```

### 2. 并发处理测试
```python
def test_concurrent_analysis(self):
    # 测试同时处理多个视频的能力
    # 验证资源使用和性能影响
    pass
```

## 验收标准

### 功能验收
- [ ] 所有测试视频成功完成分析流程
- [ ] 数据在各模块间正确传递
- [ ] 任务队列正常处理并发请求
- [ ] 错误场景正确处理和恢复
- [ ] API响应格式符合契约规范

### 性能验收
- [ ] 短视频(3分钟)分析时间 < 5分钟
- [ ] 中等视频(15分钟)分析时间 < 15分钟
- [ ] 长视频(45分钟)分析时间 < 30分钟
- [ ] 并发处理3个视频无性能退化
- [ ] 内存使用 < 2GB per worker

### 质量验收
- [ ] 转录准确率 > 90%
- [ ] 内容分析结果结构完整
- [ ] 评论分析覆盖所有评论
- [ ] 错误恢复机制正常工作
- [ ] 日志记录完整详细

## API配额管理

### YouTube API
- 每日配额: 10,000 units
- 测试用量预估: ~100 units per video
- 测试视频数量限制: 50个/天

### OpenAI API
- 使用测试专用API key
- 监控token使用量
- 设置合理的rate limiting

### Whisper API
- 使用本地Whisper模型或测试API
- 监控处理时间和资源使用

## 交付物

1. **测试报告**: `tests/integration/phase2/PHASE2_TEST_REPORT.md`
2. **性能报告**: 详细的性能指标和瓶颈分析
3. **数据流验证**: 完整数据流的验证报告
4. **错误处理报告**: 各种错误场景的处理验证
5. **API使用报告**: API配额使用和优化建议

## 后续步骤

Phase 2集成测试通过后：
1. 更新 `docs/PROGRESS_TRACKER.md` 中的Phase 2状态
2. 通知协调者可以开始Phase 3任务
3. 保留测试数据和环境供Phase 3使用

## 注意事项

- 所有测试使用真实的YouTube视频和API
- 合理管理API配额，避免超限
- 测试数据要包含不同类型和长度的视频
- 性能测试要在真实负载下进行
- 错误处理测试要覆盖所有可能的失败场景
