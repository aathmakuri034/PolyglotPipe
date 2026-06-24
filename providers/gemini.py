"""Gemini API provider (cloud backend, free tier).

PURPOSE
    Concrete implementation of the provider interfaces backed by Gemini
    (ChatGoogleGenerativeAI). Used for translation, summarization, and QA.

WHAT TO BUILD HERE
    - A GeminiProvider class implementing base.py's interfaces.
    - Route every call through rate_limiter.py to respect 15 RPM / 1000 RPD.
    - try/except with structured logging + exponential backoff on API errors.
    - Map raw responses into the standardized result type.
"""
