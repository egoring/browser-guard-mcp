# browser-guard-mcp

[![CI](https://github.com/egoring/browser-guard-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/egoring/browser-guard-mcp/actions/workflows/ci.yml)

> 한국어: [README.md](README.md) · Design doc (Korean): [docs/설계서.md](docs/설계서.md)

**Browser automation for AI agents — an MCP server with layered safety guards.**

Handing an LLM agent a raw browser is dangerous. This server wraps Playwright behind guards: only allowlisted domains, read-only by default, and every action (including blocked attempts) lands in an audit log.

## Guard layers

Domain allowlist (lookalike domains blocked) · local-file isolation (bundled demo site only, path-escape safe) · read-only default (`BROWSERGUARD_READ_ONLY=false` to enable interaction) · text cap with `truncated` flag · session-level blocks (no downloads, popups closed instantly) · audit log queryable by the agent itself.

## Tools

`browser_navigate` · `browser_get_text` · `browser_click` · `browser_fill` · `browser_screenshot` · `browser_guard_status` · `browser_audit_log`

## Install

```bash
pip install -e .
playwright install chromium
export BROWSERGUARD_ALLOWED_DOMAINS="books.toscrape.com"
```

## Tests

```bash
pip install -e ".[dev]"
pytest   # 19 tests, no browser/network — lookalike domains, path escape, read-only, guard-before-browser
```

## License

MIT
