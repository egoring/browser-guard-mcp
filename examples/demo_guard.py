"""가드 동작을 눈으로 확인하는 예시 스크립트 (브라우저 실행 없이 로직만 테스트).

실행: python examples/demo_guard.py
"""
from browser_guard_mcp.guard import (
    DEMO_DIR,
    GuardConfig,
    GuardViolation,
    clip_text,
    ensure_writable,
    validate_url,
)

config = GuardConfig(allowed_domains=["books.toscrape.com"], read_only=True, max_text_chars=50)

print("=== 1) 허용 도메인 이동 ===")
print(validate_url("https://books.toscrape.com/index.html", config))

print("\n=== 2) 위장 도메인 차단 (허용도메인.attacker.io) ===")
try:
    validate_url("https://books.toscrape.com.attacker.io/", config)
except GuardViolation as e:
    print(f"차단됨: {e}")

print("\n=== 3) 허용목록 밖 도메인 차단 ===")
try:
    validate_url("https://google.com/search?q=test", config)
except GuardViolation as e:
    print(f"차단됨: {e}")

print("\n=== 4) 로컬 파일 경로 탈출 차단 ===")
try:
    validate_url("/etc/passwd", config)
except GuardViolation as e:
    print(f"차단됨: {e}")

print("\n=== 5) 동봉 데모 사이트는 허용 ===")
print(validate_url(str(DEMO_DIR / "index.html"), config))

print("\n=== 6) 읽기 전용 모드에서 클릭 차단 ===")
try:
    ensure_writable("click", config)
except GuardViolation as e:
    print(f"차단됨: {e}")

print("\n=== 7) 텍스트 상한 초과 시 잘림 ===")
long_text = "가" * 100
clipped, truncated = clip_text(long_text, config)
print(f"길이: {len(clipped)}자, truncated={truncated}")
