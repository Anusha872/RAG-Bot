import io
import pypdf
from fastapi import HTTPException, UploadFile


class TextExtractorService:
    """Service to parse and extract plain text from uploaded files (.pdf, .txt)."""

    @staticmethod
    async def extract_text(file: UploadFile) -> str:
        filename = file.filename or ""
        content_bytes = await file.read()

        if filename.endswith(".pdf") or file.content_type == "application/pdf":
            return TextExtractorService._extract_from_pdf(content_bytes)
        elif filename.endswith(".txt") or file.content_type == "text/plain":
            return TextExtractorService._extract_from_txt(content_bytes)
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Only .pdf and .txt files are allowed."
            )

    @staticmethod
    def _extract_from_pdf(content_bytes: bytes) -> str:
        try:
            pdf_file = io.BytesIO(content_bytes)
            reader = pypdf.PdfReader(pdf_file)
            text_parts = []
            for page_num, page in enumerate(reader.pages):
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
            
            full_text = "\n".join(text_parts).strip()
            if not full_text:
                raise HTTPException(status_code=400, detail="Unable to extract text from PDF (file may be image-only/scanned).")
            return full_text
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF document: {str(e)}")

    @staticmethod
    def _extract_from_txt(content_bytes: bytes) -> str:
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content_bytes.decode("latin-1")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to decode text file: {str(e)}")
        
        text = text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Uploaded text file is empty.")
        return text
