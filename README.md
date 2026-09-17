# captcha-resolver-omni

Thư viện giải CAPTCHA — chỉ cần sao chép thư mục `captcha_resolver/` vào dự án của bạn và import trực tiếp (không cần `pip install` / `pyproject`).

## Các loại CAPTCHA được hỗ trợ

| Loại CAPTCHA                | Enum                        | Trạng thái                                       |
| --------------------------- | --------------------------- | ------------------------------------------------ |
| Puzzle (kéo thanh trượt)    | `CaptchaType.PUZZLE_SLIDER` | Đã hỗ trợ (GeeTest v4, TikTok cần kiểm tra thêm) |
| GeeTest v4 (bí danh)        | `CaptchaType.GEE_TEST_V4`   | Sử dụng cùng solver với Puzzle Slider            |
| Whirl (xoay hình)           | `CaptchaType.WHIRL_ROTATE`  | Thuật toán heuristic (đang phát triển)           |
| 3D (tìm vật thể giống nhau) | `CaptchaType.OBJECT_3D`     | ORB + fallback bằng pixel (đang phát triển)      |
| Hashcash                    | `CaptchaType.HASHCASH`      | Nonce SHA-1/SHA-256 (đang phát triển)            |

## Cấu trúc thư mục

```text
captcha_resolver/

├── __init__.py        # API công khai (solve, create_resolver, PlaywrightDriver, ...)
├── types.py            # CaptchaType, Point, Box, SolveResult
├── exceptions.py
├── base.py             # BaseResolver, BaseDriver (có thể triển khai cho Selenium, v.v.)
├── factory.py          # REGISTRY + create_resolver() + solve()
├── vision.py           # OpenCV: template matching, xoay hình, tính độ tương đồng ORB
├── mouse.py            # Tạo quỹ đạo kéo chuột mô phỏng thao tác người dùng
├── driver.py           # PlaywrightDriver (triển khai BaseDriver cho Playwright)
├── logging.py
└── solvers/
    ├── puzzle_slider.py
    ├── whirl_rotate.py
    ├── object_3d.py
    └── hashcash.py
```

## Cách sử dụng

```python
from captcha_resolver import CaptchaType, PlaywrightDriver, solve

result = solve(
    CaptchaType.GEE_TEST_V4,
    PlaywrightDriver(page)
)

if result.solved:
    print("dx:", result.value)  # khoảng cách di chuyển tính bằng pixel
else:
    print(result.error)
```

### Tùy chỉnh selector

Các selector có thể được thay đổi thông qua `config`:

```python
result = solve(
    CaptchaType.PUZZLE_SLIDER,
    PlaywrightDriver(page),
    config={
        "background": ".captcha__bg",
        "slice": ".captcha__piece",
        "handle": ".captcha__slider",
        "image_source": "screenshot",  # Kiểu TikTok: không có URL ảnh trực tiếp
        "max_attempts": 5,
        "debug_dir": "captcha_debug",  # Ghi bg.png / piece.png
    }
)
```

## Hashcash thuần (không cần driver)

```python
from captcha_resolver import CaptchaType, solve

result = solve(
    CaptchaType.HASHCASH,
    config={
        "resource": "challenge",
        "bits": 20
    }
)

print(result.value)
# {"nonce": ..., "header": ..., "digest": ...}
```

## Tự kiểm tra (Self-test)

```bash
python examples/selftest.py
```

Kiểm tra các chức năng template matching / ORB / xoay hình / Hashcash trên dữ liệu hình ảnh được tạo tổng hợp — không cần kết nối mạng.

## Sử dụng trong các dự án khác

1. Sao chép thư mục `captcha_resolver/` vào dự án của bạn.

2. Cài đặt các thư viện phụ thuộc:

```bash
pip install -r requirements.txt
```

Các thư viện chính gồm:

* `numpy`
* `opencv-python`
* `requests`
* `playwright`

3. Tích hợp adapter:

Với Playwright, chỉ cần sử dụng:

```python
PlaywrightDriver(page)
```

Nếu sử dụng framework automation khác, hãy triển khai `BaseDriver` tương ứng.

## Trạng thái nghiên cứu – TikTok

Solver Puzzle Slider hiện được chuyển từ code `bingx/geetest`. Solver **chưa được xác thực hoàn chỉnh với CAPTCHA của TikTok**.

Các vấn đề cần tiếp tục nghiên cứu:

* Xác định các selector mà TikTok sử dụng (`bg` / `piece` / `slider` / `iframe`?).
* Xác định phần `piece` là một ảnh riêng biệt (kiểu URL) hay được lấy trực tiếp từ screenshot (`image_source="screenshot"`).
* Điều chỉnh `scale ratio` và các giá trị `offset_x/y` dựa trên dữ liệu CAPTCHA thực tế.
