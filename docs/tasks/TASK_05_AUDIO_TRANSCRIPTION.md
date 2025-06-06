# Task 5: 音频转录服务

## 任务概述

实现音频转录服务，将YouTube视频的音频文件转换为带时间戳的文本转录。使用OpenAI Whisper进行高质量的语音识别，支持多语言检测和转录，为后续的内容分析提供准确的文本数据。

## 目标

- 集成OpenAI Whisper进行音频转录
- 实现多语言自动检测和转录
- 生成带时间戳的分段转录
- 优化转录质量和性能
- 实现转录结果的后处理和验证

## 可交付成果

### 1. 转录服务核心实现

```python
# backend/app/services/transcription_service.py
import whisper
import asyncio
import os
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import timedelta

from app.core.config import settings
from app.utils.exceptions import ExternalServiceError, ValidationError

@dataclass
class TranscriptSegment:
    start: float  # 开始时间（秒）
    end: float    # 结束时间（秒）
    text: str     # 文本内容
    confidence: float  # 置信度 (0-1)

@dataclass
class TranscriptResult:
    full_text: str
    segments: List[TranscriptSegment]
    language: str
    confidence: float
    duration: float
    processing_time: float

class TranscriptionService:
    """音频转录服务"""
    
    def __init__(self):
        self.model_name = settings.whisper_model or "base"
        self.device = settings.whisper_device or "cpu"
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载Whisper模型"""
        try:
            logging.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name, device=self.device)
            logging.info("Whisper model loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load Whisper model: {e}")
            raise ExternalServiceError(f"Failed to load transcription model: {e}")
    
    async def transcribe_audio(
        self, 
        audio_file_path: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> TranscriptResult:
        """转录音频文件"""
        
        if not os.path.exists(audio_file_path):
            raise ValidationError(f"Audio file not found: {audio_file_path}")
        
        try:
            import time
            start_time = time.time()
            
            # 准备转录选项
            options = {
                "task": task,  # "transcribe" 或 "translate"
                "verbose": False,
                "word_timestamps": True,
                "fp16": False if self.device == "cpu" else True
            }
            
            if language:
                options["language"] = language
            
            logging.info(f"Starting transcription for: {audio_file_path}")
            
            # 在线程池中运行转录（避免阻塞）
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._transcribe_sync, 
                audio_file_path, 
                options
            )
            
            processing_time = time.time() - start_time
            logging.info(f"Transcription completed in {processing_time:.2f} seconds")
            
            # 处理转录结果
            return self._process_transcription_result(result, processing_time)
            
        except Exception as e:
            logging.error(f"Transcription failed: {e}")
            raise ExternalServiceError(f"Transcription failed: {str(e)}")
    
    def _transcribe_sync(self, audio_file_path: str, options: Dict[str, Any]):
        """同步转录方法（在线程池中运行）"""
        return self.model.transcribe(audio_file_path, **options)
    
    def _process_transcription_result(
        self, 
        raw_result: Dict[str, Any], 
        processing_time: float
    ) -> TranscriptResult:
        """处理原始转录结果"""
        
        # 提取基本信息
        full_text = raw_result.get("text", "").strip()
        language = raw_result.get("language", "unknown")
        
        # 处理分段信息
        segments = []
        total_confidence = 0
        segment_count = 0
        
        for segment in raw_result.get("segments", []):
            # 计算分段置信度
            words = segment.get("words", [])
            if words:
                word_confidences = [
                    word.get("probability", 0.5) 
                    for word in words 
                    if "probability" in word
                ]
                segment_confidence = sum(word_confidences) / len(word_confidences) if word_confidences else 0.5
            else:
                segment_confidence = 0.5
            
            # 清理文本
            text = segment.get("text", "").strip()
            if text:
                segments.append(TranscriptSegment(
                    start=segment.get("start", 0),
                    end=segment.get("end", 0),
                    text=text,
                    confidence=segment_confidence
                ))
                
                total_confidence += segment_confidence
                segment_count += 1
        
        # 计算整体置信度
        overall_confidence = total_confidence / segment_count if segment_count > 0 else 0.5
        
        # 计算总时长
        duration = segments[-1].end if segments else 0
        
        return TranscriptResult(
            full_text=full_text,
            segments=segments,
            language=language,
            confidence=overall_confidence,
            duration=duration,
            processing_time=processing_time
        )
    
    async def detect_language(self, audio_file_path: str) -> str:
        """检测音频语言"""
        try:
            # 加载音频的前30秒进行语言检测
            audio = whisper.load_audio(audio_file_path, sr=16000)
            audio = audio[:30 * 16000]  # 前30秒
            
            # 检测语言
            _, probs = self.model.detect_language(audio)
            detected_language = max(probs, key=probs.get)
            
            logging.info(f"Detected language: {detected_language} (confidence: {probs[detected_language]:.2f})")
            
            return detected_language
            
        except Exception as e:
            logging.warning(f"Language detection failed: {e}")
            return "unknown"
    
    async def transcribe_with_language_detection(
        self, 
        audio_file_path: str
    ) -> TranscriptResult:
        """带语言检测的转录"""
        
        # 首先检测语言
        detected_language = await self.detect_language(audio_file_path)
        
        # 使用检测到的语言进行转录
        return await self.transcribe_audio(
            audio_file_path, 
            language=detected_language if detected_language != "unknown" else None
        )
    
    def format_timestamp(self, seconds: float) -> str:
        """格式化时间戳"""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"
    
    def export_srt(self, transcript: TranscriptResult) -> str:
        """导出SRT字幕格式"""
        srt_content = []
        
        for i, segment in enumerate(transcript.segments, 1):
            start_time = self.format_timestamp(segment.start)
            end_time = self.format_timestamp(segment.end)
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(segment.text)
            srt_content.append("")  # 空行
        
        return "\n".join(srt_content)
    
    def export_vtt(self, transcript: TranscriptResult) -> str:
        """导出WebVTT字幕格式"""
        vtt_content = ["WEBVTT", ""]
        
        for segment in transcript.segments:
            start_time = self.format_timestamp(segment.start)
            end_time = self.format_timestamp(segment.end)
            
            vtt_content.append(f"{start_time} --> {end_time}")
            vtt_content.append(segment.text)
            vtt_content.append("")
        
        return "\n".join(vtt_content)
```

### 2. Celery任务集成

```python
# backend/app/tasks/transcription.py
from celery import current_task
from app.core.celery_app import celery_app
from app.services.transcription_service import TranscriptionService
from app.api.v1.websocket import send_progress_update
from app.models.task import AnalysisTask, TaskStatus
from app.core.database import get_db_session
from sqlalchemy import update, select
import logging

@celery_app.task(bind=True)
def transcribe_audio_task(self, task_id: str, audio_file_path: str, options: dict):
    """音频转录Celery任务"""
    
    async def _transcribe():
        transcription_service = TranscriptionService()
        
        try:
            # 更新任务状态
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
            
            await send_progress_update(task_id, 10, "准备转录模型")
            
            # 检测语言（如果未指定）
            language = options.get('language')
            if not language:
                await send_progress_update(task_id, 20, "检测音频语言")
                language = await transcription_service.detect_language(audio_file_path)
            
            await send_progress_update(task_id, 30, "开始音频转录")
            
            # 执行转录
            transcript = await transcription_service.transcribe_audio(
                audio_file_path,
                language=language if language != "unknown" else None
            )
            
            await send_progress_update(task_id, 80, "后处理转录结果")
            
            # 后处理
            processed_transcript = await transcription_service.post_process_transcript(transcript)
            
            await send_progress_update(task_id, 90, "保存转录结果")
            
            # 生成字幕文件
            srt_content = transcription_service.export_srt(processed_transcript)
            vtt_content = transcription_service.export_vtt(processed_transcript)
            
            # 保存结果
            transcription_result = {
                'transcript': {
                    'full_text': processed_transcript.full_text,
                    'segments': [
                        {
                            'start': seg.start,
                            'end': seg.end,
                            'text': seg.text,
                            'confidence': seg.confidence
                        }
                        for seg in processed_transcript.segments
                    ],
                    'language': processed_transcript.language,
                    'confidence': processed_transcript.confidence,
                    'duration': processed_transcript.duration,
                    'processing_time': processed_transcript.processing_time
                },
                'subtitles': {
                    'srt': srt_content,
                    'vtt': vtt_content
                },
                'metadata': {
                    'model_used': transcription_service.model_name,
                    'device_used': transcription_service.device,
                    'segment_count': len(processed_transcript.segments),
                    'average_confidence': processed_transcript.confidence
                }
            }
            
            # 更新数据库
            async with get_db_session() as db:
                # 获取现有结果
                result = await db.execute(
                    select(AnalysisTask.result_data).where(AnalysisTask.id == task_id)
                )
                existing_data = result.scalar() or {}
                
                # 合并转录结果
                existing_data['transcription'] = transcription_result
                
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(result_data=existing_data)
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

## 依赖关系

### 前置条件
- Task 1: 项目配置管理（必须完成）
- Task 2: 后端API框架（必须完成）
- Task 4: YouTube数据提取（必须完成，需要音频文件）

### 阻塞任务
- Task 6: 内容分析模块（需要转录文本）
- Task 8: 分析编排器（需要转录服务）

## 验收标准

### 功能验收
- [ ] Whisper模型正确加载和初始化
- [ ] 音频转录准确且包含时间戳
- [ ] 多语言检测和转录正常工作
- [ ] 字幕文件导出功能正常
- [ ] 转录后处理提升文本质量
- [ ] Celery任务集成正常工作

### 技术验收
- [ ] 转录准确率 ≥ 90%（清晰音频）
- [ ] 处理速度 < 音频时长的50%
- [ ] 内存使用合理（< 4GB）
- [ ] 支持常见音频格式
- [ ] 错误处理完善

### 质量验收
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 性能测试通过
- [ ] 多语言测试通过
- [ ] 长音频处理稳定
- [ ] 代码遵循项目规范

## 测试要求

### 单元测试
```python
# tests/test_transcription_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.transcription_service import TranscriptionService

@pytest.fixture
def transcription_service():
    with patch('whisper.load_model'):
        return TranscriptionService()

@pytest.mark.asyncio
async def test_transcribe_audio_success(transcription_service):
    """测试音频转录成功"""
    mock_result = {
        'text': 'Hello world',
        'language': 'en',
        'segments': [
            {
                'start': 0.0,
                'end': 2.0,
                'text': 'Hello world',
                'words': [{'probability': 0.95}]
            }
        ]
    }
    
    with patch.object(transcription_service, '_transcribe_sync', return_value=mock_result):
        with patch('os.path.exists', return_value=True):
            result = await transcription_service.transcribe_audio('/fake/path.wav')
            
            assert result.full_text == 'Hello world'
            assert result.language == 'en'
            assert len(result.segments) == 1
            assert result.segments[0].start == 0.0

@pytest.mark.asyncio
async def test_language_detection(transcription_service):
    """测试语言检测"""
    with patch('whisper.load_audio', return_value=Mock()):
        with patch.object(transcription_service.model, 'detect_language', 
                         return_value=(None, {'en': 0.9, 'zh': 0.1})):
            language = await transcription_service.detect_language('/fake/path.wav')
            assert language == 'en'

def test_export_srt(transcription_service):
    """测试SRT导出"""
    from app.services.transcription_service import TranscriptResult, TranscriptSegment
    
    transcript = TranscriptResult(
        full_text="Hello world",
        segments=[
            TranscriptSegment(start=0.0, end=2.0, text="Hello world", confidence=0.95)
        ],
        language="en",
        confidence=0.95,
        duration=2.0,
        processing_time=1.0
    )
    
    srt_content = transcription_service.export_srt(transcript)
    
    assert "1" in srt_content
    assert "00:00:00.000 --> 00:00:02.000" in srt_content
    assert "Hello world" in srt_content
```

## 预估工作量

- **开发时间**: 2-3天
- **测试时间**: 1天
- **性能优化**: 0.5天
- **文档时间**: 0.5天
- **总计**: 4-5天

## 关键路径

此任务在关键路径上，完成后将为Task 6（内容分析）提供必要的转录文本。

## 交付检查清单

- [ ] 转录服务核心功能已实现
- [ ] Whisper模型集成已完成
- [ ] 多语言检测已实现
- [ ] 字幕导出功能已实现
- [ ] Celery任务集成已完成
- [ ] 后处理功能已实现
- [ ] 单元测试和性能测试通过
- [ ] 错误处理已完善
- [ ] 代码已提交并通过CI检查

## 后续任务接口

完成此任务后，为后续任务提供：
- 高质量的转录文本数据
- 带时间戳的分段信息
- 语言检测结果
- 转录置信度评分
- 字幕文件导出功能

这些将被Task 6（内容分析模块）直接使用。
