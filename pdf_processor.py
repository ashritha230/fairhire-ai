import fitz  # PyMuPDF
from docx import Document
from werkzeug.datastructures import FileStorage


def extract_text_from_file(uploaded_file: FileStorage) -> str:
    """Extract text from PDF or DOCX files"""
    
    if not uploaded_file or not uploaded_file.filename:
        return ""

    filename = uploaded_file.filename.lower()

    if filename.endswith(".pdf"):
        return _extract_pdf_text(uploaded_file)

    elif filename.endswith(".docx"):
        return _extract_docx_text(uploaded_file)

    return ""


def _extract_pdf_text(file: FileStorage) -> str:
    """Extract text from PDF"""
    try:
        file.seek(0)  # Reset pointer
        pdf_data = file.read()

        doc = fitz.open(stream=pdf_data, filetype="pdf")
        text = ""

        for page in doc:
            text += page.get_text()

        doc.close()
        return text.strip()

    except Exception as e:
        print("PDF extraction error:", e)
        return ""


def _extract_docx_text(file: FileStorage) -> str:
    """Extract text from DOCX"""
    try:
        file.seek(0)  # Reset pointer
        doc = Document(file)

        text = "\n".join([para.text for para in doc.paragraphs])

        return text.strip()

    except Exception as e:
        print("DOCX extraction error:", e)
        return ""
