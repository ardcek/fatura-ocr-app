#!/usr/bin/env python3
"""
Basit FastAPI test için minimal server
"""

import sys
import os

# Path'i ekle
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Invoice OCR API - Simple Test",
    description="Basit API testi",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Ana endpoint"""
    return {
        "message": "Invoice OCR API Test",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "test": "/test"
        }
    }

@app.get("/health")
async def health_check():
    """Sağlık durumu kontrolü"""
    try:
        # Temel kütüphane kontrolleri
        dependencies = {}
        
        try:
            import fastapi
            dependencies["fastapi"] = f"✅ {fastapi.__version__}"
        except ImportError:
            dependencies["fastapi"] = "❌ Not installed"
            
        try:
            import uvicorn
            dependencies["uvicorn"] = "✅ Installed"
        except ImportError:
            dependencies["uvicorn"] = "❌ Not installed"
            
        try:
            import pytesseract
            dependencies["pytesseract"] = "✅ Installed"
        except ImportError:
            dependencies["pytesseract"] = "❌ Not installed"
            
        try:
            from PIL import Image
            dependencies["pillow"] = "✅ Installed"
        except ImportError:
            dependencies["pillow"] = "❌ Not installed"
            
        try:
            import cv2
            dependencies["opencv"] = "✅ Installed"
        except ImportError:
            dependencies["opencv"] = "❌ Not installed"
            
        try:
            import spacy
            dependencies["spacy"] = "✅ Installed"
        except ImportError:
            dependencies["spacy"] = "❌ Not installed"
            
        return {
            "status": "healthy",
            "dependencies": dependencies,
            "system": {
                "python_version": sys.version,
                "platform": sys.platform
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {
        "message": "Test endpoint is working!",
        "status": "success",
        "data": {
            "test_number": 42,
            "test_string": "Hello World",
            "test_boolean": True,
            "test_list": [1, 2, 3, 4, 5]
        }
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Dosya yükleme endpoint'i - Sadece Mock Data"""
    try:
        # Dosya türü kontrolü
        if not file.content_type.startswith('image/'):
            return {
                "status": "error",
                "message": "Sadece resim dosyaları kabul edilir"
            }
        
        # Dosya boyutu kontrolü (10MB limit)
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            return {
                "status": "error", 
                "message": "Dosya boyutu 10MB'dan büyük olamaz"
            }
        
        print(f"File uploaded: {file.filename}, size: {len(contents)} bytes")
        
        # MOCK OCR RESPONSE (Tesseract gerekmiyor)
        import random
        from datetime import datetime
        
        mock_fields = {
            "company_name": "AKILLI TEKNOLOJİ A.Ş.",
            "invoice_number": f"FTR-2024-{random.randint(1000, 9999)}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tax_number": f"{random.randint(1000000000, 9999999999)}",
            "total_amount": round(random.uniform(1000, 15000), 2),
            "vat_amount": round(random.uniform(180, 2700), 2),
            "line_items": [
                {
                    "description": "Web Tasarım Hizmeti",
                    "quantity": 1,
                    "unit_price": round(random.uniform(800, 3000), 2),
                    "total": round(random.uniform(800, 3000), 2)
                },
                {
                    "description": "SEO Optimizasyon",
                    "quantity": 1,
                    "unit_price": round(random.uniform(500, 1500), 2), 
                    "total": round(random.uniform(500, 1500), 2)
                }
            ]
        }
        
        print(f"Generated mock fields: {mock_fields}")
        
        response_data = {
            "status": "success",
            "message": "Dosya başarıyla işlendi (OCR simülasyon)",
            "filename": file.filename,
            "size": len(contents),
            "content_type": file.content_type,
            "ocr_result": {
                "raw_text": f"""=== FATURA OCR SİMÜLASYONU ===

Dosya: {file.filename}
Boyut: {len(contents):,} bytes
Format: {file.content_type}

FATURA BİLGİLERİ:
================
Firma Adı: {mock_fields['company_name']}
Fatura No: {mock_fields['invoice_number']}
Tarih: {mock_fields['date']}
Vergi No: {mock_fields['tax_number']}

TUTAR BİLGİLERİ:
===============
Toplam: {mock_fields['total_amount']} TL
KDV: {mock_fields['vat_amount']} TL

KALEMLER:
=========""",
                "confidence": round(random.uniform(0.75, 0.95), 3),
                "extracted_fields": mock_fields,
                "note": "🚀 Bu gelişmiş OCR simülasyonu! Gerçek OCR için Tesseract kurulum gerekli."
            }
        }
        
        print(f"Sending response: {response_data}")
        return response_data
        
    except Exception as e:
        print(f"Upload error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"İşleme hatası: {str(e)}"
        }

@app.get("/test-ocr")
async def test_ocr_response():
    """Test OCR response formatını kontrol et"""
    import random
    from datetime import datetime
    
    mock_fields = {
        "company_name": "TEST FIRMA LTD.ŞTİ.",
        "invoice_number": f"TEST-{random.randint(1000, 9999)}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "tax_number": f"{random.randint(1000000000, 9999999999)}",
        "total_amount": round(random.uniform(100, 5000), 2),
        "vat_amount": round(random.uniform(50, 900), 2),
        "line_items": [
            {
                "description": "Test Hizmet",
                "quantity": 1,
                "unit_price": 1000.0,
                "total": 1000.0
            }
        ]
    }
    
    return {
        "status": "success",
        "message": "Test OCR response",
        "filename": "test-file.jpg",
        "size": 12345,
        "content_type": "image/jpeg",
        "ocr_result": {
            "raw_text": "Test OCR metni burada olacak",
            "confidence": 0.85,
            "extracted_fields": mock_fields,
            "note": "Bu bir test response'u"
        }
    }

@app.get("/api-info")
async def api_info():
    """API bilgileri"""
    return {
        "api_name": "Invoice OCR System",
        "version": "1.0.0",
        "description": "Akıllı Fatura OCR + ERP Entegrasyon Sistemi",
        "features": [
            "Fatura OCR işlemi",
            "Alan ayrıştırma (NLP)",
            "ERP entegrasyon",
            "Doğrulama sistemi",
            "RESTful API"
        ],
        "tech_stack": [
            "FastAPI",
            "Python 3.11+",
            "Tesseract OCR",
            "spaCy NLP",
            "OpenCV",
            "SQLAlchemy",
            "PostgreSQL"
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting Invoice OCR API Test Server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    print("---")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000,
        log_level="info"
    )