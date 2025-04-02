from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
from app.schemas.auth import UserCreate, UserLogin, Token
from app.schemas.document import DocumentCreate, Document, DocumentShare, DocumentQuery
from app.services.auth import get_current_user, create_user, authenticate_user, create_access_token
from app.services.document import DocumentService
from app.models.user import User
from app.config import settings
from app.services.vector_store import VectorStoreService
from app.services.ollama import OllamaService

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Document AI service is running"}

# Auth endpoints
@app.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    user = create_user(user_data)
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Document endpoints
@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user)
):
    doc_data = DocumentCreate(name=name, tags=tags)
    document = DocumentService.create_document(current_user, file, doc_data)
    return document

@app.get("/documents", response_model=List[Document])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    documents = DocumentService.get_user_documents(current_user.id, skip, limit)
    return documents

@app.get("/documents/{doc_id}", response_model=Document)
async def get_document(
    doc_id: int,
    current_user: User = Depends(get_current_user)
):
    return DocumentService.get_document_by_id(doc_id, current_user.id)

@app.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user)
):
    return DocumentService.delete_document(doc_id, current_user.id)

@app.post("/documents/{doc_id}/process")
async def process_document(
    doc_id: int,
    current_user: User = Depends(get_current_user)
):
    return DocumentService.process_document(doc_id, current_user.id)

@app.post("/documents/{doc_id}/share")
async def share_document(
    doc_id: int,
    share_data: DocumentShare,
    current_user: User = Depends(get_current_user)
):
    return DocumentService.share_document(doc_id, current_user.id, share_data)

@app.get("/shared", response_model=List[Document])
async def list_shared_documents(current_user: User = Depends(get_current_user)):
    return DocumentService.get_shared_documents(current_user.id)

@app.delete("/documents/{doc_id}/share/{user_id}")
async def remove_share(
    doc_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    return DocumentService.remove_share(doc_id, current_user.id, user_id)

@app.post("/documents/{doc_id}/query")
async def query_document(
    doc_id: int,
    query: DocumentQuery,
    current_user: User = Depends(get_current_user)
):
    # First verify user has access to the document
    document = DocumentService.get_document_by_id(doc_id, current_user.id)
    
    if not document.processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document not processed yet"
        )
    
    # Search for relevant chunks
    vector_service = VectorStoreService()
    chunks = vector_service.search_similar_chunks(str(doc_id), query.question)
    chunk_texts = [chunk["chunk_text"] for chunk in chunks]
    
    # Generate response using Ollama
    ollama_service = OllamaService()
    response = ollama_service.generate_response(
        prompt=query.question,
        model=query.model,
        context=chunk_texts
    )
    
    return {
        "response": response,
        "relevant_chunks": chunk_texts
    }
