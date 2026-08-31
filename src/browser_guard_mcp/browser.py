# Playwright 세션 래퍼 — 실제 브라우저 조작을 한 곳에 모은다 (테스트는 모의 세션으로 대체)
from __future__ import annotations

from pathlib import Path


class BrowserError(RuntimeError):
    """브라우저 조작 실패 — 원인과 대처를 담은 메시지로 던진다."""


class PlaywrightSession:
    """headless Chromium 세션 하나를 감싼다.

    안전 설정을 세션 수준에서 강제한다:
    - 다운로드 거부(accept_downloads=False) — 파일 저장 자체가 불가능
    - 새 탭·팝업은 즉시 닫음 — 에이전트는 항상 탭 하나만 다룬다
    첫 사용 시점에 브라우저를 띄운다(lazy) — 서버 기동은 가볍게.
    """

    def __init__(self) -> None:
        """지연 초기화 준비만 한다. 실제 브라우저는 첫 호출 때 뜬다."""
        self._pw = None
        self._page = None

    def _ensure(self):
        """브라우저·페이지를 준비한다. Playwright 미설치면 설치 안내와 함께 실패."""
        if self._page is not None:
            return self._page
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise BrowserError(
                "playwright 패키지가 없습니다. `pip install playwright && playwright install chromium`으로 설치하세요."
            ) from e
        self._pw = sync_playwright().start()
        browser = self._pw.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=False)
        context.on("page", lambda p: p.close())  # 팝업·새 탭은 열리는 즉시 닫는다
        self._page = context.new_page()
        return self._page

    def goto(self, url: str) -> dict:
        """URL로 이동해 최종 URL과 제목을 돌려준다."""
        page = self._ensure()
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        return {"url": page.url, "title": page.title()}

    def text(self) -> str:
        """현재 페이지의 보이는 텍스트를 추출한다."""
        return self._ensure().inner_text("body")

    def click(self, selector: str) -> None:
        """셀렉터 요소를 클릭한다 (쓰기 가드 통과 후에만 호출됨)."""
        self._ensure().click(selector, timeout=5000)

    def fill(self, selector: str, value: str) -> None:
        """입력 요소에 값을 채운다 (쓰기 가드 통과 후에만 호출됨)."""
        self._ensure().fill(selector, value, timeout=5000)

    def screenshot(self, path: str) -> str:
        """현재 화면을 PNG로 저장하고 경로를 돌려준다."""
        p = Path(path)
        self._ensure().screenshot(path=str(p))
        return str(p)

    def close(self) -> None:
        """브라우저와 Playwright 런타임을 정리한다."""
        if self._pw is not None:
            self._pw.stop()
            self._pw = self._page = None
