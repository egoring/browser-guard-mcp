"""실제 브라우저 창을 띄워서(headless=False) 눈으로 확인하는 예시.

라이브러리의 PlaywrightSession은 서버 용도로 headless=True 고정이라,
창을 보려면 Playwright를 직접 headed 모드로 띄운다.

사전 준비: pip install -e ".[dev]" && playwright install chromium
실행: python examples/demo_browser_headed.py
"""
import time

from playwright.sync_api import sync_playwright

from browser_guard_mcp.guard import DEMO_DIR, GuardConfig, GuardViolation, validate_url

config = GuardConfig(allowed_domains=[], read_only=True)
url = validate_url(str(DEMO_DIR / "index.html"), config)

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, slow_mo=300)
    page = browser.new_page()
    page.goto(url)
    print(f"열림: {page.title()} — 5초 후 자동으로 닫힙니다")
    time.sleep(5)
    browser.close()

print("\n허용목록 밖 도메인은 브라우저를 켜지도 않고 가드가 먼저 막는다:")
try:
    validate_url("https://example.com", config)
except GuardViolation as e:
    print(f"차단됨: {e}")
