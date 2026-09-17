from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

__all__ = ["CaptchaType", "Point", "Box", "SolveResult"]


class CaptchaType(str, Enum):
    PUZZLE_SLIDER = "puzzle_slider"
    GEE_TEST_V4 = "geetest_v4"
    WHIRL_ROTATE = "whirl_rotate"
    OBJECT_3D = "object_3d"
    HASHCASH = "hashcash"


@dataclass
class Point:
    x: float
    y: float

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


@dataclass
class Box:
    x: float
    y: float
    width: float
    height: float

    @property
    def center(self) -> Point:
        return Point(self.x + self.width / 2.0, self.y + self.height / 2.0)


@dataclass
class SolveResult:
    solved: bool
    value: Any = None
    attempts: int = 0
    elapsed_ms: float = 0.0
    error: Optional[str] = None
    meta: dict[str, Any] = field(default_factory=dict)