from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import requests

from .. import vision
from ..base import BaseResolver, apply_config
from ..logging import get_logger
from ..types import CaptchaType, Point, SolveResult

__all__ = ["PuzzleSliderConfig", "PuzzleSliderResolver"]

logger = get_logger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class PuzzleSliderConfig:
    background: str = ".geetest_bg"
    slice: str = ".geetest_slice_bg"
    handle: str = ".geetest_btn"
    refresh: str = ".geetest_refresh"
    success: str = ".geetest_success"
    container: str = ".geetest_box"
    image_source: str = "auto"
    match_threshold: float = 0.45
    max_attempts: int = 3
    drag_duration: float = 0.9
    check_wait: float = 3.0
    refresh_wait: float = 1.5
    offset_x: float = 0.0
    offset_y: float = 0.0
    debug_dir: Optional[str] = None
    user_agent: str = DEFAULT_USER_AGENT
    timeout: float = 10.0


class PuzzleSliderResolver(BaseResolver):
    captcha_type = CaptchaType.PUZZLE_SLIDER
    name = "puzzle_slider"

    def __init__(self, driver=None, config: Optional[PuzzleSliderConfig] = None):
        super().__init__(driver)
        self.config: PuzzleSliderConfig = apply_config(PuzzleSliderConfig(), config)

    def _capture(self) -> tuple[Any, Any, float]:
        driver = self._require_driver()
        cfg = self.config

        if cfg.image_source == "screenshot":
            bg = driver.screenshot(cfg.background)
            piece = driver.screenshot(cfg.slice)
            box = driver.bounding_box(cfg.background)
            browser_width = box.width if box else float(bg.shape[1])
        else:
            bg_url = driver.get_style_url(cfg.background)
            piece_url = driver.get_style_url(cfg.slice) or driver.get_style_url(cfg.background)
            if not bg_url or not piece_url:
                raise ValueError("No image URL found in style attributes")
            bg = self._download(bg_url)
            piece = self._download(piece_url)
            box = driver.bounding_box(cfg.background)
            browser_width = box.width if box else 300.0

        scale = browser_width / float(bg.shape[1])
        if cfg.debug_dir:
            self._save_debug(bg, piece)
        return bg, piece, scale

    def _download(self, url: str) -> Any:
        response = requests.get(
            url,
            headers={"User-Agent": self.config.user_agent},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return vision.load_image(response.content)

    def _save_debug(self, bg: Any, piece: Any) -> None:
        import cv2

        debug_dir = Path(self.config.debug_dir)
        debug_dir.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(debug_dir / "bg.png"), bg)
        cv2.imwrite(str(debug_dir / "piece.png"), piece)

    def _is_solved(self) -> bool:
        driver = self._require_driver()
        cfg = self.config
        if cfg.success and driver.is_visible(cfg.success):
            return True
        if cfg.container and driver.element_count(cfg.container) > 0 and not driver.is_visible(cfg.container):
            return True
        return False

    def _refresh(self, safe: bool = False) -> None:
        driver = self._require_driver()
        cfg = self.config
        if not cfg.refresh:
            return
        try:
            if driver.element_count(cfg.refresh) > 0:
                driver.click(cfg.refresh)
                driver.wait(cfg.refresh_wait)
        except Exception:
            if not safe:
                raise

    def solve(self) -> SolveResult:
        import time

        started = time.perf_counter()
        cfg = self.config
        driver = self._require_driver()

        for attempt in range(1, cfg.max_attempts + 1):
            try:
                bg, piece, scale = self._capture()
                match = vision.locate_puzzle_offset(bg, piece)
                if match.confidence < cfg.match_threshold:
                    raise ValueError(
                        f"Low match confidence {match.confidence:.3f} ({match.method})"
                    )

                dx = int(round(match.x * scale + cfg.offset_x))
                dy = cfg.offset_y or 0

                handle_box = driver.bounding_box(cfg.handle)
                if handle_box is None:
                    raise ValueError("Slider handle not found")
                start = Point(handle_box.center.x, handle_box.center.y)
                end = Point(start.x + dx, start.y + dy)
                driver.human_drag(start, end, duration=cfg.drag_duration)
                driver.wait(cfg.check_wait)

                if self._is_solved():
                    return SolveResult(
                        solved=True,
                        value=dx,
                        attempts=attempt,
                        elapsed_ms=(time.perf_counter() - started) * 1000.0,
                        meta={
                            "confidence": match.confidence,
                            "match_method": match.method,
                            "raw_x": match.x,
                            "scale": scale,
                        },
                    )
                logger.warning("Attempt %d failed, refreshing captcha", attempt)
                self._refresh()
            except Exception as exc:
                logger.warning("Attempt %d error: %s", attempt, exc)
                self._refresh(safe=True)

        return SolveResult(
            solved=False,
            attempts=cfg.max_attempts,
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
            error=f"Failed after {cfg.max_attempts} attempts",
        )