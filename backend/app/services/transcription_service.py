import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

import torch
import whisper

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
        self.model: Optional[whisper.Whisper] = None
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
        task: str = "transcribe",
    ) -> TranscriptResult:
        """转录音频文件"""
        try:
            if not os.path.exists(audio_file_path):
                raise ValidationError(f"音频文件不存在: {audio_file_path}")

            self._load_model()
            model = cast(whisper.Whisper, self.model)

            options = {
                "task": task,
                "fp16": torch.cuda.is_available(),
                "verbose": False,
            }

            if language:
                options["language"] = language

            logging.info(f"Starting transcription for: {audio_file_path}")

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: model.transcribe(audio_file_path, **options)
            )

            transcript_result = self._process_transcription_result(result)

            logging.info(
                f"Transcription completed. Language: {transcript_result.language}"
            )

            return transcript_result

        except Exception as e:
            logging.error(f"Transcription failed for {audio_file_path}: {e}")
            raise ExternalServiceError(f"音频转录失败: {e}")

    async def detect_language(self, audio_file_path: str) -> Dict[str, Any]:
        """检测音频语言"""
        try:
            if not os.path.exists(audio_file_path):
                raise ValidationError(f"音频文件不存在: {audio_file_path}")

            self._load_model()
            model = cast(whisper.Whisper, self.model)

            logging.info(f"Detecting language for: {audio_file_path}")

            loop = asyncio.get_event_loop()
            audio = await loop.run_in_executor(
                None, lambda: whisper.load_audio(audio_file_path)
            )

            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(model.device)

            _, probs = await loop.run_in_executor(
                None, lambda: model.detect_language(mel)
            )

            detected_language = max(probs, key=probs.get)
            confidence = probs[detected_language]

            logging.info(
                f"Language detected: {detected_language} (confidence: {confidence:.2f})"
            )

            return {
                "language": detected_language,
                "confidence": confidence,
                "all_probabilities": probs,
            }

        except Exception as e:
            logging.error(f"Language detection failed for {audio_file_path}: {e}")
            raise ExternalServiceError(f"语言检测失败: {e}")

    def _process_transcription_result(
        self, whisper_result: Dict[str, Any]
    ) -> TranscriptResult:
        """处理Whisper转录结果"""
        segments = []

        for segment in whisper_result.get("segments", []):
            transcript_segment = TranscriptSegment(
                start=segment["start"],
                end=segment["end"],
                text=segment["text"].strip(),
                confidence=segment.get("avg_logprob"),
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
            word_count=word_count,
        )

    def validate_audio_file(self, audio_file_path: str) -> bool:
        """验证音频文件"""
        try:
            if not os.path.exists(audio_file_path):
                return False

            file_size = os.path.getsize(audio_file_path)
            if file_size == 0:
                return False

            max_size = settings.max_audio_duration * 1024 * 1024  # Rough estimate
            if file_size > max_size:
                logging.warning(f"Audio file too large: {file_size} bytes")
                return False

            return True

        except Exception as e:
            logging.error(f"Audio file validation failed: {e}")
            return False

    def export_subtitle_file(
        self, transcript_result: TranscriptResult, format: str = "srt"
    ) -> str:
        """导出字幕文件"""
        try:
            if format.lower() == "srt":
                return self._export_srt(transcript_result)
            elif format.lower() == "vtt":
                return self._export_vtt(transcript_result)
            else:
                raise ValidationError(f"不支持的字幕格式: {format}")

        except Exception as e:
            logging.error(f"Subtitle export failed: {e}")
            raise ExternalServiceError(f"字幕导出失败: {e}")

    def _export_srt(self, transcript_result: TranscriptResult) -> str:
        """导出SRT格式字幕"""
        srt_content = []

        for i, segment in enumerate(transcript_result.segments, 1):
            start_time = self._format_timestamp(segment.start)
            end_time = self._format_timestamp(segment.end)

            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(segment.text)
            srt_content.append("")

        return "\n".join(srt_content)

    def _export_vtt(self, transcript_result: TranscriptResult) -> str:
        """导出VTT格式字幕"""
        vtt_content = ["WEBVTT", ""]

        for segment in transcript_result.segments:
            start_time = self._format_timestamp_vtt(segment.start)
            end_time = self._format_timestamp_vtt(segment.end)

            vtt_content.append(f"{start_time} --> {end_time}")
            vtt_content.append(segment.text)
            vtt_content.append("")

        return "\n".join(vtt_content)

    def _format_timestamp(self, seconds: float) -> str:
        """格式化时间戳为SRT格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def _format_timestamp_vtt(self, seconds: float) -> str:
        """格式化时间戳为VTT格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"
