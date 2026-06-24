import pytest
from langchain_core.documents import Document

from polyglotpipe.retrieval.exceptions import StoreError
from polyglotpipe.retrieval.store import PgVectorStore
from polyglotpipe.retrieval.types import SearchFilters

pytestmark = pytest.mark.asyncio


def _doc(path: str, content: str, lang: str = "en", media: str = "pdf") -> Document:
    return Document(
        page_content=content,
        metadata={
            "source_path": path,
            "source_lang": lang,
            "target_lang": "en",
            "media_type": media,
            "confidence": 0.9,
            "chunk_index": 0,
        },
    )


async def test_add_and_dense_search(store: PgVectorStore) -> None:
    ids = await store.add_documents(
        [
            _doc("/a.pdf", "revenue grew 12 percent in Q3"),
            _doc("/b.pdf", "compliance update for GDPR"),
        ]
    )
    assert len(ids) == 2

    results = await store.search_dense(
        store._embedder.embed(["how did revenue change"])[0],
        top_k=2,
        filters=None,
    )
    assert {r.source_path for r in results} == {"/a.pdf", "/b.pdf"}


async def test_lexical_search_matches_token(store: PgVectorStore) -> None:
    await store.add_documents(
        [
            _doc("/a.pdf", "revenue grew 12 percent in Q3"),
            _doc("/b.pdf", "compliance update for GDPR"),
        ]
    )
    results = await store.search_lexical("revenue", top_k=5, filters=None)
    assert len(results) == 1
    assert results[0].source_path == "/a.pdf"


async def test_filters_applied(store: PgVectorStore) -> None:
    await store.add_documents(
        [
            _doc("/a.pdf", "alpha", media="pdf"),
            _doc("/b.wav", "alpha", media="audio"),
        ]
    )
    results = await store.search_lexical(
        "alpha",
        top_k=5,
        filters=SearchFilters(media_type="audio"),
    )
    assert [r.media_type for r in results] == ["audio"]


async def test_upsert_replaces_content(store: PgVectorStore) -> None:
    await store.add_documents([_doc("/a.pdf", "old text")])
    await store.add_documents([_doc("/a.pdf", "new text")])
    results = await store.search_lexical("text", top_k=5, filters=None)
    assert len(results) == 1
    assert results[0].content == "new text"


async def test_store_error_when_setup_skipped() -> None:
    from polyglotpipe.retrieval.config import Settings
    from polyglotpipe.retrieval.embedder import Embedder

    s = PgVectorStore(
        Settings(database_url="postgresql://x:y@localhost/z"),  # type: ignore[arg-type]
        Embedder(Settings(database_url="postgresql://x:y@localhost/z")),  # type: ignore[arg-type]
    )
    with pytest.raises(StoreError):
        await s.search_lexical("x", 1, None)
