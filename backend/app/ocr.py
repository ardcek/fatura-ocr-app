import pytesseract
from PIL import Image
import cv2
import numpy as np
import pdfplumber
import io
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    raw_text: str
    confidence: float
    extracted_fields: Dict[str, any]
    preprocessed_image: Optional[bytes] = None

class InvoiceOCR:
    def __init__(self):
        # Tesseract konfigürasyonu
        self.tesseract_config = r'--oem 3 --psm 6 -l tur'
        
        # Türkiye fatura formatları için regex pattern'ler
        self.patterns = {
            'invoice_number': [
                r'(?:fatura\s*(?:no|numarası|num)?[:.\s]*)\s*([A-Z0-9\-/]+)',
                r'(?:belge\s*(?:no|numarası)?[:.\s]*)\s*([A-Z0-9\-/]+)',
                r'(?:seri\s*no[:.\s]*)\s*([A-Z0-9\-/]+)'
            ],
            'date': [
                r'(?:tarih|date)[:.\s]*(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})',
                r'(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})',
                r'(?:düzenlenme\s*tarihi[:.\s]*)(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})'
            ],
            'tax_number': [
                r'(?:vergi\s*(?:no|numarası)[:.\s]*)(\d{10,11})',
                r'(?:vkn[:.\s]*)(\d{10,11})',
                r'(?:tc[:.\s]*)(\d{11})'
            ],
            'total_amount': [
                r'(?:toplam|total|genel\s*toplam)[:.\s]*([0-9.,]+)(?:\s*TL|\s*₺)?',
                r'(?:ödenecek\s*tutar)[:.\s]*([0-9.,]+)(?:\s*TL|\s*₺)?',
                r'(?:net\s*tutar)[:.\s]*([0-9.,]+)(?:\s*TL|\s*₺)?'
            ],
            'vat_amount': [
                r'(?:kdv|ktv)[:.\s]*([0-9.,]+)(?:\s*TL|\s*₺)?',
                r'(?:katma\s*değer\s*vergisi)[:.\s]*([0-9.,]+)(?:\s*TL|\s*₺)?',
                r'(?:%\s*18)[:.\s]*([0-9.,]+)(?:\s*TL|\s*₺)?'
            ],
            'company_name': [
                r'^([A-ZÇĞIİÖŞÜ][A-Za-zçğıiöşü\s.&-]+)(?:\s+(?:LTD|A\.Ş|SAN|TİC))*',
                r'(?:unvan|firma)[:.\s]*([A-ZÇĞIİÖŞÜ][A-Za-zçğıiöşü\s.&-]+)'
            ],
            'line_items': [
                r'(\d+(?:[.,]\d+)?)\s+([A-Za-zçğıiöşü\s]+)\s+(\d+(?:[.,]\d+)?)\s+([0-9.,]+)'
            ]
        }

    def preprocess_image(self, image: Image.Image) -> Tuple[Image.Image, float]:
        """
        Görüntüyü OCR için optimize eder
        """
        try:
            # PIL Image'ı numpy array'e çevir
            img_array = np.array(image)
            
            # Gri tonlamaya çevir
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Gürültü azaltma
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Kontrast artırma (CLAHE)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Threshold uygulama (ikili görüntü)
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Morfolojik operasyonlar (küçük gürültüleri temizle)
            kernel = np.ones((1,1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Numpy array'i tekrar PIL Image'a çevir
            processed_image = Image.fromarray(cleaned)
            
            # Kalite skoru hesapla (basit metrik)
            quality_score = self._calculate_image_quality(cleaned)
            
            return processed_image, quality_score
            
        except Exception as e:
            logger.error(f"Image preprocessing error: {e}")
            return image, 0.5

    def _calculate_image_quality(self, image: np.ndarray) -> float:
        """
        Görüntü kalitesi için basit bir skor hesaplar
        """
        try:
            # Laplacian variance (blur detection)
            laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
            
            # Normalize et (0-1 arası)
            quality = min(laplacian_var / 1000, 1.0)
            
            return quality
        except:
            return 0.5

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        PDF'den metin çıkarır
        """
        try:
            text = ""
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"PDF text extraction error: {e}")
            return ""

    def extract_text_from_image(self, image: Image.Image) -> Tuple[str, float]:
        """
        Görüntüden OCR ile metin çıkarır
        """
        try:
            # Görüntüyü ön işleme
            processed_image, quality = self.preprocess_image(image)
            
            # Tesseract ile OCR
            text = pytesseract.image_to_string(processed_image, config=self.tesseract_config)
            
            # Güven skoru hesapla
            confidence = self._calculate_ocr_confidence(processed_image)
            
            return text, confidence * quality
            
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return "", 0.0

    def _calculate_ocr_confidence(self, image: Image.Image) -> float:
        """
        OCR güven skoru hesaplar
        """
        try:
            # Tesseract'ın kendi güven skorunu al
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config=self.tesseract_config)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            
            if confidences:
                return sum(confidences) / len(confidences) / 100.0
            return 0.0
        except:
            return 0.5

    def extract_fields_from_text(self, text: str) -> Dict[str, any]:
        """
        Metinden fatura alanlarını çıkarır
        """
        extracted = {}
        
        try:
            # Metni temizle ve normalize et
            cleaned_text = self._clean_text(text)
            
            # Her alan türü için pattern'leri dene
            for field_name, patterns in self.patterns.items():
                if field_name == 'line_items':
                    extracted[field_name] = self._extract_line_items(cleaned_text)
                else:
                    extracted[field_name] = self._extract_single_field(cleaned_text, patterns)
            
            # Veri tiplerini düzelt
            extracted = self._normalize_extracted_data(extracted)
            
        except Exception as e:
            logger.error(f"Field extraction error: {e}")
            
        return extracted

    def _clean_text(self, text: str) -> str:
        """
        Metni OCR sonrası temizler
        """
        # Çoklu boşlukları tekile çevir
        text = re.sub(r'\s+', ' ', text)
        
        # Yaygın OCR hatalarını düzelt
        replacements = {
            'İ': 'I',
            'ı': 'i',
            '0': 'O',  # Context'e göre düzelt
            'S': '5',  # Numbers context
        }
        
        # Basit temizlik
        text = text.strip()
        
        return text

    def _extract_single_field(self, text: str, patterns: List[str]) -> Optional[str]:
        """
        Tek bir alan için pattern matching
        """
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    return match.group(1).strip()
            except Exception as e:
                logger.debug(f"Pattern match error: {e}")
                continue
        return None

    def _extract_line_items(self, text: str) -> List[Dict[str, any]]:
        """
        Fatura satır kalemlerini çıkarır
        """
        items = []
        try:
            lines = text.split('\n')
            for line in lines:
                # Basit pattern - geliştirilmesi gerekir
                match = re.search(r'(\d+(?:[.,]\d+)?)\s+([A-Za-zçğıiöşü\s]+)\s+(\d+(?:[.,]\d+)?)\s+([0-9.,]+)', line)
                if match:
                    items.append({
                        'quantity': self._parse_number(match.group(1)),
                        'description': match.group(2).strip(),
                        'unit_price': self._parse_number(match.group(3)),
                        'total': self._parse_number(match.group(4))
                    })
        except Exception as e:
            logger.error(f"Line items extraction error: {e}")
        
        return items

    def _normalize_extracted_data(self, data: Dict[str, any]) -> Dict[str, any]:
        """
        Çıkarılan verileri normalize eder
        """
        normalized = {}
        
        for key, value in data.items():
            if value is None:
                normalized[key] = None
                continue
                
            if key == 'date' and value:
                normalized[key] = self._parse_date(value)
            elif key in ['total_amount', 'vat_amount'] and value:
                normalized[key] = self._parse_number(value)
            elif key == 'tax_number' and value:
                normalized[key] = re.sub(r'\D', '', value)  # Sadece rakamlar
            else:
                normalized[key] = value
        
        return normalized

    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Tarih string'ini parse eder
        """
        try:
            # Yaygın Türk tarih formatları
            formats = ['%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%y', '%d/%m/%y']
            
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str.strip(), fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.debug(f"Date parsing error: {e}")
            
        return None

    def _parse_number(self, number_str: str) -> Optional[float]:
        """
        Sayı string'ini parse eder
        """
        try:
            # Türk format: 1.234,56 -> 1234.56
            cleaned = number_str.replace('.', '').replace(',', '.')
            
            # Sadece rakam ve nokta bırak
            cleaned = re.sub(r'[^\d.]', '', cleaned)
            
            return float(cleaned) if cleaned else None
            
        except Exception as e:
            logger.debug(f"Number parsing error: {e}")
            return None

    def process_document(self, file_content: bytes, file_type: str) -> OCRResult:
        """
        Ana OCR işlemi - PDF veya resim dosyasını işler
        """
        try:
            if file_type.lower() == 'pdf':
                # PDF işleme
                raw_text = self.extract_text_from_pdf(file_content)
                confidence = 0.9  # PDF metni genelde güvenilir
                
            else:
                # Resim işleme
                image = Image.open(io.BytesIO(file_content))
                raw_text, confidence = self.extract_text_from_image(image)
            
            # Alan ayrıştırma
            extracted_fields = self.extract_fields_from_text(raw_text)
            
            return OCRResult(
                raw_text=raw_text,
                confidence=confidence,
                extracted_fields=extracted_fields
            )
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            return OCRResult(
                raw_text="",
                confidence=0.0,
                extracted_fields={}
            )

# Global OCR instance
ocr_engine = InvoiceOCR()