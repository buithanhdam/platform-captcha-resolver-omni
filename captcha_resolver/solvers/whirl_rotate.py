from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from .. import vision
from ..base import BaseResolver, apply_config
from ..logging import get_logger
from ..types import CaptchaType, Point, SolveResult

__all__ = ["WhirlRotateConfig", "WhirlRotateResolver"]

logger = get_logger(__name__)


@dataclass
class WhirlRotateConfig:
    image: str = ""
    dial: str = ""
    dial_center: str = ""
    radius: float = 0.0
    start_angle_deg: float = 0.0
    direction: int = -1
    max_attempts: int = 3
    drag_duration: float = 1.2
    check_wait: float = 3.0
    success: str = ""
    container: str = ""


class WhirlRotateResolver(BaseResolver):
    captcha_type = CaptchaType.WHIRL_ROTATE
    name = "whirl_rotate"

    def __init__(self, driver=None, config: Optional[WhirlRotateConfig] = None):
        super().__init__(driver)
        self.config: WhirlRotateConfig = apply_config(WhirlRotateConfig(), config)

    def _estimate_angle(self) -> float:
        cfg = self.config
        driver = self._require_driver()
        if cfg.image:
            image = driver.screenshot(cfg.image)
            result = vision.detect_upright_angle(image)
            if result.get("valid"):
                return float(result["angle_to_upright_deg"])
        return 0.0

    def _apply_rotation(self, angle_deg: float) -> None:
        cfg = self.config
        driver = self._require_driver()
        if not cfg.dial:
            return
        center = driver.bounding_box(cfg.dial_center)
        if center is None:
            box = driver.bounding_box(cfg.dial)
            center_box = box
        else:
            center_box = center
        if center_box is None:
            return
        radius = cfg.radius or max(center_box.width, center_box.height) / 2.0
        driver.circular_drag(
            Point(center_box.center.x, center_box.center.y),
            radius,
            start_angle_deg=cfg.start_angle_deg,
            delta_deg=angle_deg * cfg.direction,
            duration=cfg.drag_duration,
        )

    def _is_solved(self) -> bool:
        if not self.driver:
            return False
        if self.config.success and self.driver.is_visible(self.config.success):
            return True
        if self.config.container and not self.driver.is_visible(self.config.container):
            return True
        return False

    def solve(self) -> SolveResult:
        started = time.perf_counter()
        angle = self._estimate_angle()
        if not angle:
            return SolveResult(
                solved=False,
                elapsed_ms=(time.perf_counter() - started) * 1000.0,
                error="Could not estimate rotation angle",
            )
        self._apply_rotation(angle)
        for attempt in range(1, self.config.max_attempts + 1):
            if self._is_solved():
                return SolveResult(
                    solved=True,
                    value=angle,
                    attempts=attempt,
                    elapsed_ms=(time.perf_counter() - started) * 1000.0,
                    meta={"angle_to_upright_deg": angle},
                )
            logger.warning("Whirl attempt %d not confirmed, retrying", attempt)
            self._apply_rotation(angle)
            if self.config.check_wait:
                self._require_driver().wait(self.config.check_wait)

        return SolveResult(
            solved=False,
            value=angle,
            attempts=self.config.max_attempts,
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
            error="Rotation not confirmed by page",
        )