# 가드 정책 단위 테스트 — 브라우저·네트워크 없이 검증한다
from __future__ import annotations

import pytest

from browser_guard_mcp.guard import (
    DEMO_DIR,
    GuardConfig,
    GuardViolation,
    clip_text,
    ensure_writable,
    validate_url,
)


def _cfg(**kw) -> GuardConfig:
    """테스트용 설정을 만든다."""
    base = {"allowed_domains": ["books.toscrape.com"], "read_only": True, "max_text_chars": 100}
    base.update(kw)
    return GuardConfig(**base)


def test_allowed_domain_passes():
    """허용 도메인은 통과한다."""
    assert validate_url("https://books.toscrape.com/catalogue", _cfg()).startswith("https://")


def test_subdomain_of_allowed_passes():
    """허용 도메인의 서브도메인도 통과한다."""
    validate_url("https://www.books.toscrape.com/", _cfg())


def test_unlisted_domain_blocked_with_allowlist_in_message():
    """목록 밖 도메인은 거절되고, 메시지에 허용 목록이 안내된다."""
    with pytest.raises(GuardViolation, match="books.toscrape.com"):
        validate_url("https://google.com", _cfg())


def test_lookalike_domain_blocked():
    """끝만 비슷한 위장 도메인(evil-books.toscrape.com.attacker.io)은 통과하지 못한다."""
    with pytest.raises(GuardViolation):
        validate_url("https://books.toscrape.com.attacker.io/", _cfg())


def test_demo_site_file_passes_without_allowlist():
    """동봉 데모 사이트는 허용목록이 비어 있어도 열 수 있다."""
    uri = validate_url(str(DEMO_DIR / "index.html"), _cfg(allowed_domains=[]))
    assert uri.startswith("file://")


def test_local_file_outside_demo_blocked():
    """데모 폴더 밖 로컬 파일(임의 파일 열람)은 차단된다."""
    with pytest.raises(GuardViolation, match="데모 사이트"):
        validate_url("/etc/passwd", _cfg())


def test_empty_url_blocked():
    """빈 URL은 안내와 함께 거절된다."""
    with pytest.raises(GuardViolation, match="빈 URL"):
        validate_url("  ", _cfg())


def test_read_only_blocks_click_and_fill():
    """읽기 전용 모드에서는 click·fill이 거절되고 해제 방법이 안내된다."""
    for action in ("click", "fill"):
        with pytest.raises(GuardViolation, match="읽기 전용"):
            ensure_writable(action, _cfg())


def test_writable_mode_allows_actions():
    """읽기 전용을 끄면 상호작용 동작이 허용된다."""
    ensure_writable("click", _cfg(read_only=False))  # 예외 없어야 함


def test_clip_text_truncates_and_flags():
    """상한 초과 텍스트는 잘리고 truncated=True로 표시된다."""
    text, truncated = clip_text("가" * 150, _cfg())
    assert len(text) == 100 and truncated
    text, truncated = clip_text("짧다", _cfg())
    assert text == "짧다" and not truncated


def test_config_from_env(monkeypatch):
    """환경 변수 파싱 — 공백 정리·소문자화·읽기 전용 기본값."""
    monkeypatch.setenv("BROWSERGUARD_ALLOWED_DOMAINS", " Books.toscrape.com , quotes.toscrape.com ")
    monkeypatch.delenv("BROWSERGUARD_READ_ONLY", raising=False)
    c = GuardConfig.from_env()
    assert c.allowed_domains == ["books.toscrape.com", "quotes.toscrape.com"]
    assert c.read_only is True  # 기본은 안전한 쪽
