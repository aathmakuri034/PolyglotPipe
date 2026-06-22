class RetrievalError(Exception):
    """Base for all retrieval-layer failures."""


class StoreError(RetrievalError):
    """Vector / lexical store failed."""


class EmbeddingError(RetrievalError):
    """Embedding model failed."""


class RerankerError(RetrievalError):
    """Cross-encoder reranker failed."""
