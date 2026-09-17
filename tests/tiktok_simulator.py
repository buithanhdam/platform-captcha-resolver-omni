"""TikTok simulator: open the fake TikTok-style captcha page with browser/stealth
config from browser_config.py, then optionally solve it with the library.

Sử dụng:
    python tests/tiktok_simulator.py                 # open + auto-solve
    python tests/tiktok_simulator.py --headed        # show browser
    python tests/tiktok_simulator.py --no-solve      # only open, manual inspect
    python tests/tiktok_simulator.py --debug-dir captcha_debug  # save images

When you capture the REAL TikTok captcha page, replace the body/content of
fake_tiktok_captcha.html (or pass --page path/to/tiktok_captcha.html) and keep
data-role selectors aligned so the resolver works here first.

Run from anywhere; script adds the repo root to sys.path automatically.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.browser_config import (
    BROWSER_CONFIG,
    BROWSER_HEADER_CONFIG,
    build_stealth_js,
)

from captcha_resolver import CaptchaType, PlaywrightDriver, solve

DEFAULT_PAGE = Path(__file__).resolve().parent / "fake_tiktok_captcha.html"

ROLE_SELECTORS = {
    "background": "[data-role='captcha-background']",
    "slice": "[data-role='captcha-piece']",
    "handle": "[data-role='captcha-handle']",
    "refresh": "[data-role='captcha-refresh']",
    "success": "[data-role='captcha-success']",
    "container": "[data-role='captcha-container']",
    "image_source": "screenshot",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Open fake TikTok captcha page and optionally solve it")
    parser.add_argument("--page", default=str(DEFAULT_PAGE), help="HTML file to open")
    display = parser.add_mutually_exclusive_group()
    display.add_argument("--headed", action="store_true", help="show browser window")
    display.add_argument("--headless", action="store_true", help="force headless")
    parser.add_argument("--no-solve", action="store_true", help="only open, do not run resolver")
    parser.add_argument("--wait", type=float, default=5.0, help="seconds to keep browser open after solving")
    parser.add_argument("--debug-dir", default=None, help="save bg.png / piece.png from the resolver")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    headless = not args.headed if args.headed else (args.headless or BROWSER_CONFIG["headless"])

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(
                headless=headless,
                channel=BROWSER_CONFIG["channel"],
                args=BROWSER_HEADER_CONFIG,
                timeout=BROWSER_CONFIG["timeout"],
            )
        except Exception as exc:
            print(f"[warn] channel '{BROWSER_CONFIG['channel']}' unavailable ({exc}); using default chromium")
            browser = p.chromium.launch(
                headless=headless,
                args=BROWSER_HEADER_CONFIG,
                timeout=BROWSER_CONFIG["timeout"],
            )

        context = browser.new_context(
            user_agent=BROWSER_CONFIG["user_agent"],
            viewport={"width": BROWSER_CONFIG["viewport"]["width"], "height": BROWSER_CONFIG["viewport"]["height"]},
            locale=BROWSER_CONFIG["locale"],
            timezone_id=BROWSER_CONFIG["timezone_id"],
        )
        context.add_init_script(build_stealth_js())

        page = context.new_page()
        page.goto(Path(args.page).resolve().as_uri(), wait_until="load")
        page.wait_for_selector("[data-role='captcha-container']", timeout=BROWSER_CONFIG["timeout"])
        print(f"[tiktok-sim] fake captcha page loaded: {args.page}")

        if not args.no_solve:
            config = dict(ROLE_SELECTORS)
            if args.debug_dir:
                config["debug_dir"] = args.debug_dir
            print("[tiktok-sim] solving...")
            result = solve(CaptchaType.PUZZLE_SLIDER, PlaywrightDriver(page), config=config)
            print("[tiktok-sim] solved:", result.solved)
            print("[tiktok-sim] value:", result.value)
            print("[tiktok-sim] meta:", result.meta)
            if not result.solved and result.error:
                print("[tiktok-sim] error:", result.error)

        print(f"[tiktok-sim] keeping browser open {args.wait}s for inspection...")
        page.wait_for_timeout(args.wait * 1000.0)
        browser.close()


if __name__ == "__main__":
    main()