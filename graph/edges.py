"""Conditional edge logic (the routing brain of the graph).

PURPOSE
    Decide which node runs next based on the current state — e.g. budget
    exhausted -> use local provider, more files pending -> loop back to ingest.

WHAT TO BUILD HERE
    - Predicate functions that read state and return the next node name.
    - Routing for: provider fallback, retry-after-rate-limit, and completion.
    - Keep decisions pure (read state, return a label) for easy testing.
"""
