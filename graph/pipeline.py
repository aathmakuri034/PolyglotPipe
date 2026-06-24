"""Graph assembly (the single entry point for orchestration).

PURPOSE
    Wire the nodes and edges into one runnable LangGraph StateGraph, with
    checkpointing for resume-across-sleep. Everything else imports from here.

WHAT TO BUILD HERE
    - Construct a StateGraph over the shared state (graph/state.py, shared file).
    - Register nodes (ingest, translate, embed, query) and conditional edges.
    - Attach a checkpointer and expose a compiled, runnable graph.
"""
