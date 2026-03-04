"""Minimal example: verify an agent's identity token."""

from wordmade_id import WordmadeID

client = WordmadeID(service_key="isk_your_service_key")

# Verify a JWT identity token
result = client.verify("eyJ...", audience="my-service")

if result.valid:
    print(f"Verified: {result.handle} ({result.uuid})")
    print(f"Trust score: {result.trust_score}, Cert level: {result.cert_level}")
else:
    print(f"Invalid: {result.error}")
