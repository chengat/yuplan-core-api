#!/usr/bin/env python3
"""
Open a real browser with Playwright, let you log in to York, then print a Cookie header.

Usage:
  python3 scripts/get_sis_cookie_playwright.py

One-time setup:
  pip install playwright
  python3 -m playwright install chromium
"""

from __future__ import annotations

import sys

TARGET_URL = "https://apps1.sis.yorku.ca/WebObjects/cdm.woa/Contents/WebServerResources/FW2026LE.html"


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        print(
            "Playwright not available. Run: pip install playwright && python3 -m playwright install chromium",
            file=sys.stderr,
        )
        print(f"Import error: {exc}", file=sys.stderr)
        return 1

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(TARGET_URL, wait_until="domcontentloaded")

        print("\nBrowser opened.")
        print("1) Complete York login in the opened browser")
        print("2) Confirm you can open timetable pages")
        input("3) Press Enter here to capture cookies and exit... ")

        cookies = context.cookies()
        filtered = [c for c in cookies if c.get("domain", "").endswith("yorku.ca")]
        if not filtered:
            print("No yorku.ca cookies found in browser context.", file=sys.stderr)
            browser.close()
            return 1

        cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in filtered)
        print("\nCOOKIE_HEADER_START")
        print(cookie_header)
        print("COOKIE_HEADER_END\n")
        print("Use the line between markers as your POST body cookie value.")

        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
