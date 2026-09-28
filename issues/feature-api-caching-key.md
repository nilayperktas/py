# Feature: API Key Management, Caching & Rate-Limit Handling

## Summary
Add secure API key configuration, simple response caching, and rate-limit/backoff handling to reduce API failures and protect the key.

## Motivation
Currently the app uses public endpoints without explicit API key support. When switching to rate-limited or paid APIs (e.g., OpenWeatherMap), the app must safely manage keys and limit requests.

## Acceptance criteria
- API key is read from environment variables (or `.env`) and not hardcoded.
- Implement a server-side cache (in-memory, TTL-based) for geocoding and forecast responses.
- Detect HTTP 429 or rate-limit headers and implement exponential backoff or user-friendly error messages.
- Provide clear README notes on setting the API key and deploying securely.

## Implementation notes
- Use `python-dotenv` for local development, and `os.environ` for production.
- Implement a small in-memory cache (dict with expiry) or use `cachetools` library.
- Add unit tests for caching behavior and error handling.

## Suggested labels
backend, infra, security
