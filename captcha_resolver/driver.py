from __future__ import annotations

import re
from typing import Optional

import numpy as np

from . import vision
from .base import BaseDriver
from .mouse import circular_drag_path, human_drag_path
from .types import Box, Point

__all__ = ["PlaywrightDriver"]

_URL_RE = re.compile(r"url\(\s*['\"]?(.*?)['\"]?\s*\)")


class PlaywrightDriver(BaseDriver):
    def __init__(self, page, default_timeout: int = 10000):
        self.page = page
        self.default_timeout = default_timeout

    def _locator(self, selector: str):
        return self.page.locator(selector)

    def element_count(self, selector: str) -> int:
        return self._locator(selector).count()

    def is_visible(self, selector: str) -> bool:
        locator = self._locator(selector)
        return locator.count() > 0 and locator.first.is_visible()

    def bounding_box(self, selector: str) -> Optional[Box]:
        box = self._locator(selector).first.bounding_box()
        if box is None:
            return None
        return Box(x=box["x"], y=box["y"], width=box["width"], height=box["height"])

    def screenshot(self, selector: str) -> np.ndarray:
        data = self._locator(selector).first.screenshot(timeout=self.default_timeout)
        return vision.load_image(data)

    def get_style_url(self, selector: str) -> Optional[str]:
        style = self._locator(selector).first.get_attribute("style") or ""
        match = _URL_RE.search(style)
        return match.group(1) if match else None

    def click(self, selector: str, timeout: Optional[int] = None) -> None:
        self._locator(selector).first.click(
            timeout=timeout if timeout is not None else self.default_timeout
        )

    def human_drag(self, start: Point, end: Point, duration: float = 0.8) -> None:
        path = human_drag_path(start, end)
        mouse = self.page.mouse
        mouse.move(start.x, start.y)
        mouse.down()
        segment_ms = max(4.0, duration * 1000.0 / len(path))
        for point in path:
            mouse.move(point.x, point.y)
            self.page.wait_for_timeout(segment_ms)
        mouse.up()

    def circular_drag(
        self,
        center: Point,
        radius: float,
        start_angle_deg: float,
        delta_deg: float,
        duration: float = 1.2,
    ) -> None:
        path = circular_drag_path(center, radius, start_angle_deg, delta_deg)
        mouse = self.page.mouse
        first = path[0]
        mouse.move(first.x, first.y)
        mouse.down()
        segment_ms = max(4.0, duration * 1000.0 / len(path))
        for point in path[1:]:
            mouse.move(point.x, point.y)
            self.page.wait_for_timeout(segment_ms)
        mouse.up()

    def wait(self, seconds: float) -> None:
        self.page.wait_for_timeout(seconds * 1000.0)