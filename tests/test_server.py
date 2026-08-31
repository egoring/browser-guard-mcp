# 서버 도구 테스트 — 모의 브라우저 세션을 주입해 가드·감사 로그 연동을 검증한다
from __future__ import annotations

from browser_guard_mcp import server
from browser_guard_mcp.audit import AuditLog
from browser_guard_mcp.guard import DEMO_DIR, GuardConfig


class FakeSession:
    """호출을 기록하고 정해진 값을 돌려주는 모의 브라우저 세션."""

    def __init__(self) -> None:
        """호출 기록 저장소를 초기화한다."""
        self.calls: list[tuple] = []

    def goto(self, url):
        """이동을 기록하고 이동 결과를 돌려준다."""
        self.calls.append(("goto", url))
        return {"url": url, "title": "가드 데모 상점"}

    def text(self):
        """고정 본문을 돌려준다."""
        self.calls.append(("text",))
        return "무선 마우스 — 19,000원 " * 50

    def click(self, selector):
        """클릭을 기록한다 (가드 통과 시에만 도달)."""
        self.calls.append(("click", selector))

    def fill(self, selector, value):
        """입력을 기록한다 (가드 통과 시에만 도달)."""
        self.calls.append(("fill", selector, value))

    def screenshot(self, path):
        """스크린샷 저장을 기록하고 경로를 돌려준다."""
        self.calls.append(("screenshot", path))
        return path


def _setup(read_only: bool = True, domains: list | None = None) -> FakeSession:
    """서버 전역 상태에 모의 세션·테스트 설정을 주입한다."""
    fake = FakeSession()
    server._state["session"] = fake
    server._state["config"] = GuardConfig(
        allowed_domains=domains if domains is not None else ["books.toscrape.com"],
        read_only=read_only,
        max_text_chars=200,
    )
    server._state["audit"] = AuditLog()
    return fake


def test_navigate_allowed_domain():
    """허용 도메인 이동은 세션에 전달되고 감사 로그에 ok로 남는다."""
    fake = _setup()
    result = server.browser_navigate("https://books.toscrape.com/")
    assert result["title"] == "가드 데모 상점"
    assert fake.calls[0][0] == "goto"
    log = server.browser_audit_log()["entries"]
    assert log[0]["action"] == "navigate" and log[0]["ok"] is True


def test_navigate_blocked_domain_never_reaches_browser():
    """차단된 도메인은 에러 dict로 돌아오고, 브라우저는 호출조차 되지 않는다."""
    fake = _setup()
    result = server.browser_navigate("https://google.com")
    assert "허용되지 않은 도메인" in result["error"]
    assert fake.calls == []  # 가드가 앞단에서 끊었다
    log = server.browser_audit_log()["entries"]
    assert log[0]["ok"] is False  # 차단 시도도 기록된다


def test_navigate_demo_site_always_allowed():
    """동봉 데모 사이트는 허용목록이 비어도 이동된다."""
    _setup(domains=[])
    result = server.browser_navigate(str(DEMO_DIR / "index.html"))
    assert "error" not in result


def test_click_blocked_in_read_only_mode():
    """읽기 전용(기본)에서 클릭은 거절되고 세션에 도달하지 않는다."""
    fake = _setup(read_only=True)
    result = server.browser_click(".order")
    assert "읽기 전용" in result["error"]
    assert fake.calls == []


def test_click_and_fill_allowed_when_writable():
    """읽기 전용을 끄면 클릭·입력이 세션까지 전달된다."""
    fake = _setup(read_only=False)
    assert server.browser_click(".order") == {"clicked": ".order"}
    assert server.browser_fill("#search", "마우스") == {"filled": "#search"}
    assert ("click", ".order") in fake.calls and ("fill", "#search", "마우스") in fake.calls


def test_get_text_truncated_by_guard():
    """긴 본문은 상한에서 잘리고 truncated=True가 붙는다."""
    _setup()
    result = server.browser_get_text()
    assert len(result["text"]) == 200 and result["truncated"] is True


def test_guard_status_reports_config():
    """상태 조회가 현재 가드 설정을 그대로 보여준다."""
    _setup(read_only=True)
    status = server.browser_guard_status()
    assert status["read_only"] is True
    assert status["allowed_domains"] == ["books.toscrape.com"]


def test_audit_log_orders_newest_first():
    """감사 로그는 최신순이고 허용·차단이 함께 남는다."""
    _setup()
    server.browser_navigate("https://books.toscrape.com/")
    server.browser_navigate("https://google.com")
    entries = server.browser_audit_log()["entries"]
    assert entries[0]["ok"] is False and entries[1]["ok"] is True
