# Task 5: 音频转录服务 - Sub-Session Prompt

## 项目背景

你正在为YouTube视频分析工具构建音频转录服务。这个服务需要：
- 使用OpenAI Whisper进行高质量音频转录
- 支持多语言自动检测
- 生成带时间戳的转录文本
- 优化转录质量和性能

## 任务目标

实现完整的音频转录服务，包括Whisper模型集成、语言检测、时间戳生成和转录结果后处理。

## 具体要求

### 1. 转录服务核心实现

```python
# backend/app/services/transcription_service.py
import whisper
import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import torch

from app.core.config import settings
from app.utils.exceptions import ExternalServiceError, ValidationError

@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    confidence: Optional[float] = None

@dataclass
class TranscriptResult:
    language: str
    language_confidence: float
    segments: List[TranscriptSegment]
    full_text: str
    duration: float
    word_count: int

class TranscriptionService:
    """音频转录服务"""
    
    def __init__(self):
        self.model = None
        self.model_size = settings.whisper_model_size or "base"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def _load_model(self):
        """延迟加载Whisper模型"""
        if self.model is None:
            try:
                logging.info(f"Loading Whisper model: {self.model_size}")
                self.model = whisper.load_model(self.model_size, device=self.device)
                logging.info(f"Whisper model loaded on {self.device}")
            except Exception as e:
                logging.error(f"Failed to load Whisper model: {e}")
                raise ExternalServiceError(f"转录模型加载失败: {e}")
    
    async def transcribe_audio(
        self, 
        audio_file_path: str, 
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> TranscriptResult:
        """转录音频文件"""
        try:
            if not os.path.exists(audio_file_path):
                raise ValidationError(f"音频文件不存在: {audio_file_path}")
            
            self._load_model()
            
            options = {
                "task": task,
                "fp16": torch.cuda.is_available(),
                "verbose": False
            }
            
            if language:
                options["language"] = language
            
            logging.info(f"Starting transcription for: {audio_file_path}")
            
            result = self.model.transcribe(audio_file_path, **options)
            transcript_result = self._process_transcription_result(result)
            
            logging.info(f"Transcription completed. Language: {transcript_result.language}")
            
            return transcript_result
            
        except Exception as e:
            logging.error(f"Transcription failed for {audio_file_path}: {e}")
            raise ExternalServiceError(f"音频转录失败: {e}")
    
    def _process_transcription_result(self, whisper_result: Dict[str, Any]) -> TranscriptResult:
        """处理Whisper转录结果"""
        segments = []
        
        for segment in whisper_result.get("segments", []):
            transcript_segment = TranscriptSegment(
                start=segment["start"],
                end=segment["end"],
                text=segment["text"].strip(),
                confidence=segment.get("avg_logprob")
            )
            segments.append(transcript_segment)
        
        duration = segments[-1].end if segments else 0
        full_text = " ".join([seg.text for seg in segments])
        word_count = len(full_text.split())
        
        return TranscriptResult(
            language=whisper_result.get("language", "unknown"),
            language_confidence=whisper_result.get("language_confidence", 0.0),
            segments=segments,
            full_text=full_text,
            duration=duration,
            word_count=word_count
        )
    
    async def detect_language(self, audio_file_path: str) -> Dict[str, Any]:
        """检测音频语言"""
        try:
            self._load_model()
            
            audio = whisper.load_audio(audio_file_path)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            confidence = probs[detected_language]
            
            return {
                "language": detected_language,
                "confidence": confidence,
                "all_probabilities": dict(sorted(probs.items(), key=lambda x: x[1], reverse=True)[:5])
            }
            
        except Exception as e:
            logging.error(f"Language detection failed: {e}")
            raise ExternalServiceError(f"语言检测失败: {e}")

# 全局实例
transcription_service = TranscriptionService()
```

### 2. Celery任务集成

```python
# backend/app/tasks/transcription.py
from celery import current_task
from app.core.celery_app import celery_app
from app.services.transcription_service import transcription_service
from app.api.v1.websocket import send_progress_update
from app.models.task import AnalysisTask, TaskStatus
from app.core.database import get_db_session
from sqlalchemy import update
import logging

@celery_app.task(bind=True)
def transcribe_audio_task(self, task_id: str, audio_file_path: str, options: dict):
    """音频转录Celery任务"""
    
    async def _transcribe():
        try:
            async with get_db_session() as db:
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(
                        status=TaskStatus.PROCESSING,
                        current_step="音频转录"
                    )
                )
                await db.commit()
            
            await send_progress_update(task_id, 10, "加载转录模型")
            
            # 检测语言（如果未指定）
            language = options.get('language')
            if not language:
                await send_progress_update(task_id, 20, "检测音频语言")
                language_info = await transcription_service.detect_language(audio_file_path)
                language = language_info['language']
                logging.info(f"Detected language: {language}")
            
            await send_progress_update(task_id, 30, f"开始转录 ({language})")
            
            # 执行转录
            transcript_result = await transcription_service.transcribe_audio(
                audio_file_path,
                language=language,
                task=options.get('task', 'transcribe')
            )
            
            await send_progress_update(task_id, 90, "保存转录结果")
            
            # 构建结果数据
            transcription_result = {
                'language': transcript_result.language,
                'language_confidence': transcript_result.language_confidence,
                'full_text': transcript_result.full_text,
                'duration': transcript_result.duration,
                'word_count': transcript_result.word_count,
                'segments': [
                    {
                        'start': seg.start,
                        'end': seg.end,
                        'text': seg.text,
                        'confidence': seg.confidence
                    }
                    for seg in transcript_result.segments
                ]
            }
            
            # 保存到数据库
            async with get_db_session() as db:
                result = await db.execute(
                    select(AnalysisTask).where(AnalysisTask.id == task_id)
                )
                task = result.scalar_one()
                
                current_result = task.result_data or {}
                current_result['transcription'] = transcription_result
                
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(result_data=current_result)
                )
                await db.commit()
            
            await send_progress_update(task_id, 100, "转录完成")
            
            return transcription_result
            
        except Exception as e:
            logging.error(f"Transcription failed for task {task_id}: {e}")
            
            async with get_db_session() as db:
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(
                        status=TaskStatus.FAILED,
                        error_message=f"转录失败: {str(e)}"
                    )
                )
                await db.commit()
            
            raise
    
    import asyncio
    return asyncio.run(_transcribe())
```

## 验收标准

### 功能验收
- [ ] Whisper模型正确加载和使用
- [ ] 多语言自动检测准确
- [ ] 转录文本质量高
- [ ] 时间戳精确对应
- [ ] 支持不同音频格式
- [ ] 错误处理机制完善

### 技术验收
- [ ] 转录速度合理（实时倍数 > 0.5x）
- [ ] 内存使用控制在合理范围
- [ ] GPU加速正常工作（如可用）
- [ ] 模型加载时间 < 30秒
- [ ] 长音频处理稳定

### 质量验收
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 多语言测试通过
- [ ] 音质差异测试通过
- [ ] 长时间运行稳定
- [ ] 代码遵循项目规范

## 测试要求

### 单元测试
```python
# tests/test_transcription_service.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.transcription_service import TranscriptionService, TranscriptResult

@pytest.fixture
def transcription_service():
    return TranscriptionService()

@pytest.mark.asyncio
async def test_transcribe_audio(transcription_service):
    """测试音频转录"""
    with patch.object(transcription_service, '_load_model'):
        with patch.object(transcription_service.model, 'transcribe') as mock_transcribe:
            mock_transcribe.return_value = {
                'language': 'en',
                'language_confidence': 0.95,
                'segments': [
                    {
                        'start': 0.0,
                        'end': 5.0,
                        'text': 'Hello world',
                        'avg_logprob': -0.5
                    }
                ]
            }
            
            with patch('os.path.exists', return_value=True):
                result = await transcription_service.transcribe_audio('test.wav')
                
                assert isinstance(result, TranscriptResult)
                assert result.language == 'en'
                assert result.full_text == 'Hello world'
                assert len(result.segments) == 1

@pytest.mark.asyncio
async def test_language_detection(transcription_service):
    """测试语言检测"""
    with patch.object(transcription_service, '_load_model'):
        with patch('whisper.load_audio'):
            with patch('whisper.pad_or_trim'):
                with patch('whisper.log_mel_spectrogram'):
                    with patch.object(transcription_service.model, 'detect_language') as mock_detect:
                        mock_detect.return_value = (None, {'en': 0.9, 'zh': 0.1})
                        
                        result = await transcription_service.detect_language('test.wav')
                        
                        assert result['language'] == 'en'
                        assert result['confidence'] == 0.9
```

## 交付物清单

- [ ] 转录服务核心类 (app/services/transcription_service.py)
- [ ] 数据模型定义 (TranscriptSegment, TranscriptResult)
- [ ] Celery任务实现 (app/tasks/transcription.py)
- [ ] Whisper模型管理功能
- [ ] 语言检测功能
- [ ] 时间戳处理功能
- [ ] 字幕文件导出功能
- [ ] 错误处理和日志记录
- [ ] 单元测试文件
- [ ] 配置文件更新

## 关键接口

完成此任务后，需要为后续任务提供：
- 结构化的转录文本数据
- 带时间戳的文本段落
- 语言检测信息
- 转录质量指标

## 预估时间

- 开发时间: 2-3天
- 测试时间: 1天
- 模型优化: 0.5天
- 文档时间: 0.5天
- 总计: 4-5天

## 注意事项

1. 确保Whisper模型版本兼容性
2. 合理管理GPU内存使用
3. 处理各种音频质量和格式
4. 实现模型的延迟加载和清理
5. 优化长音频的处理性能

这是内容分析的基础数据源，请确保转录质量和准确性。
