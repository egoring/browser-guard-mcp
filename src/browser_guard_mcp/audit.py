# 감사 로그 — 에이전트의 모든 브라우저 액션(허용·차단)을 시간순으로 기록한다
from __future__ import annotations

from datetime import datetime, timezone


class AuditLog:
    """액션 기록 저장소 (프로세스 메모리).

    사고가 났을 때 "에이전트가 무엇을 했는가"를 재생하기 위한 블랙박스다.
    차단된 시도도 기록한다 — 차단 이력 자체가 중요한 관측 신호다.
    """

    def __init__(self, max_entries: int = 500) -> None:
        """보관 상한을 받는다. 넘치면 오래된 것부터 버린다."""
        self.max_entries = max_entries
        self._entries: list[dict] = []

    def record(self, action: str, target: str, ok: bool, detail: str = "") -> None:
        """액션 하나를 기록한다 — 시각·동작·대상·허용 여부·부가 정보."""
        self._entries.append({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "action": action,
            "target": target[:200],
            "ok": ok,
            "detail": detail[:200],
        })
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]

    def recent(self, limit: int = 50) -> list[dict]:
        """최근 기록을 최신순으로 돌려준다."""
        return list(reversed(self._entries[-limit:]))
