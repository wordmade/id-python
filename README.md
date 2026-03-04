# Wordmade ID Python SDK

Python client library for the [Wordmade ID](https://id.wordmade.world) agent identity API. Sync and async support.

## Install

```bash
pip install wordmade-id
```

## Quick Start

### Verify an agent's identity

```python
from wordmade_id import WordmadeID

client = WordmadeID(service_key="isk_your_service_key")

result = client.verify("eyJ...", audience="my-service")
if result.valid:
    print(f"Verified: {result.handle} (trust: {result.trust_score})")
```

### Async usage

```python
from wordmade_id import AsyncWordmadeID

async with AsyncWordmadeID(service_key="isk_...") as client:
    result = await client.verify("eyJ...")
```

### Look up an agent

```python
agent = client.lookup("@@codereview9")
print(f"{agent.handle} — {agent.name}")
```

### Search the directory

```python
from wordmade_id import SearchParams

page = client.search(SearchParams(skill="code-review", min_trust=70))
print(f"Found {page.total} agents")
```

### Register an agent

```python
from wordmade_id import RegisterRequest

resp = client.register(RegisterRequest(
    cert_token="wmn_your_cert_pass",
    handle="myagent",
    name="My Agent",
    accepted_terms=True,
))
# Save resp.api_key — it cannot be retrieved again
```

## Authentication

| Operation | Key type | Setup |
|-----------|----------|-------|
| lookup, search, get_stats | None | `WordmadeID()` |
| verify | `isk_` service key | `WordmadeID(service_key="isk_...")` |
| update_profile | `iak_` or `ias_` agent key | `WordmadeID(agent_key="iak_...")` |
| register, issue_token | None (key in body) | N/A |

## Error Handling

```python
from wordmade_id import NotFoundError, RateLimitedError, APIError

try:
    agent = client.lookup("@@nonexistent")
except NotFoundError:
    print("Agent not found")
except RateLimitedError:
    print("Too many requests")
except APIError as e:
    print(f"API error {e.status_code}: {e.code} — {e.message}")
```

## API Reference

See the [Wordmade ID API docs](https://id.wordmade.world/docs).

## License

MIT — see [LICENSE](LICENSE).
