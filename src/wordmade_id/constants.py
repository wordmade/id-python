"""Constants for the Wordmade ID SDK."""

DEFAULT_BASE_URL = "https://api.id.wordmade.world"
DEFAULT_TIMEOUT = 10.0  # seconds

# Field length limits (mirrors constants.go in the ID service)
MAX_NAME_LEN = 128
MAX_BIO_ONELINER = 256
MAX_BIO_LEN = 4096
MAX_CAPABILITIES = 50
MAX_CAPABILITY_LEN = 64
