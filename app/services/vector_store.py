import faiss
import numpy as np
from pymongo import MongoClient
from pymongo.collection import Collection
from typing import List, Dict, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config import settings

class VectorStoreService:
    def __init__(self):
        # Initialize embeddings model
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Connect to MongoDB
        self.client = MongoClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB_NAME]
        self.collection: Collection = self.db[settings.MONGO_VECTOR_COLLECTION]
        
        # Initialize FAISS index
        self.embedding_size = 768  # Size of embeddings from the model
        self.index = faiss.IndexFlatL2(self.embedding_size)

    def create_and_store_embeddings(self, document_id: str, text: str, metadata: Dict):
        # Split text into chunks (simplified - consider better chunking strategies)
        chunks = self._chunk_text(text)
        
        # Generate embeddings for each chunk
        embeddings = self.embedding_model.embed_documents(chunks)
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Add vectors to FAISS index
        if not self.index.is_trained:
            self.index.add(embeddings_array)
        
        # Store chunks and embeddings in MongoDB
        documents_to_insert = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            documents_to_insert.append({
                "document_id": document_id,
                "chunk_id": f"{document_id}_{i}",
                "chunk_text": chunk,
                "embedding": embedding.tolist(),
                "metadata": metadata,
                "chunk_index": i
            })
        
        self.collection.insert_many(documents_to_insert)
        
        return len(chunks)

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Simple text chunking implementation"""
        chunks = []
        start = 0
        end = chunk_size
        
        while start < len(text):
            chunks.append(text[start:end])
            start = end - overlap
            end = start + chunk_size
        
        return chunks

    def search_similar_chunks(self, document_id: str, query: str, k: int = 10) -> List[Dict]:
        # Embed the query
        query_embedding = self.embedding_model.embed_query(query)
        query_vector = np.array([query_embedding]).astype('float32')
        
        # Search in FAISS index
        distances, indices = self.index.search(query_vector, k)
        
        # Get the actual chunks from MongoDB
        chunk_ids = [f"{document_id}_{idx}" for idx in indices[0]]
        chunks = list(self.collection.find({"chunk_id": {"$in": chunk_ids}}))
        
        # Sort chunks by their original order in the document
        chunks.sort(key=lambda x: x["chunk_index"])
        
        return chunks

    def close(self):
        self.client.close()
