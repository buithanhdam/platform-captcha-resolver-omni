from typing import Optional

from .base import BaseResolver
from .exceptions import UnsupportedCaptchaTypeError
from .solvers.hashcash import HashcashResolver
from .solvers.object_3d import Object3DResolver
from .solvers.puzzle_slider import PuzzleSliderResolver
from .solvers.whirl_rotate import WhirlRotateResolver
from .types import CaptchaType, SolveResult

__all__ = ["REGISTRY", "create_resolver", "solve"]

REGISTRY: dict[CaptchaType, type[BaseResolver]] = {
    CaptchaType.PUZZLE_SLIDER: PuzzleSliderResolver,
    CaptchaType.GEE_TEST_V4: PuzzleSliderResolver,
    CaptchaType.WHIRL_ROTATE: WhirlRotateResolver,
    CaptchaType.OBJECT_3D: Object3DResolver,
    CaptchaType.HASHCASH: HashcashResolver,
}


def create_resolver(captcha_type, driver=None, config: Optional[dict] = None) -> BaseResolver:
    key = CaptchaType(captcha_type)
    resolver_cls = REGISTRY.get(key)
    if resolver_cls is None:
        raise UnsupportedCaptchaTypeError(f"Unsupported captcha type: {captcha_type}")
    return resolver_cls(driver=driver, config=config)


def solve(captcha_type, driver=None, config: Optional[dict] = None) -> SolveResult:
    return create_resolver(captcha_type, driver=driver, config=config).solve()