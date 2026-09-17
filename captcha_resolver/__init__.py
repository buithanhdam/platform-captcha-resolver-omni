from .base import BaseDriver, BaseResolver, apply_config
from .exceptions import (
    CaptchaNotDetectedError,
    CaptchaSolverError,
    CaptchaSolveFailedError,
    UnsupportedCaptchaTypeError,
)
from .factory import REGISTRY, create_resolver, solve
from .types import Box, CaptchaType, Point, SolveResult

__version__ = "0.1.0"

try:
    from .driver import PlaywrightDriver
except Exception:  # pragma: no cover - playwright not installed
    PlaywrightDriver = None  # type: ignore[assignment]

__all__ = [
    "__version__",
    "CaptchaType",
    "Point",
    "Box",
    "SolveResult",
    "BaseDriver",
    "BaseResolver",
    "apply_config",
    "PlaywrightDriver",
    "create_resolver",
    "solve",
    "REGISTRY",
    "CaptchaSolverError",
    "CaptchaNotDetectedError",
    "CaptchaSolveFailedError",
    "UnsupportedCaptchaTypeError",
]