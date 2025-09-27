from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

Base = declarative_base()

# Fatura durumları
class InvoiceStatus(str, Enum):
    UPLOADED = "uploaded"
    OCR_PROCESSED = "ocr_processed"
    VALIDATED = "validated"
    SENT_TO_ERP = "sent_to_erp"
    ERP_CONFIRMED = "erp_confirmed"
    ERROR = "error"

# Database Models
class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # PDF, JPG, PNG
    status = Column(String, default=InvoiceStatus.UPLOADED)
    
    # OCR sonuçları
    raw_text = Column(Text)
    confidence_score = Column(Float, default=0.0)
    
    # Ayrıştırılan alanlar
    invoice_number = Column(String)
    invoice_date = Column(DateTime)
    company_name = Column(String)
    company_tax_number = Column(String)
    total_amount = Column(Float)
    vat_amount = Column(Float)
    net_amount = Column(Float)
    currency = Column(String, default="TRY")
    
    # Ek veriler JSON formatında
    extracted_fields = Column(JSON)
    validation_data = Column(JSON)
    
    # ERP entegrasyon
    erp_id = Column(String)  # ERP sistemindeki ID
    erp_response = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime)
    validated_at = Column(DateTime)
    sent_to_erp_at = Column(DateTime)
    
    # İlişkiler
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    validations = relationship("ValidationRecord", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    
    description = Column(String)
    quantity = Column(Float)
    unit_price = Column(Float)
    unit = Column(String)  # adet, kg, m2 vb.
    vat_rate = Column(Float)
    line_total = Column(Float)
    
    # JSON formatında ek veriler
    additional_data = Column(JSON)
    
    invoice = relationship("Invoice", back_populates="line_items")

class ValidationRecord(Base):
    __tablename__ = "validation_records"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    
    user_id = Column(String)  # Doğrulama yapan kullanıcı
    field_name = Column(String)  # Hangi alan düzeltildi
    original_value = Column(String)
    corrected_value = Column(String)
    confidence_before = Column(Float)
    confidence_after = Column(Float, default=1.0)
    
    created_at = Column(DateTime, default=func.now())
    
    invoice = relationship("Invoice", back_populates="validations")

class ERPIntegrationLog(Base):
    __tablename__ = "erp_integration_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    
    action = Column(String)  # CREATE, UPDATE, DELETE
    request_data = Column(JSON)
    response_data = Column(JSON)
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=func.now())

# Pydantic Schemas (API için)
class InvoiceBase(BaseModel):
    filename: str
    file_type: str

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceResponse(InvoiceBase):
    id: int
    status: str
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    company_name: Optional[str] = None
    company_tax_number: Optional[str] = None
    total_amount: Optional[float] = None
    vat_amount: Optional[float] = None
    net_amount: Optional[float] = None
    currency: str = "TRY"
    confidence_score: float = 0.0
    created_at: datetime
    
    class Config:
        from_attributes = True

class LineItemCreate(BaseModel):
    description: str
    quantity: float
    unit_price: float
    unit: str = "adet"
    vat_rate: float = 18.0

class LineItemResponse(LineItemCreate):
    id: int
    line_total: float
    
    class Config:
        from_attributes = True

class ValidationRequest(BaseModel):
    field_name: str
    corrected_value: str
    user_id: str = "admin"

class OCRResult(BaseModel):
    raw_text: str
    confidence_score: float
    extracted_fields: Dict[str, Any]
    line_items: List[Dict[str, Any]] = []

class ERPRequest(BaseModel):
    invoice_id: int
    action: str = "CREATE"
    
class ERPResponse(BaseModel):
    success: bool
    erp_id: Optional[str] = None
    message: str
    data: Optional[Dict[str, Any]] = None