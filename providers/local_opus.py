"""Local opus-mt translation provider (offline CPU fallback).

PURPOSE
    Translate without the cloud — used when the Gemini free-tier budget is
    exhausted or the network is down. Runs Helsinki-NLP/opus-mt models on CPU.

WHAT TO BUILD HERE
    - A LocalOpusProvider implementing the translation interface from base.py.
    - Lazy model/tokenizer loading, with graceful handling of out-of-memory.
    - Per-language-pair model selection (tokens_used = 0, no API cost).
"""
