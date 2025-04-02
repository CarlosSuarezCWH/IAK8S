import os
from datetime import datetime
from typing import List, Optional

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.models.user import User
from app.database.mysql import SessionLocal
from app.utils.file_processing import save_upload_file, extract_text_from_file
from app.services.vector_store import VectorStoreService
from app.schemas.document import DocumentCreate, DocumentShare

class DocumentService:
    @staticmethod
    def create_document(user: User, file: UploadFile, doc_data: DocumentCreate):
        db = SessionLocal()
        
        # Save file to disk
        file_path = save_upload_file(settings.UPLOAD_FOLDER, file)
        
        # Create document record
        document = Document(
            user_id=user.id,
            name=doc_data.name or file.filename,
            file_path=file_path,
            file_type=file.content_type,
            file_size=os.path.getsize(file_path),
            tags=",".join(doc_data.tags) if doc_data.tags else None
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        db.close()
        
        return document

    @staticmethod
    def get_user_documents(user_id: int, skip: int = 0, limit: int = 100):
        db = SessionLocal()
        documents = db.query(Document).filter(Document.user_id == user_id).offset(skip).limit(limit).all()
        db.close()
        return documents

    @staticmethod
    def get_document_by_id(document_id: int, user_id: int):
        db = SessionLocal()
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id
        ).first()
        db.close()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        return document

    @staticmethod
    def delete_document(document_id: int, user_id: int):
        db = SessionLocal()
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id
        ).first()
        
        if not document:
            db.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete file from disk
        try:
            os.remove(document.file_path)
        except OSError:
            pass
        
        # Delete from database
        db.delete(document)
        db.commit()
        db.close()
        return {"message": "Document deleted successfully"}

    @staticmethod
    def process_document(document_id: int, user_id: int):
        db = SessionLocal()
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id
        ).first()
        
        if not document:
            db.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        if document.processed:
            db.close()
            return {"message": "Document already processed"}
        
        # Extract text from file
        text = extract_text_from_file(document.file_path)
        
        # Process text and create embeddings
        vector_service = VectorStoreService()
        vector_service.create_and_store_embeddings(
            document_id=str(document.id),
            text=text,
            metadata={
                "user_id": str(user_id),
                "document_name": document.name,
                "document_type": document.file_type
            }
        )
        
        # Update document status
        document.processed = True
        db.commit()
        db.refresh(document)
        db.close()
        
        return {"message": "Document processed successfully"}

    @staticmethod
    def share_document(document_id: int, owner_id: int, share_data: DocumentShare):
        db = SessionLocal()
        
        # Get document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == owner_id
        ).first()
        
        if not document:
            db.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get user to share with
        shared_with = db.query(User).filter(User.email == share_data.email).first()
        if not shared_with:
            db.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this email not found"
            )
        
        # Check if already shared
        existing_share = db.query(SharedDocument).filter(
            SharedDocument.document_id == document_id,
            SharedDocument.shared_with_id == shared_with.id
        ).first()
        
        if existing_share:
            db.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document already shared with this user"
            )
        
        # Create share record
        shared_doc = SharedDocument(
            document_id=document_id,
            owner_id=owner_id,
            shared_with_id=shared_with.id,
            permission_level=share_data.permission_level
        )
        
        db.add(shared_doc)
        db.commit()
        db.refresh(shared_doc)
        db.close()
        
        return {"message": "Document shared successfully"}

    @staticmethod
    def get_shared_documents(user_id: int):
        db = SessionLocal()
        
        # Documents shared with me
        shared_docs = db.query(Document).join(
            SharedDocument,
            SharedDocument.document_id == Document.id
        ).filter(
            SharedDocument.shared_with_id == user_id
        ).all()
        
        db.close()
        return shared_docs

    @staticmethod
    def remove_share(document_id: int, owner_id: int, user_id: int):
        db = SessionLocal()
        
        shared_doc = db.query(SharedDocument).filter(
            SharedDocument.document_id == document_id,
            SharedDocument.owner_id == owner_id,
            SharedDocument.shared_with_id == user_id
        ).first()
        
        if not shared_doc:
            db.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share record not found"
            )
        
        db.delete(shared_doc)
        db.commit()
        db.close()
        
        return {"message": "Share removed successfully"}
