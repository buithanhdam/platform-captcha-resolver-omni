from __future__ import annotations

import hashlib
import itertools
import time
from dataclasses import dataclass
from typing import Optional

from ..base import BaseResolver, apply_config
from ..types import CaptchaType, SolveResult

__all__ = ["HashcashConfig", "HashcashResolver", "find_nonce", "leading_zero_bits", "verify_stamp"]


@dataclass
class HashcashConfig:
    resource: str = ""
    bits: int = 20
    hasher: str = "sha1"
    date: Optional[str] = None
    max_iterations: int = 50_000_000
    counter_start: int = 0


def leading_zero_bits(hex_digest: str) -> int:
    binary = "".join(f"{int(c, 16):04b}" for c in hex_digest)
    return len(binary) - len(binary.lstrip("0"))


def build_stamp(bits: int, date: str, resource: str, counter: int) -> str:
    return f"1:{bits}:{date}:{resource}::{counter:x}"


def find_nonce(
    resource: str,
    bits: int,
    hasher: str = "sha1",
    date: Optional[str] = None,
    counter_start: int = 0,
    max_iterations: int = 50_000_000,
) -> tuple[int, str, str]:
    if date is None:
        date = time.strftime("%y%m%d")
    digest_fn = getattr(hashlib, hasher)
    for counter in itertools.count(counter_start):
        header = build_stamp(bits, date, resource, counter)
        digest = digest_fn(header.encode()).hexdigest()
        if leading_zero_bits(digest) >= bits:
            return counter, header, digest
        if counter - counter_start >= max_iterations:
            raise TimeoutError(f"Nonce not found within {max_iterations} iterations for {bits} bits")


def verify_stamp(header: str, digest: str, bits: int, hasher: str = "sha1") -> bool:
    expected = getattr(hashlib, hasher)(header.encode()).hexdigest()
    if expected != digest:
        return False
    return leading_zero_bits(digest) >= bits


class HashcashResolver(BaseResolver):
    captcha_type = CaptchaType.HASHCASH
    name = "hashcash"

    def __init__(self, driver=None, config: Optional[HashcashConfig] = None):
        super().__init__(driver)
        self.config: HashcashConfig = apply_config(HashcashConfig(), config)

    def solve(self) -> SolveResult:
        started = time.perf_counter()
        cfg = self.config
        if not cfg.resource:
            return SolveResult(
                solved=False,
                elapsed_ms=(time.perf_counter() - started) * 1000.0,
                error="resource is required",
            )
        try:
            nonce, header, digest = find_nonce(
                resource=cfg.resource,
                bits=cfg.bits,
                hasher=cfg.hasher,
                date=cfg.date,
                counter_start=cfg.counter_start,
                max_iterations=cfg.max_iterations,
            )
        except TimeoutError as exc:
            return SolveResult(
                solved=False,
                elapsed_ms=(time.perf_counter() - started) * 1000.0,
                error=str(exc),
            )
        return SolveResult(
            solved=True,
            value={"nonce": nonce, "header": header, "digest": digest},
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
            meta={"bits": cfg.bits, "hasher": cfg.hasher},
        )