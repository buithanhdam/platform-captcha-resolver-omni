"""Usage example: solve a GeeTest v4 slider captcha with Playwright.

Copy the `captcha_resolver` folder into your project, then:

    from captcha_resolver import CaptchaType, PlaywrightDriver, solve

The page must already be where the captcha is visible (e.g. a login form)
or navigate to it first:

    page.goto("https://target-site.com/login")

TikTok uses a different selector set; pass them via `config` once
confirmed during research.
"""

from playwright.sync_api import sync_playwright

from captcha_resolver import CaptchaType, PlaywrightDriver, solve

CAPTCHA_PAGE_URL = "https://example.com/page-with-captcha"

# Defaults are GeeTest v4 selectors. For other providers, override:
# config = {
#     "background": ".captcha__bg",
#     "slice": ".captcha__piece",
#     "handle": ".captcha__slider",
#     "image_source": "screenshot",  # TikTok-style: no raw image URLs
#     "debug_dir": "captcha_debug",
# }

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(CAPTCHA_PAGE_URL)

    result = solve(CaptchaType.GEE_TEST_V4, PlaywrightDriver(page))
    print("solved:", result.solved)
    print("value:", result.value)
    print("meta:", result.meta)

    browser.close()