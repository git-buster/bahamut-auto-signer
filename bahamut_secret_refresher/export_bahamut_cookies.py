from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OUTPUTS = (
    ("www", "https://www.gamer.com.tw/", "baha_cookie_www.json"),
    ("daily", "https://www.gamer.com.tw/dailySign.php", "baha_cookie_daily.json"),
    ("guild", "https://guild.gamer.com.tw/", "baha_cookie_guild.json"),
    ("ani", "https://ani.gamer.com.tw/", "baha_cookie_ani.json"),
)


def load_chromium_page() -> Any:
    try:
        from DrissionPage import ChromiumPage
    except ImportError as exc:
        raise SystemExit(
            "Missing DrissionPage. Install it first:\n"
            "python -m pip install DrissionPage\n"
        ) from exc
    return ChromiumPage


def export_current_cookies(page: Any, path: Path) -> None:
    cookies = page.cookies(all_info=True)
    path.write_text(
        json.dumps(cookies, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Exported {len(cookies)} cookies to {path}")


def main() -> int:
    chromium_page = load_chromium_page()
    try:
        page = chromium_page()
    except Exception as exc:
        raise SystemExit(
            "Could not open Chromium. Close existing browser automation windows "
            "and try again, or install/update DrissionPage.\n"
            f"Original error: {exc}"
        ) from exc
    output_dir = Path.cwd()

    print("A Chromium window will open. Log in manually when needed.")
    print("After each page is fully logged in, return here and press Enter.")

    try:
        for name, url, filename in OUTPUTS:
            print(f"\nOpening {name}: {url}")
            page.get(url)
            input(f"Confirm {name} is logged in, then press Enter to export...")
            export_current_cookies(page, output_dir / filename)
    finally:
        page.close()

    print("\nDone. Add the JSON contents to GitHub Secrets:")
    print("baha_cookie_www.json   -> BAHA_COOKIE_JSON")
    print("baha_cookie_daily.json -> BAHA_DAILY_COOKIE_JSON")
    print("baha_cookie_guild.json -> BAHA_GUILD_COOKIE_JSON")
    print("baha_cookie_ani.json   -> BAHA_ANIME_COOKIE_JSON")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
