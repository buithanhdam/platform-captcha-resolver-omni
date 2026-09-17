from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

import cv2
import numpy as np

ImageSource = Union[str, Path, np.ndarray, bytes]

__all__ = [
    "Match",
    "load_image",
    "to_gray",
    "to_edges",
    "trim_to_content",
    "locate_puzzle_offset",
    "detect_upright_angle",
    "orb_similarity",
    "best_match_index",
]


@dataclass
class Match:
    x: float
    confidence: float
    method: str


def load_image(src: ImageSource) -> np.ndarray:
    if isinstance(src, (str, Path)):
        image = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
        if image is None:
            raise FileNotFoundError(f"Cannot read image: {src}")
        return image
    if isinstance(src, bytes):
        return cv2.imdecode(np.frombuffer(src, np.uint8), cv2.IMREAD_UNCHANGED)
    return np.asarray(src)


def to_gray(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image
    if image.ndim == 3 and image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def to_edges(image: np.ndarray, low: int = 50, high: int = 150) -> np.ndarray:
    return cv2.Canny(to_gray(image), low, high)


def trim_to_content(image: np.ndarray, threshold: int = 20, margin: int = 1) -> np.ndarray:
    if image.ndim == 3 and image.shape[2] == 4:
        alpha = image[..., 3] > 8
        rgb = image[..., :3]
        spread = rgb.max(axis=2) - rgb.min(axis=2)
        mask = alpha & (spread > threshold)
    elif image.ndim == 3:
        mask = (255 - np.min(image, axis=2)) > threshold
    else:
        mask = image > threshold

    if not mask.any():
        return image

    ys, xs = np.where(mask)
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0 = max(0, y0 - margin)
    y1 = min(image.shape[0], y1 + margin)
    x0 = max(0, x0 - margin)
    x1 = min(image.shape[1], x1 + margin)
    return image[y0:y1, x0:x1]


def locate_puzzle_offset(background: np.ndarray, piece: np.ndarray) -> Match:
    bg = to_gray(background)
    gap = trim_to_content(piece)
    gap_gray = to_gray(gap)
    if gap_gray.size == 0 or gap_gray.shape[1] > bg.shape[1] or gap_gray.shape[0] > bg.shape[0]:
        raise ValueError("Piece is larger than the background image")

    bg_edges = to_edges(bg)
    gap_edges = to_edges(gap_gray)

    best = _best_template_match(bg_edges, gap_edges, "canny")
    alt = _best_template_match(bg, gap_gray, "gray")
    if alt.confidence > best.confidence:
        best = alt
    return best


def _best_template_match(image: np.ndarray, template: np.ndarray, method: str) -> Match:
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    return Match(x=float(max_loc[0]), confidence=float(max_val), method=method)


def detect_upright_angle(image: np.ndarray) -> dict:
    gray = to_gray(image)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return {"valid": False}

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < 50:
        return {"valid": False}

    rect = cv2.minAreaRect(largest)
    (cx, cy), (w, h), raw_angle = rect
    if w < h:
        axis_deg = raw_angle + 90.0
    else:
        axis_deg = raw_angle
    axis_deg %= 180.0

    angle_to_upright = (90.0 - axis_deg) % 360.0
    if angle_to_upright > 180.0:
        angle_to_upright -= 360.0

    return {
        "valid": True,
        "angle_to_upright_deg": angle_to_upright,
        "axis_angle_deg": axis_deg,
        "area": float(cv2.contourArea(largest)),
    }


def orb_similarity(a: np.ndarray, b: np.ndarray) -> float:
    orb = cv2.ORB_create(nfeatures=500)
    kp_a, des_a = orb.detectAndCompute(to_gray(a), None)
    kp_b, des_b = orb.detectAndCompute(to_gray(b), None)
    if des_a is None or des_b is None or len(kp_a) < 3 or len(kp_b) < 3:
        return _pixel_similarity(a, b)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches = bf.knnMatch(des_a, des_b, k=2)
    good = [m for m, n in matches if m.distance < 0.75 * n.distance]
    if not good:
        return 0.0
    return float(len(good) / min(len(kp_a), len(kp_b)))


def _pixel_similarity(a: np.ndarray, b: np.ndarray) -> float:
    size = (128, 128)
    a_small = cv2.resize(to_gray(a), size, interpolation=cv2.INTER_AREA)
    b_small = cv2.resize(to_gray(b), size, interpolation=cv2.INTER_AREA)
    a_norm = cv2.normalize(a_small, None, 0, 1, cv2.NORM_MINMAX)
    b_norm = cv2.normalize(b_small, None, 0, 1, cv2.NORM_MINMAX)
    return float(1.0 - np.abs(a_norm - b_norm).mean())


def best_match_index(target: np.ndarray, options: list[np.ndarray]) -> tuple[int, list[float]]:
    if not options:
        raise ValueError("No options to match against")
    scores = [orb_similarity(target, opt) for opt in options]
    best_idx = int(max(range(len(scores)), key=lambda i: scores[i]))
    return best_idx, scores