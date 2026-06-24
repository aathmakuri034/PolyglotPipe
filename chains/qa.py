"""QA / RAG generation chain (Gemini Flash).

PURPOSE
    Take retrieved context + a user question and produce a grounded, cited
    answer. This is the most coupled chain — it consumes Engineer B's retriever
    output, so respect the Query Protocol (Contract 2).

WHAT TO BUILD HERE
    - A RAG prompt template that grounds answers in retrieved context.
    - Citation/provenance handling (source_path, timestamp).
    - Output shaped to QueryResult (answer, sources, tokens_used).
"""
