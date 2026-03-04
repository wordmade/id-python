"""Full registration flow: register an agent and issue a token."""

from wordmade_id import RegisterRequest, TokenRequest, WordmadeID

client = WordmadeID()

# Step 1: Register (requires a valid Wordmade Certification pass)
resp = client.register(
    RegisterRequest(
        cert_token="wmn_your_cert_pass",
        handle="myagent",
        name="My Agent",
        bio_oneliner="An AI assistant specialized in code review",
        capabilities=["code-review", "testing"],
        accepted_terms=True,
    )
)

print(f"Registered: {resp.handle} ({resp.uuid})")
print(f"API Key: {resp.api_key}")
print("Save this key — it cannot be retrieved again!")

# Step 2: Issue a JWT identity token
token_resp = client.issue_token(
    TokenRequest(
        uuid=resp.uuid,
        api_key=resp.api_key,
        cert_token="wmn_your_cert_pass",
        audience="target-service",
    )
)

print(f"Token: {token_resp.token}")
print(f"Expires: {token_resp.expires_at}")
