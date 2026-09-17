"""Synthetic self-check for the library: vision + hashcash only.

Run: python examples/selftest.py
"""

from captcha_resolver import CaptchaType, create_resolver
from captcha_resolver import vision


def build_synthetic_slider(hole_x: int = 150) -> tuple[object, object, int]:
    import cv2
    import numpy as np

    def make_patch() -> np.ndarray:
        patch = np.full((50, 50, 3), 200, dtype=np.uint8)
        cv2.rectangle(patch, (5, 5), (44, 44), (80, 80, 210), -1)
        cv2.circle(patch, (24, 24), 12, (30, 160, 90), 3)
        cv2.line(patch, (5, 40), (44, 8), (220, 90, 40), 4)
        return patch

    patch = make_patch()
    bg = np.full((200, 400, 3), 235, dtype=np.uint8)
    for i in range(0, 200, 12):
        cv2.line(bg, (0, i), (399, i + 60), (180, 180, 182), 1)
    bg[70:120, hole_x : hole_x + 50] = patch
    return bg, patch.copy(), hole_x


def test_puzzle_slider() -> None:
    bg, piece, expected = build_synthetic_slider(hole_x=150)
    match = vision.locate_puzzle_offset(bg, piece)
    assert abs(match.x - expected) < 6, f"expected ~{expected}, got {match.x}"
    assert match.confidence > 0.6, f"confidence too low: {match.confidence}"
    print(f"[puzzle_slider] OK x={match.x:.1f} conf={match.confidence:.3f} ({match.method})")


def test_object_3d() -> None:
    import cv2
    import numpy as np

    target = np.full((64, 64, 3), (30, 160, 200), dtype=np.uint8)
    cv2.circle(target, (32, 32), 20, (240, 220, 60), -1)
    wrong = np.full((64, 64, 3), (40, 40, 40), dtype=np.uint8)
    cv2.rectangle(wrong, (8, 8), (40, 40), (90, 90, 200), -1)
    index, scores = vision.best_match_index(target, [wrong, target, wrong])
    assert index == 1, f"expected option 1, got {index}"
    print(f"[object_3d] OK index={index} scores={[round(s, 3) for s in scores]}")


def test_whirl() -> None:
    import cv2
    import numpy as np

    img = np.full((120, 120, 3), 255, dtype=np.uint8)
    cv2.rectangle(img, (30, 60), (90, 115), (40, 40, 40), -1)
    res = vision.detect_upright_angle(img)
    assert res["valid"], "contour not found"
    print(f"[whirl] OK axis={res['axis_angle_deg']:.1f}deg "
          f"angle_to_upright={res['angle_to_upright_deg']:.1f}deg")


def test_hashcash() -> None:
    from captcha_resolver.solvers.hashcash import verify_stamp

    resolver = create_resolver(
        CaptchaType.HASHCASH,
        config={"resource": "test-resource", "bits": 12, "hasher": "sha1"},
    )
    result = resolver.solve()
    assert result.solved, result
    assert verify_stamp(
        header=result.value["header"],
        digest=result.value["digest"],
        bits=12,
    ), "stamp failed verification"
    print(f"[hashcash] OK bits=12 nonce={result.value['nonce']} "
          f"digest={result.value['digest'][:16]}...")


if __name__ == "__main__":
    test_puzzle_slider()
    test_object_3d()
    test_whirl()
    test_hashcash()
    print("\nALL SELF-CHECKS PASSED")