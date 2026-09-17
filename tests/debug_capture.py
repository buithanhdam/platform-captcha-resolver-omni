import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from playwright.sync_api import sync_playwright
from tests.browser_config import BROWSER_CONFIG, BROWSER_HEADER_CONFIG
from captcha_resolver import vision, PlaywrightDriver

PAGE = Path(__file__).resolve().parent / "fake_tiktok_captcha.html"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        channel=BROWSER_CONFIG["channel"],
        args=BROWSER_HEADER_CONFIG,
    )
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto(PAGE.resolve().as_uri())
    page.wait_for_selector("[data-role='captcha-container']")

    gap_x = page.evaluate("window.__captcha_debug().gapX")

    driver = PlaywrightDriver(page)
    bg = driver.screenshot("[data-role='captcha-background']")
    piece = driver.screenshot("[data-role='captcha-piece']")

    import cv2
    cv2.imwrite("debug_bg.png", bg)
    cv2.imwrite("debug_piece.png", piece)
    print("sizes bg:", bg.shape, "piece:", piece.shape)

    match = vision.locate_puzzle_offset(bg, piece)
    print("gapX from JS:", gap_x)
    print("match:", match)

    trimmed = vision.trim_to_content(piece)
    print("trimmed piece:", trimmed.shape)
    gray_bg = vision.to_gray(bg)
    gray_p = vision.to_gray(trimmed)
    ph, pw = gray_p.shape
    best = (None, -1)
    for cand in range(max(0, gap_x - 40), gap_x + 41):
        roi = gray_bg[120 : 120 + ph, cand : cand + pw]
        if roi.shape != gray_p.shape:
            continue
        score = float(1.0 - (cv2.absdiff(gray_p, roi).mean() / 255.0))
        if best[1] < score:
            best = (cand, score)
    print("brute-force best near gap:", best)

    browser.close()