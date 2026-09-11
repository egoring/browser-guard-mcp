"""실제 헤드리스 Chromium을 띄워 가드가 브라우저 앞단에서 막는 걸 확인하는 예시.

사전 준비: pip install -e ".[dev]" && playwright install chromium
실행: python examples/demo_browser.py
"""
from browser_guard_mcp.browser import PlaywrightSession
from browser_guard_mcp.guard import DEMO_DIR, GuardConfig, GuardViolation, ensure_writable, validate_url

config = GuardConfig(allowed_domains=[], read_only=True)
session = PlaywrightSession()

try:
    print("=== 1) 동봉 데모 사이트로 실제 이동 ===")
    url = validate_url(str(DEMO_DIR / "index.html"), config)
    result = session.goto(url)
    print(result)

    print("\n=== 2) 페이지 텍스트 일부 ===")
    print(session.text()[:200])

    print("\n=== 3) 허용목록 밖 도메인 — 브라우저에 닿기 전에 가드가 차단 ===")
    try:
        validate_url("https://example.com", config)
    except GuardViolation as e:
        print(f"차단됨 (브라우저 호출 안 됨): {e}")

    print("\n=== 4) 읽기 전용 모드 — 클릭 시도도 브라우저에 닿기 전에 차단 ===")
    try:
        ensure_writable("click", config)
    except GuardViolation as e:
        print(f"차단됨 (브라우저 호출 안 됨): {e}")

    print("\n=== 5) 스크린샷 저장 (조회는 허용) ===")
    path = session.screenshot("/tmp/browser_guard_demo.png")
    print(f"저장됨: {path}")
finally:
    session.close()
