import importlib
import sys
from unittest.mock import patch, Mock


def reload_embedding_with_patches(exists_return=False):
    # Ensure fresh import and restore original module to avoid side-effects
    original_module = sys.modules.get('app.services.embedding_service')
    if 'app.services.embedding_service' in sys.modules:
        del sys.modules['app.services.embedding_service']

    # Inject a fake faiss module so import-time references resolve safely
    import types
    fake_faiss = types.ModuleType('faiss')
    fake_faiss.IndexFlatL2 = lambda dim: Mock(ntotal=0)
    sys.modules['faiss'] = fake_faiss

    try:
        with patch('os.path.exists', return_value=exists_return):
            with patch('app.services.embedding_service.SentenceTransformer') as mock_st:
                mock_st.return_value = Mock(encode=Mock(return_value=[[0.1]*384]))
                module = importlib.import_module('app.services.embedding_service')
                return module
    finally:
        # Clean up injected fake faiss module and restore original module
        if 'faiss' in sys.modules:
            del sys.modules['faiss']
        if original_module is not None:
            sys.modules['app.services.embedding_service'] = original_module
        else:
            if 'app.services.embedding_service' in sys.modules:
                del sys.modules['app.services.embedding_service']


def test_embedding_manager_creates_new_index_when_missing():
    mod = reload_embedding_with_patches(exists_return=False)
    # When index file missing, manager.index should be the mocked IndexFlatL2
    assert hasattr(mod, 'vector_store')
    assert mod.vector_store.index is not None


def test_embedding_manager_loads_existing_index_when_present():
    # When file exists, faiss.read_index will be called; patch it to return object
    if 'app.services.embedding_service' in sys.modules:
        del sys.modules['app.services.embedding_service']

    import types
    fake_faiss = types.ModuleType('faiss')
    fake_faiss.read_index = lambda path: Mock(ntotal=5)
    sys.modules['faiss'] = fake_faiss
    try:
        with patch('os.path.exists', return_value=True):
            with patch('app.services.embedding_service.SentenceTransformer') as mock_st:
                mock_st.return_value = Mock(encode=Mock(return_value=[[0.1]*384]))
                mod = importlib.import_module('app.services.embedding_service')
                assert mod.vector_store.index.ntotal == 5
    finally:
        del sys.modules['faiss']
