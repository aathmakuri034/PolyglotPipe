"""Rate-limit-aware wrapper for the Gemini free tier.

PURPOSE
    Keep every cloud call inside the free-tier budget. All Gemini requests
    funnel through here so limits are enforced in exactly one place.

WHAT TO BUILD HERE
    - A RateLimiter that tracks request timestamps (sliding window).
    - Enforce both per-minute (RPM) and per-day (RPD) limits.
    - seconds_until_available() / acquire() to gate or block callers.
    - Exponential backoff helper for retrying transient API failures.
"""
