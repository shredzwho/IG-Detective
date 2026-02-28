class IGDetectiveError(Exception):
    """Base exception for all IG-Detective errors."""
    pass

class RateLimitError(IGDetectiveError):
    """Raised when Instagram returns a 429 Too Many Requests."""
    pass

class AuthenticationError(IGDetectiveError):
    """Raised when authentication fails or session is invalid (401)."""
    pass

class UserNotFoundError(IGDetectiveError):
    """Raised when a target user does not exist (404)."""
    pass

class NetworkError(IGDetectiveError):
    """Raised for general connectivity issues."""
    pass
