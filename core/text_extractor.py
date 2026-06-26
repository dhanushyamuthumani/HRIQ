import pdfplumber
import docx
import os
import logging
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
    return text

def extract_text_from_docx(docx_path: str) -> str:
    """Extracts text from a DOCX file using python-docx."""
    text = ""
    try:
        doc = docx.Document(docx_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        logger.error(f"Error extracting text from DOCX {docx_path}: {e}")
    return text

def extract_text(file_path: str) -> Optional[str]:
    """Generic text extractor based on file extension."""
    if not os.path.exists(file_path):
        return None
    
    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".pdf":
        return extract_text_from_pdf(file_path)
    elif extension == ".docx":
        return extract_text_from_docx(file_path)
    else:
        logger.warning(f"Unsupported file format: {extension}")
        return None

if __name__ == "__main__":
    # Quick manual test if run directly
    sample_pdf = "sample.pdf"
    if os.path.exists(sample_pdf):
        print("Extracting from PDF...")
        print(extract_text(sample_pdf)[:500])
