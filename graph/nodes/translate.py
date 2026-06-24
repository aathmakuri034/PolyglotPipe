"""Translation node (rate-limit aware).

PURPOSE
    Wrap the translation chain as a graph node, batching documents and staying
    within the API budget. Falls back to the local provider when needed.

WHAT TO BUILD HERE
    - A node function that pulls untranslated docs from state and translates them.
    - Rate-limit gating + provider fallback (Gemini -> local opus-mt).
    - Write translated docs and updated budget back to state.
"""
