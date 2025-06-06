class YouTubeAnalyzerError(Exception):
    pass


class ValidationError(YouTubeAnalyzerError):
    pass


class ExternalServiceError(YouTubeAnalyzerError):
    pass


class AnalysisError(YouTubeAnalyzerError):
    pass


class TaskNotFoundError(YouTubeAnalyzerError):
    pass


class TaskCancellationError(YouTubeAnalyzerError):
    pass
