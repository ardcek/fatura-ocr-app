from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from PIL import Image
import pytesseract
import io
import os
import uuid
from datetime import datetime
from typing import List, Optional
import logging

from models import (
    Base, Invoice, InvoiceStatus, InvoiceResponse, 
    InvoiceCreate, OCRResult, ValidationRequest, 
    ERPRequest, ERPResponse
)
from ocr import ocr_engine
from field_extractor import field_extractor

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/invoice_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI app
app = FastAPI(
    title="Smart Invoice OCR API",
    description="Akıllı Fatura OCR + ERP Entegrasyon Sistemi",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)

# Upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {
        "message": "Smart Invoice OCR API", 
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload",
            "process": "/process/{invoice_id}",
            "validate": "/validate/{invoice_id}",
            "results": "/results/{invoice_id}",
            "erp": "/erp/send/{invoice_id}"
        }
    }

@app.post("/upload", response_model=InvoiceResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Fatura dosyasını yükle ve veritabanına kaydet
    """
    try:
        # Dosya formatını kontrol et
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Desteklenmeyen dosya formatı: {file.content_type}"
            )
        
        # Dosyayı kaydet
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1].lower()
        file_path = f"{UPLOAD_DIR}/{file_id}.{file_extension}"
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Veritabanı kaydı oluştur
        db_invoice = Invoice(
            filename=file.filename,
            file_path=file_path,
            file_type=file_extension,
            status=InvoiceStatus.UPLOADED,
            created_at=datetime.utcnow()
        )
        
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)
        
        # Arka planda OCR işlemini başlat
        background_tasks.add_task(process_invoice_ocr, db_invoice.id, file_path, file_extension)
        
        return InvoiceResponse.from_orm(db_invoice)
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/process/{invoice_id}")
async def process_invoice(
    invoice_id: int,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Faturayı işle (OCR + Alan Ayrıştırma)
    """
    try:
        # Faturayı bul
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Arka planda işleme başlat
        background_tasks.add_task(process_invoice_ocr, invoice_id, invoice.file_path, invoice.file_type)
        
        return {"message": "Processing started", "invoice_id": invoice_id}
        
    except Exception as e:
        logger.error(f"Process error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/results/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice_results(invoice_id: int, db: Session = Depends(get_db)):
    """
    Fatura sonuçlarını getir
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return InvoiceResponse.from_orm(invoice)

@app.post("/validate/{invoice_id}")
async def validate_invoice_field(
    invoice_id: int,
    validation: ValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Kullanıcı tarafından alan doğrulaması/düzeltmesi
    """
    try:
        # Faturayı bul
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Alan güncelle
        if hasattr(invoice, validation.field_name):
            setattr(invoice, validation.field_name, validation.corrected_value)
            
            # Validation record oluştur
            from models import ValidationRecord
            validation_record = ValidationRecord(
                invoice_id=invoice_id,
                user_id=validation.user_id,
                field_name=validation.field_name,
                original_value=getattr(invoice, validation.field_name),
                corrected_value=validation.corrected_value
            )
            
            db.add(validation_record)
            
            # Invoice status güncelle
            invoice.status = InvoiceStatus.VALIDATED
            invoice.validated_at = datetime.utcnow()
            
            db.commit()
            
            return {"message": "Field validated", "field": validation.field_name, "value": validation.corrected_value}
        
        else:
            raise HTTPException(status_code=400, detail=f"Field {validation.field_name} not found")
            
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Faturaları listele
    """
    invoices = db.query(Invoice).offset(skip).limit(limit).all()
    return [InvoiceResponse.from_orm(inv) for inv in invoices]

@app.post("/erp/send/{invoice_id}")
async def send_to_erp(
    invoice_id: int,
    erp_request: ERPRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Faturayı ERP sistemine gönder (WOLVOX)
    """
    try:
        # Faturayı bul
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # ERP'ye gönderimi arka planda başlat
        background_tasks.add_task(send_to_wolvox_erp, invoice_id, erp_request.action)
        
        return {"message": "ERP send started", "invoice_id": invoice_id}
        
    except Exception as e:
        logger.error(f"ERP send error: {e}")
        raise HTTPException(status_code=500, detail=f"ERP send failed: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Sistem durumu kontrolü
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "connected",
            "ocr_engine": "ready",
            "field_extractor": "ready"
        }
    }

# Background tasks
async def process_invoice_ocr(invoice_id: int, file_path: str, file_type: str):
    """
    Arka planda OCR işlemi
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting OCR processing for invoice {invoice_id}")
        
        # Dosyayı oku
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # OCR işlemi
        ocr_result = ocr_engine.process_document(file_content, file_type)
        
        # Alan ayrıştırma
        extracted_fields = field_extractor.extract_all_fields(ocr_result.raw_text)
        
        # Faturayı güncelle
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if invoice:
            invoice.raw_text = ocr_result.raw_text
            invoice.confidence_score = ocr_result.confidence
            invoice.status = InvoiceStatus.OCR_PROCESSED
            invoice.processed_at = datetime.utcnow()
            
            # Ayrıştırılan alanları kaydet
            if 'invoice_number' in extracted_fields:
                invoice.invoice_number = extracted_fields['invoice_number'].value
            if 'date' in extracted_fields:
                invoice.invoice_date = extracted_fields['date'].value
            if 'company_name' in extracted_fields:
                invoice.company_name = extracted_fields['company_name'].value
            if 'tax_number' in extracted_fields:
                invoice.company_tax_number = extracted_fields['tax_number'].value
            if 'total_amount' in extracted_fields:
                invoice.total_amount = extracted_fields['total_amount'].value
            if 'vat_amount' in extracted_fields:
                invoice.vat_amount = extracted_fields['vat_amount'].value
            if 'net_amount' in extracted_fields:
                invoice.net_amount = extracted_fields['net_amount'].value
            
            # JSON formatında ekstra bilgileri kaydet
            invoice.extracted_fields = {
                field_name: {
                    'value': field.value,
                    'confidence': field.confidence,
                    'method': field.method
                }
                for field_name, field in extracted_fields.items()
            }
            
            db.commit()
        
        logger.info(f"OCR processing completed for invoice {invoice_id}")
        
    except Exception as e:
        logger.error(f"OCR processing error for invoice {invoice_id}: {e}")
        
        # Hata durumunu kaydet
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if invoice:
            invoice.status = InvoiceStatus.ERROR
            db.commit()
            
    finally:
        db.close()

async def send_to_wolvox_erp(invoice_id: int, action: str = "CREATE"):
    """
    WOLVOX ERP sistemine veri gönder
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting ERP send for invoice {invoice_id}")
        
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return
        
        # ERP request data hazırla
        erp_data = {
            "invoice_number": invoice.invoice_number,
            "date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            "company_name": invoice.company_name,
            "company_tax_number": invoice.company_tax_number,
            "total_amount": invoice.total_amount,
            "vat_amount": invoice.vat_amount,
            "net_amount": invoice.net_amount,
            "currency": invoice.currency or "TRY",
            "action": action
        }
        
        # DUMMY ERP API call (gerçek WOLVOX entegrasyonu için değiştirilecek)
        erp_response = await call_dummy_wolvox_api(erp_data)
        
        # Sonucu kaydet
        from models import ERPIntegrationLog
        log_entry = ERPIntegrationLog(
            invoice_id=invoice_id,
            action=action,
            request_data=erp_data,
            response_data=erp_response,
            success=erp_response.get('success', False)
        )
        
        db.add(log_entry)
        
        # Invoice durumunu güncelle
        if erp_response.get('success'):
            invoice.status = InvoiceStatus.SENT_TO_ERP
            invoice.erp_id = erp_response.get('erp_id')
            invoice.erp_response = erp_response
            invoice.sent_to_erp_at = datetime.utcnow()
        else:
            invoice.status = InvoiceStatus.ERROR
            
        db.commit()
        
        logger.info(f"ERP send completed for invoice {invoice_id}")
        
    except Exception as e:
        logger.error(f"ERP send error for invoice {invoice_id}: {e}")
        
    finally:
        db.close()

async def call_dummy_wolvox_api(data: dict) -> dict:
    """
    Dummy WOLVOX API call (test için)
    """
    import asyncio
    import random
    
    # Simulate API call delay
    await asyncio.sleep(1)
    
    # Dummy response
    success = random.choice([True, True, True, False])  # 75% başarı oranı
    
    if success:
        return {
            "success": True,
            "erp_id": f"WLX_{random.randint(10000, 99999)}",
            "message": "Invoice created successfully in WOLVOX",
            "data": data
        }
    else:
        return {
            "success": False,
            "error": "Connection timeout to WOLVOX API",
            "message": "Failed to create invoice in ERP system"
        }
