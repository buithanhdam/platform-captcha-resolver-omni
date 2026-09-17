from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Any, Optional

from .types import Box, CaptchaType, Point, SolveResult

__all__ = ["BaseDriver", "BaseResolver", "apply_config"]


def apply_config(default: Any, config: Any) -> Any:
    if config is None:
        return default
    if isinstance(config, dict):
        updates = {k: v for k, v in config.items() if hasattr(default, k)}
        return replace(default, **updates)
    return config


class BaseDriver(ABC):
    """Minimal browser-automation contract. Implement this to plug the
    library into Playwright, Selenium, uiautomation, etc."""

    @abstractmethod
    def element_count(self, selector: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def is_visible(self, selector: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def bounding_box(self, selector: str) -> Optional[Box]:
        raise NotImplementedError

    @abstractmethod
    def screenshot(self, selector: str) -> Any:
        """Return a BGR numpy array of the element."""
        raise NotImplementedError

    @abstractmethod
    def get_style_url(self, selector: str) -> Optional[str]:
        """Extract the background-image url(...) from an element style."""
        raise NotImplementedError

    @abstractmethod
    def click(self, selector: str, timeout: Optional[int] = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def human_drag(self, start: Point, end: Point, duration: float = 0.8) -> None:
        raise NotImplementedError

    @abstractmethod
    def circular_drag(
        self,
        center: Point,
        radius: float,
        start_angle_deg: float,
        delta_deg: float,
        duration: float = 1.2,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def wait(self, seconds: float) -> None:
        raise NotImplementedError


class BaseResolver(ABC):
    captcha_type: CaptchaType
    name: str = "base"

    def __init__(self, driver: Optional[BaseDriver] = None):
        self.driver = driver

    def _require_driver(self) -> BaseDriver:
        if self.driver is None:
            raise RuntimeError(f"{type(self).__name__} requires a driver instance")
        return self.driver

    @abstractmethod
    def solve(self) -> SolveResult:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{type(self).__name__} type={self.captcha_type.value}>"