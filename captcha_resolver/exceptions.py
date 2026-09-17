from __future__ import annotations

__all__ = [
    "CaptchaSolverError",
    "CaptchaNotDetectedError",
    "CaptchaSolveFailedError",
    "UnsupportedCaptchaTypeError",
]


class CaptchaSolverError(Exception):
    """Base error for all captcha resolver failures."""


class CaptchaNotDetectedError(CaptchaSolverError):
    """Raised when the expected captcha element is not found on the page."""


class CaptchaSolveFailedError(CaptchaSolverError):
    """Raised when every attempt to solve the captcha fails."""


class UnsupportedCaptchaTypeError(CaptchaSolverError):
    """Raised when the captcha type is not registered in the factory."""