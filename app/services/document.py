import os
import logging
from datetime import datetime
from typing import Optional, List, AsyncGenerator
from pathlib import Path

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.config import settings
from app.database import get_db_session
from app.models.document import Document, SharedDocument
from app.schemas.document import DocumentCreate, DocumentShare
from app.utils.file_processing import save_upload_file, extract_text_from_file
from app.services.vector_store import VectorStoreService
from app.services.ollama import OllamaService

logger = logging.getLogger(__name__)

class DocumentService:
    @staticmethod
    async def create_document(
        db: AsyncSession,
        user_id: int,
        file: UploadFile,
        doc_data: DocumentCreate
    ) -> Document:
        # Validate file size
        if file.size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit"
            )

        # Save file to disk
        file_path = await save_upload_file(settings.UPLOAD_FOLDER, file)
        
        # Create document record
        document = Document(
            user_id=user_id,
            name=doc_data.name or file.filename,
            file_path=file_path,
            file_type=file.content_type,
            file_size=file.size,
            tags=",".join(doc_data.tags) if doc_data.tags else None
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document

    @staticmethod
    async def get_user_documents(
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        result = await db.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def process_document(
        db: AsyncSession,
        document_id: int,
        user_id: int
    ) -> Document:
        # Get document with lock
        result = await db.execute(
            select(Document)
            .where(
                Document.id == document_id,
                Document.user_id == user_id
            )
            .with_for_update()
        )
        document = result.scalars().first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        if document.processed:
            return document
        
        try:
            # Extract text from file
            text = await extract_text_from_file(document.file_path)
            
            # Process text and create embeddings
            vector_service = VectorStoreService()
            await vector_service.create_and_store_embeddings(
                document_id=str(document.id),
                text=text,
                metadata={
                    "user_id": str(user_id),
                    "document_name": document.name,
                    "document_type": document.file_type
                }
            )
            
            # Update document status
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(processed=True, updated_at=datetime.utcnow())
            )
            await db.commit()
            
            # Refresh document
            await db.refresh(document)
            return document
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing document {document_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing document"
            )

    @staticmethod
    async def share_document(
        db: AsyncSession,
        document_id: int,
        owner_id: int,
        share_data: DocumentShare
    ) -> SharedDocument:
        # Check if document exists and belongs to owner
        doc_result = await db.execute(
            select(Document)
            .where(
                Document.id == document_id,
                Document.user_id == owner_id
            )
        )
        if not doc_result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get user to share with
        user_result = await db.execute(
            select(User)
            .where(User.email == share_data.email)
        )
        shared_with = user_result.scalars().first()
        
        if not shared_with:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create share record
        shared_doc = SharedDocument(
            document_id=document_id,
            owner_id=owner_id,
            shared_with_id=shared_with.id,
            permission_level=share_data.permission_level
        )
        
        db.add(shared_doc)
        await db.commit()
        await db.refresh(shared_doc)
        return shared_doc