"""Browser / stealth config for the TikTok simulator.

Values copied from the old bingx scraper setup and kept verbatim.
"""
import os

BROWSER_CONFIG = {
    "channel": os.environ.get('BROWSER_CHANNEL', "msedge"),
    "headless": os.environ.get("HEADLESS", "true").lower() == "true",
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "timeout": 30000,
    "locale": "vi-VN",
    "timezone_id": "Asia/Ho_Chi_Minh",
}

BROWSER_HEADER_CONFIG = [
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-infobars',
]

STEALTH_CONFIG = {
    "webdriver": False,
    "chrome_app": False,
    "chrome_csi": False,
    "chrome_load_times": False,
    "chrome_runtime": False,
    "iframe_content_window": False,
    "media_codecs": False,
    "navigator_hardware_concurrency": 4,
    "navigator_languages": ["en-US", "en"],
    "navigator_permissions": False,
    "navigator_plugins": False,
    "navigator_webdriver": False,
    "outerdimensions": False,
    "webgl_vendor": False,
}


def build_stealth_js() -> str:
    """Build the anti-detection init script from STEALTH_CONFIG.

    Practical subset implemented in JS; keys marked False are already the
    stealth defaults and need no script. media_codecs / webgl_vendor /
    iframe_content_window require more elaborate JS and are left as an
    extension point for when TikTok hardening demands them.
    """
    parts = []
    parts.append("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
    languages = STEALTH_CONFIG["navigator_languages"]
    parts.append(
        "Object.defineProperty(navigator, 'languages', "
        "{ get: () => %r });" % (languages,)
    )
    parts.append(
        "Object.defineProperty(navigator, 'hardwareConcurrency', "
        "{ get: () => %d });" % STEALTH_CONFIG["navigator_hardware_concurrency"]
    )
    return "\n".join(parts)