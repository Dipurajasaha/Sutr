import numpy as np
import pytest

from app.api.endpoints import _sanitize_chunk_text


def test_sanitize_chunk_text_none_returns_empty():
    assert _sanitize_chunk_text(None) == ""


def test_sanitize_chunk_text_bytes_and_nulls():
    raw = b"hello\x00world"
    out = _sanitize_chunk_text(raw)
    assert "\x00" not in out
    assert out == "helloworld"


def test_sanitize_chunk_text_str_trims_and_encodes():
    s = "  text with spaces  "
    assert _sanitize_chunk_text(s) == "text with spaces"


@pytest.mark.parametrize("count", [1, 3])
def test_vector_store_methods_monkeypatched(monkeypatch, count):
    # Patch SentenceTransformer to avoid loading real model
    class DummyModel:
        def encode(self, texts):
            # return deterministic vectors
            return [[0.1] * 384 for _ in texts]

    class FakeIndex:
        def __init__(self, dim):
            self.ntotal = 0

        def add(self, embeddings):
            self.ntotal += len(embeddings)

        def search(self, query_vector, top_k):
            # return zeros distances and increasing indices
            distances = np.zeros((1, top_k), dtype=np.float32)
            indices = np.tile(np.arange(top_k, dtype=np.int64), (1, 1))
            return distances, indices

    class FakeFaissModule:
        IndexFlatL2 = FakeIndex

        @staticmethod
        def write_index(index, path):
            return None
        @staticmethod
        def read_index(path):
            return FakeIndex(None)

    monkeypatch.setattr("app.services.embedding_service.SentenceTransformer", lambda name: DummyModel())
    monkeypatch.setattr("app.services.embedding_service.faiss", FakeFaissModule)

    # import here to use patched modules
    from app.services.embedding_service import VectorStoreManager

    store = VectorStoreManager()

    texts = [f"text {i}" for i in range(count)]
    embeddings = store.generate_embeddings(texts)
    assert embeddings.shape[0] == count

    faiss_ids = store.add_to_index(embeddings)
    assert len(faiss_ids) == count

    distances, indices = store.search_index("query", top_k=2)
    assert isinstance(distances, list)
    assert isinstance(indices, list)
