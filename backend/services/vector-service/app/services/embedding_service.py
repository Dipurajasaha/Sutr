import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings

##########################################################################
# Vector Store Manager
##########################################################################
class VectorStoreManager:
    def __init__(self):
        print("Loading local embedding model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384

        os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH), exist_ok=True)

        if os.path.exists(settings.FAISS_INDEX_PATH):
            self.index = faiss.read_index(settings.FAISS_INDEX_PATH)
            print(f"Loaded existing FAISS index with {self.index.ntotal} vectors.")
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            print("Created new FAISS index.")


    ##########################################################################
    # Generate Embeddings
    ##########################################################################
    def generate_embeddings(self, texts: list[str]) -> np.ndarray:
        # -- encode texts to vector embeddings --
        embeddings = self.model.encode(texts)
        return np.array(embeddings, dtype=np.float32)
    

    ##########################################################################
    # Add Vectors to Index
    ##########################################################################
    def add_to_index(self, embeddings: np.ndarray) -> list[int]:
        # -- add embeddings to FAISS and persist index --
        start_id = self.index.ntotal
        self.index.add(embeddings)

        faiss.write_index(self.index, settings.FAISS_INDEX_PATH)

        return [start_id + i for i in range(len(embeddings))]
    

    ##########################################################################
    # Search Index
    ##########################################################################
    def search_index(self, query: str, top_k: int = 5) -> tuple[list[float], list[int]]:
        # -- embed query and search FAISS for nearest neighbors --
        query_vector = self.generate_embeddings([query])
        distances, indices = self.index.search(query_vector, top_k)
        return distances[0].tolist(), indices[0].tolist()

# -- singleton vector store instance used across endpoints --
vector_store = VectorStoreManager()    