# browser-guard-mcp 서버 본체 — 가드를 통과한 요청만 Playwright 세션에 전달한다
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .audit import AuditLog
from .browser import BrowserError, PlaywrightSession
from .guard import GuardConfig, GuardViolation, clip_text, ensure_writable, validate_url

mcp = FastMCP(
    "browser-guard-mcp",
    instructions=(
        "다층 가드를 두른 브라우저 자동화 서버. 허용된 도메인과 동봉 데모 사이트만 이동할 수 있고, "
        "기본은 읽기 전용(조회·스크린샷만)이다. 클릭·입력이 거절되면 그 이유가 메시지에 담긴다. "
        "설정: BROWSERGUARD_ALLOWED_DOMAINS(콤마 구분), BROWSERGUARD_READ_ONLY(기본 true), "
        "BROWSERGUARD_MAX_TEXT."
    ),
)

# 프로세스 전역 상태 — 세션은 지연 생성, 테스트에서는 모의 객체로 교체한다
_state: dict = {"session": None, "config": None, "audit": AuditLog()}


def _config() -> GuardConfig:
    """가드 설정을 확정한다 (최초 1회 환경 변수에서)."""
    if _state["config"] is None:
        _state["config"] = GuardConfig.from_env()
    return _state["config"]


def _session():
    """브라우저 세션을 확정한다 (최초 1회 생성 — lazy)."""
    if _state["session"] is None:
        _state["session"] = PlaywrightSession()
    return _state["session"]


def _blocked(action: str, target: str, e: Exception) -> dict:
    """차단·실패를 감사 로그에 남기고 에이전트가 읽을 에러 dict로 바꾼다."""
    _state["audit"].record(action, target, ok=False, detail=str(e))
    return {"error": str(e)}


@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
def browser_navigate(
    url: Annotated[str, Field(description="이동할 주소 (허용 도메인 또는 동봉 데모 사이트 경로)")],
) -> dict:
    """허용목록을 통과한 URL로 이동한다. 반환: 최종 URL·페이지 제목."""
    try:
        safe = validate_url(url, _config())
        result = _session().goto(safe)
    except (GuardViolation, BrowserError) as e:
        return _blocked("navigate", url, e)
    _state["audit"].record("navigate", result["url"], ok=True)
    return result


@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
def browser_get_text() -> dict:
    """현재 페이지의 보이는 텍스트를 추출한다. 상한 초과 시 truncated=True로 잘라 낸다."""
    try:
        raw = _session().text()
    except BrowserError as e:
        return _blocked("get_text", "-", e)
    text, truncated = clip_text(raw, _config())
    _state["audit"].record("get_text", f"{len(text)}자", ok=True)
    return {"text": text, "truncated": truncated}


@mcp.tool(annotations={"readOnlyHint": False, "openWorldHint": False})
def browser_click(
    selector: Annotated[str, Field(description="클릭할 요소의 CSS 셀렉터")],
) -> dict:
    """요소를 클릭한다. 읽기 전용 모드(기본)에서는 거절된다."""
    try:
        ensure_writable("click", _config())
        _session().click(selector)
    except (GuardViolation, BrowserError) as e:
        return _blocked("click", selector, e)
    _state["audit"].record("click", selector, ok=True)
    return {"clicked": selector}


@mcp.tool(annotations={"readOnlyHint": False, "openWorldHint": False})
def browser_fill(
    selector: Annotated[str, Field(description="입력 요소의 CSS 셀렉터")],
    value: Annotated[str, Field(description="입력할 값")],
) -> dict:
    """입력 요소에 값을 채운다. 읽기 전용 모드(기본)에서는 거절된다."""
    try:
        ensure_writable("fill", _config())
        _session().fill(selector, value)
    except (GuardViolation, BrowserError) as e:
        return _blocked("fill", selector, e)
    _state["audit"].record("fill", selector, ok=True)
    return {"filled": selector}


@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
def browser_screenshot() -> dict:
    """현재 화면을 PNG로 저장하고 파일 경로를 돌려준다."""
    path = str(Path(tempfile.gettempdir()) / "browser_guard_shot.png")
    try:
        saved = _session().screenshot(path)
    except BrowserError as e:
        return _blocked("screenshot", path, e)
    _state["audit"].record("screenshot", saved, ok=True)
    return {"path": saved}


@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
def browser_guard_status() -> dict:
    """현재 가드 설정(허용 도메인·읽기 전용 여부·텍스트 상한)을 돌려준다."""
    c = _config()
    return {
        "allowed_domains": c.allowed_domains,
        "read_only": c.read_only,
        "max_text_chars": c.max_text_chars,
        "demo_site": "동봉 demo_site/는 허용목록과 무관하게 항상 열 수 있음",
    }


@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
def browser_audit_log(
    limit: Annotated[int, Field(ge=1, le=500, description="가져올 기록 수")] = 50,
) -> dict:
    """감사 로그를 최신순으로 돌려준다 — 차단된 시도까지 전부 기록돼 있다."""
    return {"entries": _state["audit"].recent(limit)}


def main() -> None:
    """stdio 트랜스포트로 서버를 실행한다 (Claude Desktop 등 로컬 클라이언트용)."""
    mcp.run()


if __name__ == "__main__":
    main()
