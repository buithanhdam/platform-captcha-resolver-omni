from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from .. import vision
from ..base import BaseResolver, apply_config
from ..types import CaptchaType, SolveResult

__all__ = ["Object3DConfig", "Object3DResolver"]


@dataclass
class Object3DConfig:
    target: str = ""
    options: list[str] = field(default_factory=list)
    success: str = ""
    container: str = ""


class Object3DResolver(BaseResolver):
    captcha_type = CaptchaType.OBJECT_3D
    name = "object_3d"

    def __init__(self, driver=None, config: Optional[Object3DConfig] = None):
        super().__init__(driver)
        self.config: Object3DConfig = apply_config(Object3DConfig(), config)

    def solve(self) -> SolveResult:
        started = time.perf_counter()
        cfg = self.config
        if not cfg.target or not cfg.options:
            return SolveResult(
                solved=False,
                elapsed_ms=(time.perf_counter() - started) * 1000.0,
                error="target and options selectors are required",
            )

        driver = self._require_driver()
        target_image = driver.screenshot(cfg.target)
        option_images = [driver.screenshot(sel) for sel in cfg.options]
        index, scores = vision.best_match_index(target_image, option_images)

        return SolveResult(
            solved=True,
            value=index,
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
            meta={"scores": scores, "selector": cfg.options[index]},
        )