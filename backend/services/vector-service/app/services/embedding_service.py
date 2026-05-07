import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings

###############################################################################
# -- manages the FAISS vector store and embedding generation --
###############################################################################
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


    ##############################################################################
    # -- converts text to vector embeddings --
    ##############################################################################
    def generate_embeddings(self, texts: list[str]) -> np.ndarray:
        embeddings = self.model.encode(texts)
        return np.array(embeddings, dtype=np.float32)
    

    ##############################################################################
    # -- adds vectors to FAISS and returns their assigned integer IDs --
    ##############################################################################
    def add_to_index(self, embeddings: np.ndarray) -> list[int]:
        start_id = self.index.ntotal
        self.index.add(embeddings)

        faiss.write_index(self.index, settings.FAISS_INDEX_PATH)

        return [start_id + i for i in range(len(embeddings))]
    

    ##############################################################################
    # -- searches for the closest vectors to the query --
    ##############################################################################
    def search_index(self, query: str, top_k: int = 5) -> tuple[list[float], list[int]]:
        query_vector = self.generate_embeddings([query])
        distances, indices = self.index.search(query_vector, top_k)
        return distances[0].tolist(), indices[0].tolist()

# -- singleton instance to be used across endpoints --
vector_store = VectorStoreManager()    