from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Test için basitleştirilmiş versiyonu

app = FastAPI(
    title="Smart Invoice OCR API - Test Version",
    description="Test için basitleştirilmiş API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLite test database
DATABASE_URL = "sqlite:///./test_invoice.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {
        "message": "Smart Invoice OCR API - Test Version", 
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/upload",
            "/test-ocr"
        ]
    }

@app.get("/health")
async def health_check():
    """
    Sistem durumu kontrolü
    """
    try:
        # Kütüphane kontrolleri
        import pytesseract
        import spacy
        import cv2
        from PIL import Image
        
        # spaCy model kontrol
        try:
            nlp = spacy.load("en_core_web_sm")
            spacy_status = "en_core_web_sm loaded"
        except:
            spacy_status = "model not loaded"
        
        return {
            "status": "healthy",
            "components": {
                "pytesseract": "installed",
                "opencv": "installed", 
                "pillow": "installed",
                "spacy": spacy_status,
                "database": "sqlite_ready"
            }
        }
    except ImportError as e:
        return {
            "status": "error",
            "error": f"Missing dependency: {e}"
        }

@app.post("/test-ocr")
async def test_ocr_simple(file: UploadFile = File(...)):
    """
    Basit OCR testi
    """
    try:
        # Dosya formatı kontrolü
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Desteklenmeyen dosya formatı: {file.content_type}"
            )
        
        # Dosyayı oku
        contents = await file.read()
        
        # PIL Image oluştur
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(contents))
        
        # Basit OCR
        import pytesseract
        
        # Tesseract konfigürasyonu
        config = r'--oem 3 --psm 6 -l eng'  # İngilizce test için
        
        # OCR işlemi
        text = pytesseract.image_to_string(image, config=config)
        
        return {
            "status": "success",
            "filename": file.filename,
            "content_type": file.content_type,
            "image_size": f"{image.width}x{image.height}",
            "extracted_text": text[:500] if text else "No text extracted",
            "text_length": len(text) if text else 0
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "detail": "OCR processing failed"
        }

@app.post("/upload")
async def upload_test(file: UploadFile = File(...)):
    """
    Dosya upload testi
    """
    try:
        contents = await file.read()
        file_size = len(contents)
        
        return {
            "status": "success",
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": file_size,
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }