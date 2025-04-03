import logging
import numpy as np
import faiss
from typing import List, Dict, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from contextlib import contextmanager

from app.config import settings
from app.database.mongodb import get_mongo_collection
from app.exceptions import VectorStoreError

logger = logging.getLogger(__name__)

class VectorStoreService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the vector store service (singleton pattern)"""
        logger.info("Initializing VectorStoreService")
        
        # Initialize embeddings model
        self.embedding_model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device='cpu'
        )
        self.embedding_size = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(self.embedding_size)
        self.index_id_map = faiss.IndexIDMap(self.index)
        
        # MongoDB collection for metadata
        self.collection_name = settings.MONGO_VECTOR_COLLECTION

    async def create_and_store_embeddings(
        self,
        document_id: str,
        text: str,
        metadata: Dict
    ) -> int:
        """Process text and store embeddings with metadata"""
        try:
            # Chunk the text
            chunks = self._chunk_text(text)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(
                chunks,
                show_progress_bar=False,
                convert_to_numpy=True
            ).astype('float32')
            
            # Prepare documents for MongoDB
            operations = []
            chunk_ids = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"{document_id}_{i}"
                chunk_ids.append(chunk_id)
                
                operations.append({
                    'chunk_id': chunk_id,
                    'document_id': document_id,
                    'chunk_text': chunk,
                    'embedding': embedding.tolist(),
                    'metadata': metadata,
                    'chunk_index': i
                })
            
            # Store in MongoDB and FAISS
            with get_mongo_collection(self.collection_name) as collection:
                # Add to FAISS index
                ids = np.array([i for i in range(len(chunk_ids))])
                self.index_id_map.add_with_ids(embeddings, ids)
                
                # Insert into MongoDB
                result = collection.insert_many(operations)
                logger.info(f"Stored {len(result.inserted_ids)} chunks for document {document_id}")
                
                return len(result.inserted_ids)
                
        except Exception as e:
            logger.error(f"Error storing embeddings: {str(e)}")
            raise VectorStoreError(f"Failed to store embeddings: {str(e)}")

    async def search_similar_chunks(
        self,
        document_id: str,
        query: str,
        k: int = 5
    ) -> List[Dict]:
        """Search for similar text chunks"""
        try:
            # Embed the query
            query_embedding = self.embedding_model.encode(
                query,
                show_progress_bar=False
            ).astype('float32').reshape(1, -1)
            
            # Search in FAISS
            distances, indices = self.index_id_map.search(query_embedding, k)
            
            # Get chunks from MongoDB
            with get_mongo_collection(self.collection_name) as collection:
                chunks = list(collection.find({
                    "document_id": document_id,
                    "chunk_index": {"$in": [int(i) for i in indices[0]]}
                }).sort("chunk_index", 1))
                
                # Add similarity scores
                for chunk, distance in zip(chunks, distances[0]):
                    chunk['similarity_score'] = 1 / (1 + distance)
                
                return chunks
                
        except Exception as e:
            logger.error(f"Error searching chunks: {str(e)}")
            raise VectorStoreError(f"Search failed: {str(e)}")

    def _chunk_text(self, text: str) -> List[str]:
        """Improved text chunking with overlap and paragraph awareness"""
        # Implement your preferred chunking strategy here
        # Example: Split by paragraphs first, then by sentences if needed
        paragraphs = [p for p in text.split('\n') if p.strip()]
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= settings.CHUNK_SIZE:
                current_chunk += para + "\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    async def delete_document_embeddings(self, document_id: str) -> bool:
        """Delete all embeddings for a document"""
        try:
            with get_mongo_collection(self.collection_name) as collection:
                # Find all chunks for this document
                chunks = collection.find({"document_id": document_id})
                chunk_indices = [chunk['chunk_index'] for chunk in chunks]
                
                # Remove from FAISS
                if chunk_indices:
                    ids_to_remove = np.array(chunk_indices)
                    self.index_id_map.remove_ids(ids_to_remove)
                
                # Delete from MongoDB
                result = collection.delete_many({"document_id": document_id})
                return result.deleted_count > 0
                
        except Exception as e:
            logger.error(f"Error deleting embeddings: {str(e)}")
            raise VectorStoreError(f"Failed to delete embeddings: {str(e)}")