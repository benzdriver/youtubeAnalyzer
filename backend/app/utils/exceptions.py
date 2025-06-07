from typing import Optional


class YouTubeAnalyzerError(Exception):
    """Base exception for YouTube Analyzer application"""

    pass


class ValidationError(YouTubeAnalyzerError):
    """Raised when input validation fails"""

    pass


class ExternalServiceError(YouTubeAnalyzerError):
    """Raised when external service calls fail"""

    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message)
        self.service = service
        self.retry_after = retry_after


class YouTubeAPIError(ExternalServiceError):
    """Specific error for YouTube API failures"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        quota_exceeded: bool = False,
    ):
        super().__init__(message, service="youtube_api")
        self.error_code = error_code
        self.quota_exceeded = quota_exceeded


class AudioDownloadError(ExternalServiceError):
    """Specific error for audio download failures"""

    def __init__(self, message: str, video_id: Optional[str] = None):
        super().__init__(message, service="yt_dlp")
        self.video_id = video_id


class AnalysisError(YouTubeAnalyzerError):
    """Raised when analysis processing fails"""

    pass


class TaskNotFoundError(YouTubeAnalyzerError):
    """Raised when a task cannot be found"""

    pass


class TaskCancellationError(YouTubeAnalyzerError):
    """Raised when a task is cancelled"""

    pass


class StorageError(YouTubeAnalyzerError):
    """Raised when file storage operations fail"""

    pass


class RetryableError(YouTubeAnalyzerError):
    """Base class for errors that should trigger retries"""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class RateLimitError(RetryableError):
    """Raised when API rate limits are exceeded"""

    def __init__(
        self, message: str, service: Optional[str] = None, retry_after: int = 300
    ):
        super().__init__(message, retry_after)
        self.service = service
