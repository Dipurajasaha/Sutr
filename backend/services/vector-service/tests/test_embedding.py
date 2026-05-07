import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from app.services.embedding_service import vector_store, VectorStoreManager

def test_generate_embeddings():
    # Setup our mocked SentenceTransformer to return dummy data
    vector_store.model.encode.return_value = [[0.1, 0.2, 0.3]]
    
    result = vector_store.generate_embeddings(["dummy text"])
    
    assert isinstance(result, np.ndarray)
    assert result.shape == (1, 3)
    vector_store.model.encode.assert_called_once_with(["dummy text"])

def test_add_to_index():
    # Setup our mocked FAISS index
    vector_store.index.ntotal = 5
    embeddings = np.array([[0.1, 0.2]])
    
    ids = vector_store.add_to_index(embeddings)
    
    assert ids == [5]
    vector_store.index.add.assert_called_once()

def test_search_index():
    # Setup mocked search results
    vector_store.model.encode.return_value = [[0.1, 0.2]]
    vector_store.index.search.return_value = (np.array([[0.5]]), np.array([[99]]))
    
    distances, indices = vector_store.search_index("query", 1)
    
    assert distances == [0.5]
    assert indices == [99]


@patch("os.path.exists", return_value=True)
@patch("app.services.embedding_service.faiss.read_index")
@patch("app.services.embedding_service.SentenceTransformer")
def test_load_existing_index(mock_sentence_transformer, mock_read_index, mock_exists):
    mock_read_index.return_value = MagicMock(ntotal=12)

    manager = VectorStoreManager()

    mock_read_index.assert_called_once()
    mock_sentence_transformer.assert_called_once_with("all-MiniLM-L6-v2")
    assert manager.index.ntotal == 12