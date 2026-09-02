# browser-guard-mcp

[![CI](https://github.com/egoring/browser-guard-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/egoring/browser-guard-mcp/actions/workflows/ci.yml)

> English: [README.en.md](README.en.md) · 설계 문서: [docs/설계서.md](docs/설계서.md)

**AI 에이전트를 위한 브라우저 자동화 — 다층 안전 가드 내장 MCP 서버.**

LLM 에이전트에 브라우저를 그대로 열어주는 건 위험합니다. 이 서버는 Playwright를 가드 뒤에서 열어줍니다 — 허용된 도메인만 이동하고, 기본은 읽기 전용이며, 모든 행동(차단된 시도 포함)이 감사 로그에 남습니다.

## 이런 상황에서 씁니다

**상황** — 운영팀이 매일 아침 경쟁사·제휴사 페이지 몇 곳을 눈으로 확인한다(가격, 공지, 재고). 에이전트에게 시키고 싶지만, 브라우저를 통째로 주면 엉뚱한 사이트로 가거나 뭔가 눌러버릴까 불안하다.

**도입 후** — 확인 대상 도메인만 허용목록에 넣고 읽기 전용으로 물린다. "이 세 페이지 열어서 가격 바뀐 것 있는지 알려줘"가 안전한 일상 업무가 된다 — 클릭·제출은 코드 수준에서 불가능하고, 에이전트가 어디서 무엇을 봤는지(차단된 시도까지) 감사 로그에 남는다.

## 가드 계층

| 계층 | 막는 것 |
|---|---|
| **도메인 허용목록** | 의도 밖 사이트 이동 — 위장 도메인(`허용도메인.attacker.io`)도 차단 |
| **로컬 파일 격리** | 임의 파일 열람 — 동봉 데모 사이트 폴더 밖은 경로 탈출 포함 전부 거절 |
| **읽기 전용 기본값** | 의도 밖 클릭·입력 — 끄려면 명시적으로 `BROWSERGUARD_READ_ONLY=false` |
| **텍스트 상한** | 컨텍스트 윈도 범람 — 초과분은 잘리고 `truncated` 표시 |
| **세션 수준 차단** | 다운로드 거부, 팝업·새 탭 즉시 닫기 |
| **감사 로그** | 추적 불가 — 모든 행동이 시간순 기록, 에이전트도 자기 기록을 조회 가능 |

## 도구

`browser_navigate` · `browser_get_text` · `browser_click` · `browser_fill` · `browser_screenshot` · `browser_guard_status` · `browser_audit_log`

## 데모

동봉된 가짜 쇼핑몰(`demo_site/`)로 외부 인터넷 없이 시연할 수 있습니다.

- "데모 상점 열어서 3만 원 이하 상품 알려줘" → 정상 조회
- "무선 마우스 주문해줘" → **거절** — 읽기 전용 모드라 클릭 불가, 에이전트가 이유를 설명
- "구글에서 검색해봐" → **거절** — 허용목록 밖, 허용된 도메인 목록 안내

프롬프트가 아니라 코드가 강제하는 안전입니다.

## 설치

```bash
pip install -e .
playwright install chromium

export BROWSERGUARD_ALLOWED_DOMAINS="books.toscrape.com,quotes.toscrape.com"
export BROWSERGUARD_READ_ONLY="true"   # 기본값 — 조회·스크린샷만
```

Claude Desktop 설정은 [examples/](examples/claude_desktop_config.json) 참조.

## 테스트

```bash
pip install -e ".[dev]"
pytest   # 19건, 브라우저·네트워크 불필요 — 위장 도메인, 경로 탈출, 읽기 전용, 차단 시 브라우저 미호출
```

## 함께 보기

- [sql-guard-mcp](https://github.com/egoring/sql-guard-mcp) — 같은 원칙의 SQL 버전: 능력을 주되 부주의를 불가능하게
- [judge-mcp](https://github.com/egoring/judge-mcp) · [log-triage-agent](https://github.com/egoring/log-triage-agent) · [llm-sse-gateway](https://github.com/egoring/llm-sse-gateway)

## 라이선스

MIT
