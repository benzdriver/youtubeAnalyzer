import logging
from typing import Optional

from sqlalchemy import select, update

from app.api.v1.websocket import send_progress_update
from app.core.database import AsyncSessionLocal
from app.models.task import AnalysisTask, TaskStatus
from app.services.transcription_service import TranscriptionService
from app.utils.exceptions import ValidationError


async def transcribe_audio_task(
    task_id: str, audio_file_path: str, language: Optional[str] = None
):
    """转录音频文件的Celery任务"""

    async def _transcribe():
        async with AsyncSessionLocal() as db:
            transcription_service = TranscriptionService()

            try:
                result = await db.execute(
                    select(AnalysisTask).where(AnalysisTask.id == task_id)
                )
                task = result.scalar_one_or_none()

                if not task:
                    raise ValidationError(f"Task not found: {task_id}")

                await send_progress_update(
                    task_id, 10, "初始化转录服务", "初始化转录服务"
                )

                if not transcription_service.validate_audio_file(audio_file_path):
                    raise ValidationError(f"音频文件无效: {audio_file_path}")

                await send_progress_update(task_id, 20, "检测音频语言", "语言检测")

                if not language:
                    language_result = await transcription_service.detect_language(
                        audio_file_path
                    )
                    detected_language = language_result["language"]
                    language_confidence = language_result["confidence"]

                    logging.info(
                        f"Detected language: {detected_language} "
                        f"(confidence: {language_confidence:.2f})"
                    )

                    if language_confidence < 0.5:
                        logging.warning(
                            f"Low language detection confidence: {language_confidence}"
                        )
                        detected_language = None
                else:
                    detected_language = language
                    language_confidence = 1.0

                await send_progress_update(task_id, 40, "开始音频转录", "音频转录")

                transcript_result = await transcription_service.transcribe_audio(
                    audio_file_path, language=detected_language
                )

                await send_progress_update(task_id, 80, "处理转录结果", "结果处理")

                transcription_result = {
                    "language": transcript_result.language,
                    "language_confidence": transcript_result.language_confidence,
                    "duration": transcript_result.duration,
                    "word_count": transcript_result.word_count,
                    "full_text": transcript_result.full_text,
                    "segments": [
                        {
                            "start": seg.start,
                            "end": seg.end,
                            "text": seg.text,
                            "confidence": seg.confidence,
                        }
                        for seg in transcript_result.segments
                    ],
                }

                result = await db.execute(
                    select(AnalysisTask).where(AnalysisTask.id == task_id)
                )
                task = result.scalar_one()

                current_result = task.result_data or {}
                current_result["transcription"] = transcription_result

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

                async with AsyncSessionLocal() as db:
                    await db.execute(
                        update(AnalysisTask)
                        .where(AnalysisTask.id == task_id)
                        .values(
                            status=TaskStatus.FAILED,
                            error_message=f"转录失败: {str(e)}",
                        )
                    )
                    await db.commit()

                raise

    return await _transcribe()
