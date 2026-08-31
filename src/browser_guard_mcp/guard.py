# 가드 정책 — 도메인 허용목록·읽기 전용 모드·텍스트 상한을 코드로 강제한다
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

# 동봉 데모 사이트 위치 — 허용목록이 비어 있어도 여기만은 항상 열 수 있다
DEMO_DIR = Path(__file__).resolve().parents[2] / "demo_site"


class GuardViolation(ValueError):
    """가드 위반 — 에이전트가 읽고 다음 행동을 정할 수 있는 메시지를 담는다."""


@dataclass
class GuardConfig:
    """가드 설정. 환경 변수로 재정의한다.

    BROWSERGUARD_ALLOWED_DOMAINS  콤마 구분 허용 도메인 (기본: 없음 — 데모 사이트만)
    BROWSERGUARD_READ_ONLY        "false"일 때만 클릭·입력 허용 (기본: true — 안전 기본값)
    BROWSERGUARD_MAX_TEXT         get_text 반환 상한 문자 수 (기본 20000)
    """

    allowed_domains: list[str] = field(default_factory=list)
    read_only: bool = True
    max_text_chars: int = 20000

    @classmethod
    def from_env(cls) -> "GuardConfig":
        """환경 변수에서 설정을 읽는다. 읽기 전용이 기본값 — 끄려면 명시적으로 꺼야 한다."""
        raw = os.environ.get("BROWSERGUARD_ALLOWED_DOMAINS", "")
        domains = [d.strip().lower() for d in raw.split(",") if d.strip()]
        return cls(
            allowed_domains=domains,
            read_only=os.environ.get("BROWSERGUARD_READ_ONLY", "true").lower() != "false",
            max_text_chars=int(os.environ.get("BROWSERGUARD_MAX_TEXT", "20000")),
        )


def _domain_allowed(host: str, allowed: list[str]) -> bool:
    """호스트가 허용 도메인과 일치하거나 그 서브도메인인지 확인한다."""
    host = host.lower()
    return any(host == d or host.endswith("." + d) for d in allowed)


def validate_url(url: str, config: GuardConfig) -> str:
    """이동 대상 URL을 검증한다 — 허용목록 밖이면 GuardViolation.

    - http/https: 도메인 허용목록 대조 (서브도메인 포함)
    - file/로컬 경로: 동봉 demo_site 안의 파일만 허용 (임의 로컬 파일 열람 차단)
    """
    if not url or not url.strip():
        raise GuardViolation("빈 URL입니다. 이동할 주소를 지정하세요.")
    url = url.strip()

    parsed = urlparse(url)
    if parsed.scheme in ("http", "https"):
        if not _domain_allowed(parsed.netloc.split(":")[0], config.allowed_domains):
            raise GuardViolation(
                f"허용되지 않은 도메인입니다: {parsed.netloc}. "
                f"허용 목록: {config.allowed_domains or '[없음 — 동봉 데모 사이트만 가능]'}. "
                "BROWSERGUARD_ALLOWED_DOMAINS로 추가할 수 있습니다."
            )
        return url

    # file:// 또는 스킴 없는 로컬 경로 -> demo_site 내부만 허용
    path = Path(parsed.path if parsed.scheme == "file" else url)
    try:
        resolved = path.resolve()
        resolved.relative_to(DEMO_DIR)
    except (ValueError, OSError):
        raise GuardViolation(
            f"로컬 파일은 동봉 데모 사이트({DEMO_DIR})만 열 수 있습니다: {url}"
        ) from None
    return resolved.as_uri()


def ensure_writable(action: str, config: GuardConfig) -> None:
    """클릭·입력 같은 '만지는' 동작이 허용 모드인지 확인한다.

    읽기 전용 모드(기본)에서는 navigate·get_text·screenshot만 가능하다 —
    모델이 조심하길 기대하지 말고, 부주의가 불가능하게 만든다.
    """
    if config.read_only:
        raise GuardViolation(
            f"읽기 전용 모드에서는 '{action}' 동작을 할 수 없습니다. "
            "조회(navigate·get_text·screenshot)만 가능합니다. "
            "상호작용이 필요하면 BROWSERGUARD_READ_ONLY=false로 서버를 재시작하세요."
        )


def clip_text(text: str, config: GuardConfig) -> tuple[str, bool]:
    """페이지 텍스트를 상한 문자 수로 자른다 — 컨텍스트 윈도 범람 방지."""
    if len(text) <= config.max_text_chars:
        return text, False
    return text[: config.max_text_chars], True
