"""Abstract provider interfaces (the contract every model backend implements).

PURPOSE
    Define *what* a provider can do — without saying *how*. The chains and graph
    nodes import these interfaces, never a concrete provider, so cloud (Gemini)
    and local (opus-mt) backends can be swapped transparently.

WHAT TO BUILD HERE
    - Abstract base classes for chat/completion and translation.
    - A standardized result type (text, tokens_used, model, confidence).
    - Abstract methods like complete(), translate(), is_available().
"""
