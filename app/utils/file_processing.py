import os
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status
import PyPDF2
import docx
import pandas as pd

def save_upload_file(upload_dir: str, file: UploadFile) -> str:
    try:
        # Create directory if it doesn't exist
        Path(upload_dir).mkdir(parents=True, exist_ok=True)
        
        # Construct file path
        file_path = os.path.join(upload_dir, file.filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
        
        return file_path
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )

def extract_text_from_file(file_path: str) -> str:
    try:
        if file_path.endswith('.pdf'):
            return _extract_text_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            return _extract_text_from_docx(file_path)
        elif file_path.endswith('.csv'):
            return _extract_text_from_csv(file_path)
        else:
            raise ValueError("Unsupported file format")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error extracting text: {str(e)}"
        )

def _extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def _extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def _extract_text_from_csv(file_path: str) -> str:
    df = pd.read_csv(file_path)
    return df.to_string(index=False)
