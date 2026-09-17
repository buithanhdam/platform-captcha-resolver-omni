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
        headless=True, channel=BROWSER_CONFIG["channel"], args=BROWSER_HEADER_CONFIG
    )
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto(PAGE.resolve().as_uri())
    page.wait_for_selector("[data-role='captcha-container']")

    state0 = page.evaluate("window.__captcha_debug()")
    print("state0:", state0)

    driver = PlaywrightDriver(page)
    bg = driver.screenshot("[data-role='captcha-background']")
    piece = driver.screenshot("[data-role='captcha-piece']")
    match = vision.locate_puzzle_offset(bg, piece)
    print("match:", match)

    handle = driver.bounding_box("[data-role='captcha-handle']")
    print("handle box:", handle)
    start = handle.center
    from captcha_resolver.types import Point

    end = Point(start.x + round(match.x), start.y)
    print("drag:", start, "->", end)
    page.mouse.move(start.x, start.y)
    page.mouse.down()
    page.mouse.move(end.x, end.y, steps=30)
    page.mouse.up()
    page.wait_for_timeout(500)

    state1 = page.evaluate("window.__captcha_debug()")
    print("state1:", state1)

    browser.close()