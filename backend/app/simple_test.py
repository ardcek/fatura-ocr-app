#!/usr/bin/env python3
"""
Basit FastAPI test için minimal server
"""

import sys
import os

# Path'i ekle
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
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