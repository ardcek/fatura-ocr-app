from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="WOLVOX Mock ERP API",
    description="Akınsoft WOLVOX ERP Sistemi için Mock API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
invoice_storage = {}

class WolvoxInvoiceRequest(BaseModel):
    invoice_number: Optional[str] = None
    date: Optional[str] = None
    company_name: Optional[str] = None
    company_tax_number: Optional[str] = None
    total_amount: Optional[float] = None
    vat_amount: Optional[float] = None
    net_amount: Optional[float] = None
    currency: str = "TRY"
    action: str = "CREATE"

class WolvoxResponse(BaseModel):
    success: bool
    erp_id: Optional[str] = None
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None

@app.get("/")
async def root():
    return {
        "message": "WOLVOX Mock ERP API",
        "version": "1.0.0",
        "endpoints": {
            "create_invoice": "/api/v1/invoices",
            "update_invoice": "/api/v1/invoices/{erp_id}",
            "get_invoice": "/api/v1/invoices/{erp_id}",
            "delete_invoice": "/api/v1/invoices/{erp_id}",
            "health": "/health"
        }
    }

@app.post("/api/v1/invoices", response_model=WolvoxResponse)
async def create_invoice(invoice: WolvoxInvoiceRequest):
    """
    WOLVOX ERP sisteminde fatura oluştur
    """
    try:
        # Simüle edilmiş başarı/başarısızlık oranı (80% başarı)
        success = random.random() < 0.8
        
        if not success:
            # Rastgele hata durumları
            errors = [
                {"code": "DUPLICATE_INVOICE", "message": "Bu fatura numarası zaten mevcut"},
                {"code": "INVALID_TAX_NUMBER", "message": "Vergi numarası geçersiz"},
                {"code": "CONNECTION_TIMEOUT", "message": "WOLVOX sunucusu yanıt vermiyor"},
                {"code": "INSUFFICIENT_PERMISSIONS", "message": "Bu işlem için yetki yok"},
            ]
            error = random.choice(errors)
            
            return WolvoxResponse(
                success=False,
                message=error["message"],
                error_code=error["code"]
            )
        
        # Başarı durumu
        erp_id = f"WLX_{uuid.uuid4().hex[:8].upper()}"
        
        # Invoice'ı mock storage'a kaydet
        invoice_data = {
            "erp_id": erp_id,
            "invoice_number": invoice.invoice_number,
            "date": invoice.date,
            "company_name": invoice.company_name,
            "company_tax_number": invoice.company_tax_number,
            "total_amount": invoice.total_amount,
            "vat_amount": invoice.vat_amount,
            "net_amount": invoice.net_amount,
            "currency": invoice.currency,
            "status": "ACTIVE",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        invoice_storage[erp_id] = invoice_data
        
        logger.info(f"Created invoice {erp_id} for company {invoice.company_name}")
        
        return WolvoxResponse(
            success=True,
            erp_id=erp_id,
            message="Fatura başarıyla WOLVOX sisteminde oluşturuldu",
            data=invoice_data
        )
        
    except Exception as e:
        logger.error(f"Invoice creation error: {e}")
        return WolvoxResponse(
            success=False,
            message="İç sistem hatası",
            error_code="INTERNAL_ERROR"
        )

@app.get("/api/v1/invoices/{erp_id}", response_model=WolvoxResponse)
async def get_invoice(erp_id: str):
    """
    WOLVOX ERP sisteminden fatura bilgilerini getir
    """
    try:
        if erp_id not in invoice_storage:
            return WolvoxResponse(
                success=False,
                message="Fatura bulunamadı",
                error_code="INVOICE_NOT_FOUND"
            )
        
        invoice_data = invoice_storage[erp_id]
        
        return WolvoxResponse(
            success=True,
            erp_id=erp_id,
            message="Fatura bilgileri başarıyla alındı",
            data=invoice_data
        )
        
    except Exception as e:
        logger.error(f"Invoice retrieval error: {e}")
        return WolvoxResponse(
            success=False,
            message="İç sistem hatası",
            error_code="INTERNAL_ERROR"
        )

@app.put("/api/v1/invoices/{erp_id}", response_model=WolvoxResponse)
async def update_invoice(erp_id: str, invoice: WolvoxInvoiceRequest):
    """
    WOLVOX ERP sisteminde faturayı güncelle
    """
    try:
        if erp_id not in invoice_storage:
            return WolvoxResponse(
                success=False,
                message="Fatura bulunamadı",
                error_code="INVOICE_NOT_FOUND"
            )
        
        # Simüle edilmiş başarı oranı
        success = random.random() < 0.9
        
        if not success:
            return WolvoxResponse(
                success=False,
                message="Fatura güncelleme sırasında hata oluştu",
                error_code="UPDATE_FAILED"
            )
        
        # Güncellenmiş verileri kaydet
        existing_invoice = invoice_storage[erp_id]
        existing_invoice.update({
            "invoice_number": invoice.invoice_number or existing_invoice["invoice_number"],
            "company_name": invoice.company_name or existing_invoice["company_name"],
            "company_tax_number": invoice.company_tax_number or existing_invoice["company_tax_number"],
            "total_amount": invoice.total_amount or existing_invoice["total_amount"],
            "vat_amount": invoice.vat_amount or existing_invoice["vat_amount"],
            "net_amount": invoice.net_amount or existing_invoice["net_amount"],
            "updated_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Updated invoice {erp_id}")
        
        return WolvoxResponse(
            success=True,
            erp_id=erp_id,
            message="Fatura başarıyla güncellendi",
            data=existing_invoice
        )
        
    except Exception as e:
        logger.error(f"Invoice update error: {e}")
        return WolvoxResponse(
            success=False,
            message="İç sistem hatası",
            error_code="INTERNAL_ERROR"
        )

@app.delete("/api/v1/invoices/{erp_id}", response_model=WolvoxResponse)
async def delete_invoice(erp_id: str):
    """
    WOLVOX ERP sisteminden faturayı sil
    """
    try:
        if erp_id not in invoice_storage:
            return WolvoxResponse(
                success=False,
                message="Fatura bulunamadı",
                error_code="INVOICE_NOT_FOUND"
            )
        
        # Silme işlemi
        del invoice_storage[erp_id]
        
        logger.info(f"Deleted invoice {erp_id}")
        
        return WolvoxResponse(
            success=True,
            erp_id=erp_id,
            message="Fatura başarıyla silindi"
        )
        
    except Exception as e:
        logger.error(f"Invoice deletion error: {e}")
        return WolvoxResponse(
            success=False,
            message="İç sistem hatası",
            error_code="INTERNAL_ERROR"
        )

@app.get("/api/v1/invoices", response_model=Dict[str, Any])
async def list_invoices():
    """
    WOLVOX ERP sistemindeki tüm faturaları listele
    """
    try:
        return {
            "success": True,
            "message": "Faturalar başarıyla listelendi",
            "data": {
                "invoices": list(invoice_storage.values()),
                "total_count": len(invoice_storage)
            }
        }
        
    except Exception as e:
        logger.error(f"Invoice listing error: {e}")
        return {
            "success": False,
            "message": "İç sistem hatası",
            "error_code": "INTERNAL_ERROR"
        }

@app.get("/health")
async def health_check():
    """
    WOLVOX Mock API sistem durumu
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "WOLVOX Mock ERP API",
        "version": "1.0.0",
        "statistics": {
            "total_invoices": len(invoice_storage),
            "uptime": "Mock service - always available"
        }
    }

@app.get("/api/v1/system/status")
async def system_status():
    """
    WOLVOX sistem durumu (gerçek API'de mevcut olabilecek endpoint)
    """
    # Simüle edilmiş sistem durumu
    system_health = random.choice(["healthy", "healthy", "healthy", "degraded"])
    
    return {
        "system_status": system_health,
        "database_status": "connected",
        "api_version": "2.1.5",
        "last_maintenance": "2024-01-15T10:00:00Z",
        "active_sessions": random.randint(50, 200),
        "server_load": round(random.uniform(0.1, 0.8), 2)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)