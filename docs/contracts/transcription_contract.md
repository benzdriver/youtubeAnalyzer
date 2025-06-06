# 音频转录接口契约

**提供方**: TASK_05 (音频转录服务)  
**使用方**: TASK_06 (内容分析模块)  
**版本**: v1.0.0

## 概述

定义音频转录服务的接口规范，包括转录结果数据结构、服务接口和质量保证要求。

## 数据模型定义

### TranscriptSegment 数据结构

```python
from pydantic import BaseModel
from typing import Optional, List

class TranscriptSegment(BaseModel):
    """转录片段"""
    id: int
    start_time: float  # 开始时间（秒）
    end_time: float    # 结束时间（秒）
    text: str          # 转录文本
    confidence: float  # 置信度 (0.0-1.0)
    
    # 可选的词级别信息
    words: Optional[List['WordInfo']] = None
    
    def duration(self) -> float:
        """片段时长"""
        return self.end_time - self.start_time
    
    def __str__(self):
        return f"[{self.start_time:.2f}-{self.end_time:.2f}] {self.text}"

class WordInfo(BaseModel):
    """词级别信息"""
    word: str
    start_time: float
    end_time: float
    confidence: float
```

### TranscriptResult 数据结构

```python
from datetime import datetime
from typing import Dict, Any

class TranscriptResult(BaseModel):
    """完整转录结果"""
    # 基本信息
    audio_file_path: str
    video_id: str
    language: str
    
    # 转录内容
    segments: List[TranscriptSegment]
    full_text: str  # 完整文本
    
    # 质量指标
    overall_confidence: float  # 整体置信度
    word_count: int
    duration: float  # 音频总时长
    
    # 技术信息
    model_name: str  # 使用的模型名称
    model_version: str
    processing_time: float  # 处理时间（秒）
    
    # 时间戳
    created_at: datetime
    
    # 元数据
    metadata: Dict[str, Any] = {}
    
    def get_text_by_time_range(self, start: float, end: float) -> str:
        """获取指定时间范围的文本"""
        relevant_segments = [
            seg for seg in self.segments 
            if seg.start_time < end and seg.end_time > start
        ]
        return " ".join(seg.text for seg in relevant_segments)
    
    def get_low_confidence_segments(self, threshold: float = 0.7) -> List[TranscriptSegment]:
        """获取低置信度片段"""
        return [seg for seg in self.segments if seg.confidence < threshold]
    
    def to_srt_format(self) -> str:
        """转换为SRT字幕格式"""
        srt_content = []
        for i, segment in enumerate(self.segments, 1):
            start_time = self._seconds_to_srt_time(segment.start_time)
            end_time = self._seconds_to_srt_time(segment.end_time)
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(segment.text)
            srt_content.append("")
        
        return "\n".join(srt_content)
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """将秒数转换为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
```

## 服务接口定义

### 转录服务接口

```python
from abc import ABC, abstractmethod
from pathlib import Path

class TranscriptionService(ABC):
    """转录服务接口"""
    
    @abstractmethod
    async def transcribe_audio(self, audio_file_path: str, options: dict = None) -> TranscriptResult:
        """转录音频文件"""
        pass
    
    @abstractmethod
    async def detect_language(self, audio_file_path: str) -> str:
        """检测音频语言"""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        pass
    
    @abstractmethod
    async def validate_audio_file(self, audio_file_path: str) -> bool:
        """验证音频文件"""
        pass
```

### Whisper转录服务实现

```python
import whisper
import torch
from typing import Optional

class WhisperTranscriptionService(TranscriptionService):
    """基于OpenAI Whisper的转录服务"""
    
    def __init__(self, model_size: str = "base", device: str = "auto"):
        self.model_size = model_size
        self.device = self._get_device(device)
        self.model = None
        self._load_model()
    
    def _get_device(self, device: str) -> str:
        """获取计算设备"""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    def _load_model(self):
        """加载Whisper模型"""
        try:
            self.model = whisper.load_model(self.model_size, device=self.device)
        except Exception as e:
            raise TranscriptionError(f"模型加载失败: {e}")
    
    async def transcribe_audio(self, audio_file_path: str, options: dict = None) -> TranscriptResult:
        """转录音频文件"""
        if not await self.validate_audio_file(audio_file_path):
            raise TranscriptionError(f"无效的音频文件: {audio_file_path}")
        
        options = options or {}
        start_time = time.time()
        
        try:
            # 执行转录
            result = self.model.transcribe(
                audio_file_path,
                language=options.get('language'),
                task=options.get('task', 'transcribe'),
                verbose=False,
                word_timestamps=options.get('word_timestamps', True)
            )
            
            processing_time = time.time() - start_time
            
            # 转换为标准格式
            return self._convert_whisper_result(
                result, audio_file_path, processing_time, options
            )
            
        except Exception as e:
            raise TranscriptionError(f"转录失败: {e}")
    
    def _convert_whisper_result(self, whisper_result: dict, audio_file_path: str, 
                              processing_time: float, options: dict) -> TranscriptResult:
        """转换Whisper结果为标准格式"""
        segments = []
        
        for i, segment in enumerate(whisper_result['segments']):
            words = []
            if 'words' in segment:
                words = [
                    WordInfo(
                        word=word['word'],
                        start_time=word['start'],
                        end_time=word['end'],
                        confidence=word.get('confidence', 0.0)
                    )
                    for word in segment['words']
                ]
            
            segments.append(TranscriptSegment(
                id=i,
                start_time=segment['start'],
                end_time=segment['end'],
                text=segment['text'].strip(),
                confidence=segment.get('confidence', 0.0),
                words=words if words else None
            ))
        
        # 计算整体置信度
        overall_confidence = sum(seg.confidence for seg in segments) / len(segments) if segments else 0.0
        
        # 获取音频时长
        duration = whisper_result.get('duration', 0.0)
        if not duration and segments:
            duration = max(seg.end_time for seg in segments)
        
        return TranscriptResult(
            audio_file_path=audio_file_path,
            video_id=options.get('video_id', ''),
            language=whisper_result['language'],
            segments=segments,
            full_text=whisper_result['text'],
            overall_confidence=overall_confidence,
            word_count=len(whisper_result['text'].split()),
            duration=duration,
            model_name="whisper",
            model_version=self.model_size,
            processing_time=processing_time,
            created_at=datetime.utcnow(),
            metadata={
                'device': self.device,
                'options': options
            }
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
            
            return detected_language
            
        except Exception as e:
            raise TranscriptionError(f"语言检测失败: {e}")
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return list(whisper.tokenizer.LANGUAGES.keys())
    
    async def validate_audio_file(self, audio_file_path: str) -> bool:
        """验证音频文件"""
        try:
            path = Path(audio_file_path)
            
            # 检查文件是否存在
            if not path.exists():
                return False
            
            # 检查文件大小
            if path.stat().st_size == 0:
                return False
            
            # 检查文件格式
            supported_formats = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
            if path.suffix.lower() not in supported_formats:
                return False
            
            # 尝试加载音频文件
            whisper.load_audio(audio_file_path, sr=16000)
            
            return True
            
        except Exception:
            return False
```

## 错误处理规范

### 异常类型定义

```python
class TranscriptionError(Exception):
    """转录错误基类"""
    pass

class AudioFileError(TranscriptionError):
    """音频文件错误"""
    pass

class ModelLoadError(TranscriptionError):
    """模型加载错误"""
    pass

class LanguageDetectionError(TranscriptionError):
    """语言检测错误"""
    pass

class QualityError(TranscriptionError):
    """质量不达标错误"""
    pass
```

### 错误响应格式

```json
{
  "error": "transcription_error",
  "error_type": "AudioFileError",
  "message": "音频文件格式不支持",
  "code": "UNSUPPORTED_FORMAT",
  "details": {
    "file_path": "/path/to/audio.xyz",
    "supported_formats": [".wav", ".mp3", ".m4a"],
    "timestamp": "2025-06-06T01:00:00Z"
  }
}
```

## 质量保证要求

### 转录质量指标

```python
class QualityMetrics(BaseModel):
    """质量指标"""
    overall_confidence: float  # 整体置信度
    low_confidence_ratio: float  # 低置信度片段比例
    silence_ratio: float  # 静音比例
    speech_rate: float  # 语速（词/分钟）
    
    def is_acceptable(self) -> bool:
        """判断质量是否可接受"""
        return (
            self.overall_confidence >= 0.7 and
            self.low_confidence_ratio <= 0.3 and
            self.silence_ratio <= 0.5
        )

def calculate_quality_metrics(result: TranscriptResult) -> QualityMetrics:
    """计算质量指标"""
    # 计算低置信度片段比例
    low_confidence_segments = len([s for s in result.segments if s.confidence < 0.7])
    low_confidence_ratio = low_confidence_segments / len(result.segments) if result.segments else 0
    
    # 计算语速
    speech_rate = result.word_count / (result.duration / 60) if result.duration > 0 else 0
    
    # 计算静音比例（简化计算）
    total_speech_time = sum(seg.duration() for seg in result.segments)
    silence_ratio = 1 - (total_speech_time / result.duration) if result.duration > 0 else 0
    
    return QualityMetrics(
        overall_confidence=result.overall_confidence,
        low_confidence_ratio=low_confidence_ratio,
        silence_ratio=silence_ratio,
        speech_rate=speech_rate
    )
```

### 质量改进策略

```python
async def improve_transcription_quality(audio_file_path: str, 
                                      initial_result: TranscriptResult) -> TranscriptResult:
    """改进转录质量"""
    quality_metrics = calculate_quality_metrics(initial_result)
    
    if quality_metrics.is_acceptable():
        return initial_result
    
    # 质量改进策略
    improved_options = {
        'language': initial_result.language,  # 使用检测到的语言
        'task': 'transcribe',
        'word_timestamps': True,
        'condition_on_previous_text': False,  # 减少幻觉
        'compression_ratio_threshold': 2.4,
        'logprob_threshold': -1.0,
        'no_speech_threshold': 0.6
    }
    
    # 如果置信度太低，尝试使用更大的模型
    if quality_metrics.overall_confidence < 0.6:
        service = WhisperTranscriptionService(model_size="large")
        return await service.transcribe_audio(audio_file_path, improved_options)
    
    return initial_result
```

## 性能要求

### 处理时间限制

- **短视频 (< 5分钟)**: < 30秒
- **中等视频 (5-30分钟)**: < 视频时长 × 0.3
- **长视频 (> 30分钟)**: < 视频时长 × 0.5

### 资源使用限制

- **内存使用**: < 2GB per transcription
- **GPU内存**: < 4GB (如果使用GPU)
- **磁盘空间**: 临时文件 < 500MB

## 测试用例

### 单元测试

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_transcribe_audio():
    """测试音频转录"""
    service = WhisperTranscriptionService(model_size="tiny")
    
    with patch.object(service.model, 'transcribe') as mock_transcribe:
        mock_transcribe.return_value = {
            'text': 'Hello world',
            'language': 'en',
            'segments': [{
                'start': 0.0,
                'end': 2.0,
                'text': 'Hello world',
                'confidence': 0.9
            }]
        }
        
        result = await service.transcribe_audio('/path/to/test.wav')
        
        assert result.full_text == 'Hello world'
        assert result.language == 'en'
        assert len(result.segments) == 1
        assert result.overall_confidence == 0.9

@pytest.mark.asyncio
async def test_language_detection():
    """测试语言检测"""
    service = WhisperTranscriptionService()
    
    with patch.object(service.model, 'detect_language') as mock_detect:
        mock_detect.return_value = (None, {'en': 0.9, 'zh': 0.1})
        
        language = await service.detect_language('/path/to/test.wav')
        
        assert language == 'en'
```

### 集成测试

```python
@pytest.mark.integration
async def test_full_transcription_pipeline():
    """测试完整转录流程"""
    service = WhisperTranscriptionService(model_size="tiny")
    
    # 使用真实的测试音频文件
    test_audio_path = "tests/fixtures/test_audio.wav"
    
    # 验证音频文件
    is_valid = await service.validate_audio_file(test_audio_path)
    assert is_valid
    
    # 检测语言
    language = await service.detect_language(test_audio_path)
    assert language in service.get_supported_languages()
    
    # 执行转录
    result = await service.transcribe_audio(test_audio_path, {
        'language': language,
        'word_timestamps': True
    })
    
    # 验证结果
    assert result.language == language
    assert len(result.segments) > 0
    assert result.overall_confidence > 0
    assert result.word_count > 0
    
    # 验证质量
    quality_metrics = calculate_quality_metrics(result)
    assert quality_metrics.overall_confidence > 0.5
```

## 使用示例

### 基本使用

```python
from app.services.transcription import WhisperTranscriptionService

async def transcribe_video_audio(audio_file_path: str, video_id: str) -> TranscriptResult:
    """转录视频音频"""
    service = WhisperTranscriptionService(model_size="base")
    
    try:
        # 检测语言
        language = await service.detect_language(audio_file_path)
        
        # 执行转录
        result = await service.transcribe_audio(audio_file_path, {
            'video_id': video_id,
            'language': language,
            'word_timestamps': True
        })
        
        # 质量检查
        quality_metrics = calculate_quality_metrics(result)
        if not quality_metrics.is_acceptable():
            # 尝试改进质量
            result = await improve_transcription_quality(audio_file_path, result)
        
        return result
        
    except TranscriptionError as e:
        logger.error(f"转录失败: {e}")
        raise
```

### Celery任务集成

```python
from celery import current_task
from app.core.celery_app import celery_app

@celery_app.task(bind=True)
def transcribe_audio_task(self, task_id: str, audio_file_path: str, options: dict):
    """音频转录任务"""
    
    async def _transcribe():
        service = WhisperTranscriptionService(
            model_size=options.get('model_size', 'base')
        )
        
        # 更新进度
        self.update_state(state='PROGRESS', meta={'progress': 10, 'message': '开始转录'})
        
        # 验证音频文件
        if not await service.validate_audio_file(audio_file_path):
            raise TranscriptionError("音频文件验证失败")
        
        self.update_state(state='PROGRESS', meta={'progress': 20, 'message': '检测语言'})
        
        # 检测语言
        language = await service.detect_language(audio_file_path)
        
        self.update_state(state='PROGRESS', meta={'progress': 30, 'message': '执行转录'})
        
        # 执行转录
        result = await service.transcribe_audio(audio_file_path, {
            'language': language,
            'word_timestamps': True,
            **options
        })
        
        self.update_state(state='PROGRESS', meta={'progress': 90, 'message': '质量检查'})
        
        # 质量检查和改进
        quality_metrics = calculate_quality_metrics(result)
        if not quality_metrics.is_acceptable():
            result = await improve_transcription_quality(audio_file_path, result)
        
        self.update_state(state='PROGRESS', meta={'progress': 100, 'message': '转录完成'})
        
        return result.dict()
    
    import asyncio
    return asyncio.run(_transcribe())
```
