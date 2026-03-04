# Wordmade ID Python SDK

Public Python package wrapping the Wordmade ID REST API.

## What This Is

A Python client library (sync + async) for the Wordmade ID agent identity
service. Enables Python applications to register agents, verify identity
tokens, search the directory, and manage profiles.

## Structure

```
src/wordmade_id/
  __init__.py          Re-exports: WordmadeID, AsyncWordmadeID
  client.py            Sync client (httpx)
  async_client.py      Async client (httpx async)
  types.py             Dataclasses: Agent, VerifyResult, etc.
  errors.py            APIError, NotFoundError, RateLimitedError
  constants.py         Base URL, version, field limits
  _version.py          __version__
tests/
  conftest.py          Shared fixtures, httpx mock transport
  test_client.py       Sync client tests
  test_async_client.py Async client tests
examples/
  quickstart.py        Minimal verify example
  register_agent.py    Full registration flow
```

## Building

```bash
make test              # pytest
make lint              # ruff check + format
make type-check        # mypy --strict
make install-dev       # pip install -e .
```

## Source Sync

Types and API surface mirror the Go SDK (id-go), which derives from the
private `wordmade/id` repo's `internal/mcpserver/client.go`.

**Sync direction:** private `wordmade/id` -> `wordmade/id-go` -> `wordmade/id-python`

## CI/CD

- **CI** (`ci.yml`): Lint, test, type-check, scrub scan (infra + identity leaks)
- **Release** (`release.yml`): Triggered by `v*` tags, publishes to PyPI
