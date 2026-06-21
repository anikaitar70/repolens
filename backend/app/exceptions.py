class RepoLensError(Exception):
    """Base exception for RepoLens application errors."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidUploadError(RepoLensError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)


class ZipSecurityError(RepoLensError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)


class AnalysisError(RepoLensError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=500)
