import os
import logging
import shutil
from typing import List, Optional
from pathlib import Path

from app.core.config import settings


class StorageManager:
    """文件存储管理器"""
    
    def __init__(self):
        self.storage_path = Path(settings.storage_path)
        self.audio_dir = self.storage_path / "audio"
        self.upload_dir = Path(settings.upload_dir)
        
        self.ensure_directories()
    
    def ensure_directories(self) -> None:
        """确保所有必要的目录存在"""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self.audio_dir.mkdir(parents=True, exist_ok=True)
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Storage directories ensured: {self.storage_path}, {self.audio_dir}, {self.upload_dir}")
        except Exception as e:
            logging.error(f"Failed to create storage directories: {e}")
            raise
    
    def get_audio_file_path(self, video_id: str, extension: str = "wav") -> Path:
        """获取音频文件路径"""
        return self.audio_dir / f"{video_id}.{extension}"
    
    def cleanup_audio_file(self, video_id: str) -> bool:
        """清理指定视频的音频文件"""
        try:
            extensions = ['wav', 'mp3', 'm4a', 'webm', 'mp4']
            cleaned = False
            
            for ext in extensions:
                file_path = self.get_audio_file_path(video_id, ext)
                if file_path.exists():
                    file_path.unlink()
                    logging.info(f"Cleaned up audio file: {file_path}")
                    cleaned = True
            
            return cleaned
        except Exception as e:
            logging.error(f"Failed to cleanup audio file for {video_id}: {e}")
            return False
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """清理超过指定时间的旧文件"""
        import time
        
        try:
            current_time = time.time()
            cutoff_time = current_time - (max_age_hours * 3600)
            cleaned_count = 0
            
            for file_path in self.audio_dir.iterdir():
                if file_path.is_file():
                    file_mtime = file_path.stat().st_mtime
                    if file_mtime < cutoff_time:
                        file_path.unlink()
                        logging.info(f"Cleaned up old file: {file_path}")
                        cleaned_count += 1
            
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file():
                    file_mtime = file_path.stat().st_mtime
                    if file_mtime < cutoff_time:
                        file_path.unlink()
                        logging.info(f"Cleaned up old upload file: {file_path}")
                        cleaned_count += 1
            
            logging.info(f"Cleaned up {cleaned_count} old files")
            return cleaned_count
            
        except Exception as e:
            logging.error(f"Failed to cleanup old files: {e}")
            return 0
    
    def get_storage_usage(self) -> dict:
        """获取存储使用情况"""
        try:
            def get_dir_size(path: Path) -> int:
                total = 0
                if path.exists() and path.is_dir():
                    for file_path in path.rglob('*'):
                        if file_path.is_file():
                            total += file_path.stat().st_size
                return total
            
            audio_size = get_dir_size(self.audio_dir)
            upload_size = get_dir_size(self.upload_dir)
            total_size = audio_size + upload_size
            
            return {
                "audio_size_bytes": audio_size,
                "upload_size_bytes": upload_size,
                "total_size_bytes": total_size,
                "audio_size_mb": round(audio_size / (1024 * 1024), 2),
                "upload_size_mb": round(upload_size / (1024 * 1024), 2),
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }
        except Exception as e:
            logging.error(f"Failed to get storage usage: {e}")
            return {}
    
    def cleanup_task_files(self, task_id: str, video_id: Optional[str] = None) -> bool:
        """清理特定任务的所有文件"""
        try:
            cleaned = False
            
            if video_id:
                if self.cleanup_audio_file(video_id):
                    cleaned = True
            
            
            return cleaned
        except Exception as e:
            logging.error(f"Failed to cleanup files for task {task_id}: {e}")
            return False


storage_manager = StorageManager()
