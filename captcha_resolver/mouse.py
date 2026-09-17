from __future__ import annotations

import math
import random
from typing import Optional

from .types import Point

__all__ = ["human_drag_path", "circular_drag_path"]


def human_drag_path(
    start: Point,
    end: Point,
    steps: int = 42,
    wobble: float = 2.5,
    seed: Optional[int] = None,
) -> list[Point]:
    rng = random.Random(seed)
    dx = end.x - start.x
    dy = end.y - start.y
    path: list[Point] = []
    for i in range(1, steps + 1):
        t = i / steps
        ease = 1.0 - (1.0 - t) ** 3
        x = start.x + dx * ease
        y = start.y + dy * ease
        y += math.sin(t * math.pi) * wobble + rng.gauss(0.0, 0.6)
        path.append(Point(x, y))
    return path


def circular_drag_path(
    center: Point,
    radius: float,
    start_angle_deg: float,
    delta_deg: float,
    steps: int = 56,
    seed: Optional[int] = None,
) -> list[Point]:
    rng = random.Random(seed)
    start_rad = math.radians(start_angle_deg)
    delta_rad = math.radians(delta_deg)
    path: list[Point] = []
    for i in range(1, steps + 1):
        t = i / steps
        ease = t if delta_deg >= 0 else (1.0 - (1.0 - t) ** 3)
        ang = start_rad + delta_rad * ease
        r = radius + rng.gauss(0.0, 0.5)
        path.append(Point(center.x + r * math.cos(ang), center.y + r * math.sin(ang)))
    return path