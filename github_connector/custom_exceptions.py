class GitHubAPIError(Exception):
    """Base exception for all GitHub API related errors."""
    
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ResourceNotFound(GitHubAPIError):
    """Raised when a repository or resource returns 404."""
    
    def __init__(self, resource: str):
        message = f"Resource not found: {resource}"
        super().__init__(message, status_code=404)


class RateLimitExceeded(GitHubAPIError):
    """Raised when GitHub rate limit is exceeded (429 or 403)."""
    
    def __init__(self, retry_after: int = None):
        message = "GitHub API rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class AuthenticationError(GitHubAPIError):
    """Raised when authentication fails (401)."""
    
    def __init__(self):
        message = "Authentication failed. Check your GITHUB_TOKEN"
        super().__init__(message, status_code=401)


class NetworkError(GitHubAPIError):
    """Raised when network/connection issues occur."""
    
    def __init__(self, original_error: Exception):
        message = f"Network error: {str(original_error)}"
        super().__init__(message)
        self.original_error = original_error