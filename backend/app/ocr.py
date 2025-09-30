import pytesseractimport pytesseractimport pytesseract

from PIL import Image

import cv2from PIL import Imagefrom PIL import Image

import numpy as np

import ioimport cv2import cv2

import re

import jsonimport numpy as npimport numpy as np

from datetime import datetime

from typing import Dict, List, Optional, Tupleimport ioimport io

from dataclasses import dataclass

import loggingimport reimport re



# Windows Tesseract path'ini ayarlaimport jsonimport json

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

from datetime import datetimefrom datetime import datetime

# Logging setup

logging.basicConfig(level=logging.INFO)from typing import Dict, List, Optional, Tuplefrom typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from dataclasses import dataclassfrom dataclasses import dataclass

@dataclass

class OCRResult:import loggingimport logging

    raw_text: str

    confidence: float

    extracted_fields: Dict[str, any]

    preprocessed_image: Optional[bytes] = None# Windows Tesseract path'ini ayarla# Windows Tesseract path'ini ayarla



class AIInvoiceOCR:pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def __init__(self):

        # Tesseract konfigürasyonu - İngilizce (daha stabil)

        self.tesseract_config = r'--oem 3 --psm 6 -l eng'

        # Logging setup# Logging setup

        # AI destekli fatura tanıma sistemi

        self.ai_patterns = self._initialize_ai_patterns()logging.basicConfig(level=logging.INFO)logging.basicConfig(level=logging.INFO)

        

    def _initialize_ai_patterns(self) -> Dict:logger = logging.getLogger(__name__)logger = logging.getLogger(__name__)

        """AI destekli pattern sistemi"""

        return {

            'invoice_number': {

                'primary': [@dataclass@dataclass

                    r'(TR[\d\.]+)',  # TR1.2 gibi

                    r'([A-Z]{2,5}[\-\.\s]*\d+[\.\d]*)',  # Fatura no formatlarıclass OCRResult:class OCRResult:

                    r'(?:fatura|invoice)[\s\:]*([A-Z0-9\-\.\/]+)',

                    r'(?:no|number)[\s\:]*([A-Z0-9\-\.\/]+)'    raw_text: str    raw_text: str

                ],

                'context_clues': ['fatura', 'invoice', 'belge', 'document', 'TR'],    confidence: float    confidence: float

                'validation': lambda x: len(x) > 2 and any(c.isdigit() for c in x)

            },    extracted_fields: Dict[str, any]    extracted_fields: Dict[str, any]

            'date': {

                'primary': [    preprocessed_image: Optional[bytes] = None    preprocessed_image: Optional[bytes] = None

                    r'(\d{1,2}[\-\/\.]\d{1,2}[\-\/\.]\d{2,4})',  # 08-12-2015

                    r'(\d{4}[\-\/\.]\d{1,2}[\-\/\.]\d{1,2})',   # 2015-12-08

                ],

                'context_clues': ['tarih', 'date', 'düzenlenme'],class AIInvoiceOCR:class AIInvoiceOCR:

                'validation': lambda x: self._validate_date(x)

            },    def __init__(self):    def __init__(self):

            'total_amount': {

                'primary': [        # Tesseract konfigürasyonu - İngilizce (daha stabil)        # Tesseract konfigürasyonu - İngilizce (daha stabil)

                    r'(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})\s*(?:TL|TRY|₺)',

                    r'(?:toplam|total|tutar)[\s\:]*(\d+[\.,\d]*)',        self.tesseract_config = r'--oem 3 --psm 6 -l eng'        self.tesseract_config = r'--oem 3 --psm 6 -l eng'

                    r'(\d+[\.,]\d{2})\s*(?:TL|TRY)'

                ],                

                'context_clues': ['toplam', 'total', 'tutar', 'ödenecek', 'TL', 'TRY'],

                'validation': lambda x: self._validate_amount(x)        # AI destekli fatura tanıma sistemi        # AI destekli fatura tanıma sistemi

            },

            'company_name': {        self.ai_patterns = self._initialize_ai_patterns()        self.ai_patterns = self._initialize_ai_patterns()

                'primary': [

                    r'^([A-Z][A-Z\s]{2,30})',  # İlk satırdaki büyük harfli metin                

                    r'([A-Z][A-Za-z\s]{3,50})(?:\s+(?:LTD|A\.Ş|SAN|TİC))',

                ],    def _initialize_ai_patterns(self) -> Dict:    def _initialize_ai_patterns(self) -> Dict:

                'context_clues': ['firma', 'company', 'unvan'],

                'validation': lambda x: len(x) > 2 and x[0].isupper()        """AI destekli pattern sistemi"""        """AI destekli pattern sistemi"""

            },

            'ettn': {        return {        return {

                'primary': [

                    r'([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})'            'invoice_number': {            'invoice_number': {

                ],

                'context_clues': ['ETTN', 'ettn'],                'primary': [                'primary': [

                'validation': lambda x: len(x) == 36 and x.count('-') == 4

            }                    r'(TR[\d\.]+)',  # TR1.2 gibi                    r'(TR[\d\.]+)',  # TR1.2 gibi

        }

                    r'([A-Z]{2,5}[\-\.\s]*\d+[\.\d]*)',  # Fatura no formatları                    r'([A-Z]{2,5}[\-\.\s]*\d+[\.\d]*)',  # Fatura no formatları

    def _validate_date(self, date_str: str) -> bool:

        """Tarih validasyonu"""                    r'(?:fatura|invoice)[\s\:]*([A-Z0-9\-\.\/]+)',                    r'(?:fatura|invoice)[\s\:]*([A-Z0-9\-\.\/]+)',

        try:

            formats = ['%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y', '%Y-%m-%d']                    r'(?:no|number)[\s\:]*([A-Z0-9\-\.\/]+)'                    r'(?:no|number)[\s\:]*([A-Z0-9\-\.\/]+)'

            for fmt in formats:

                try:                ],                ],

                    datetime.strptime(date_str, fmt)

                    return True                'context_clues': ['fatura', 'invoice', 'belge', 'document', 'TR'],                'context_clues': ['fatura', 'invoice', 'belge', 'document', 'TR'],

                except:

                    continue                'validation': lambda x: len(x) > 2 and any(c.isdigit() for c in x)                'validation': lambda x: len(x) > 2 and any(c.isdigit() for c in x)

            return False

        except:            },            },

            return False

            'date': {            'date': {

    def _validate_amount(self, amount_str: str) -> bool:

        """Tutar validasyonu"""                'primary': [                'primary': [

        try:

            # Sayı içeriyor ve makul bir tutar aralığında                    r'(\d{1,2}[\-\/\.]\d{1,2}[\-\/\.]\d{2,4})',  # 08-12-2015                    r'(\d{1,2}[\-\/\.]\d{1,2}[\-\/\.]\d{2,4})',  # 08-12-2015

            clean = re.sub(r'[^\d\.,]', '', amount_str)

            if ',' in clean:                    r'(\d{4}[\-\/\.]\d{1,2}[\-\/\.]\d{1,2})',   # 2015-12-08                    r'(\d{4}[\-\/\.]\d{1,2}[\-\/\.]\d{1,2})',   # 2015-12-08

                clean = clean.replace(',', '.')

            value = float(clean)                ],                ],

            return 0.01 <= value <= 999999.99

        except:                'context_clues': ['tarih', 'date', 'düzenlenme'],                'context_clues': ['tarih', 'date', 'düzenlenme'],

            return False

                'validation': lambda x: self._validate_date(x)                'validation': lambda x: self._validate_date(x)

    def preprocess_image(self, image: Image.Image) -> Tuple[Image.Image, float]:

        """Görüntüyü OCR için optimize eder"""            },            },

        try:

            img_array = np.array(image)            'total_amount': {            'total_amount': {

            

            # Gri tonlama                'primary': [                'primary': [

            if len(img_array.shape) == 3:

                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)                    r'(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})\s*(?:TL|TRY|₺)',                    r'(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})\s*(?:TL|TRY|₺)',

            else:

                gray = img_array                    r'(?:toplam|total|tutar)[\s\:]*(\d+[\.,\d]*)',                    r'(?:toplam|total|tutar)[\s\:]*(\d+[\.,\d]*)',

            

            # Kontrast artırma                    r'(\d+[\.,]\d{2})\s*(?:TL|TRY)'                    r'(\d+[\.,]\d{2})\s*(?:TL|TRY)'

            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))

            enhanced = clahe.apply(gray)                ],                ],

            

            # Gürültü giderme                'context_clues': ['toplam', 'total', 'tutar', 'ödenecek', 'TL', 'TRY'],                'context_clues': ['toplam', 'total', 'tutar', 'ödenecek', 'TL', 'TRY'],

            denoised = cv2.medianBlur(enhanced, 3)

                            'validation': lambda x: self._validate_amount(x)                'validation': lambda x: self._validate_amount(x)

            # Threshold

            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)            },            },

            

            # PIL'e geri çevir            'company_name': {            'company_name': {

            processed_image = Image.fromarray(binary)

                            'primary': [                'primary': [

            return processed_image, 0.85

                                r'^([A-Z][A-Z\s]{2,30})',  # İlk satırdaki büyük harfli metin                    r'^([A-Z][A-Z\s]{2,30})',  # İlk satırdaki büyük harfli metin

        except Exception as e:

            logger.error(f"Image preprocessing error: {e}")                    r'([A-Z][A-Za-z\s]{3,50})(?:\s+(?:LTD|A\.Ş|SAN|TİC))',                    r'([A-Z][A-Za-z\s]{3,50})(?:\s+(?:LTD|A\.Ş|SAN|TİC))',

            return image, 0.5

                ],                ],

    def extract_text_from_image(self, image: Image.Image) -> Tuple[str, float]:

        """Tesseract ile OCR"""                'context_clues': ['firma', 'company', 'unvan'],                'context_clues': ['firma', 'company', 'unvan'],

        try:

            # Ön işleme                'validation': lambda x: len(x) > 2 and x[0].isupper()                'validation': lambda x: len(x) > 2 and x[0].isupper()

            processed_image, quality = self.preprocess_image(image)

                        },            },

            # OCR

            text = pytesseract.image_to_string(processed_image, config=self.tesseract_config)            'ettn': {            'ettn': {

            

            # Güven skoru hesapla                'primary': [                'primary': [

            confidence = self._calculate_confidence(processed_image, text)

                                r'([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})'                    r'([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})'

            logger.info(f"OCR completed - Text: {len(text)} chars, Confidence: {confidence:.3f}")

                            ],                ],

            return text, confidence * quality

                            'context_clues': ['ETTN', 'ettn'],                'context_clues': ['ETTN', 'ettn'],

        except Exception as e:

            logger.error(f"OCR error: {e}")                'validation': lambda x: len(x) == 36 and x.count('-') == 4                'validation': lambda x: len(x) == 36 and x.count('-') == 4

            return "", 0.0

            }            }

    def _calculate_confidence(self, image: Image.Image, text: str) -> float:

        """Güven skoru hesaplama"""        }        }

        try:

            # Tesseract confidence

            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, 

                                           config=self.tesseract_config)    def _validate_date(self, date_str: str) -> bool:    def _validate_date(self, date_str: str) -> bool:

            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]

                    """Tarih validasyonu"""        """Tarih validasyonu"""

            if confidences:

                base_conf = sum(confidences) / len(confidences) / 100.0        try:        try:

            else:

                base_conf = 0.3            formats = ['%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y', '%Y-%m-%d']            formats = ['%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y', '%Y-%m-%d']

            

            # Metin kalitesi bonusu            for fmt in formats:            for fmt in formats:

            text_quality = self._assess_text_quality(text)

                            try:                try:

            return min(base_conf * text_quality, 1.0)

                                datetime.strptime(date_str, fmt)                    datetime.strptime(date_str, fmt)

        except:

            return 0.3                    return True                    return True



    def _assess_text_quality(self, text: str) -> float:                except:                except:

        """Metin kalitesi değerlendirmesi"""

        if not text:                    continue                    continue

            return 0.1

                    return False            return False

        quality_score = 0.5  # Base score

                except:        except:

        # Uzunluk bonusu

        if len(text) > 50:            return False            return False

            quality_score += 0.2

        

        # Sayı varlığı (faturalarda önemli)

        if re.search(r'\d+', text):    def _validate_amount(self, amount_str: str) -> bool:    def _validate_amount(self, amount_str: str) -> bool:

            quality_score += 0.2

                """Tutar validasyonu"""        """Tutar validasyonu"""

        # Tarih pattern'i

        if re.search(r'\d{1,2}[\-\/\.]\d{1,2}[\-\/\.]\d{2,4}', text):        try:        try:

            quality_score += 0.1

                    # Sayı içeriyor ve makul bir tutar aralığında            # Sayı içeriyor ve makul bir tutar aralığında

        return min(quality_score, 1.0)

            clean = re.sub(r'[^\d\.,]', '', amount_str)            clean = re.sub(r'[^\d\.,]', '', amount_str)

    def ai_extract_fields(self, text: str) -> Dict[str, any]:

        """AI destekli alan çıkarma sistemi"""            if ',' in clean:            if ',' in clean:

        extracted = {}

                        clean = clean.replace(',', '.')                clean = clean.replace(',', '.')

        try:

            # Her field için AI pattern matching            value = float(clean)            value = float(clean)

            for field_name, config in self.ai_patterns.items():

                result = self._ai_field_extraction(text, field_name, config)            return 0.01 <= value <= 999999.99            return 0.01 <= value <= 999999.99

                extracted[field_name] = result

                    except:        except:

            # AI post-processing

            extracted = self._ai_post_process(text, extracted)            return False            return False

            

            logger.info(f"AI extraction completed: {len([v for v in extracted.values() if v])} fields found")

            

        except Exception as e:    def preprocess_image(self, image: Image.Image) -> Tuple[Image.Image, float]:    def preprocess_image(self, image: Image.Image) -> Tuple[Image.Image, float]:

            logger.error(f"AI extraction error: {e}")

                    """Görüntüyü OCR için optimize eder"""        """Görüntüyü OCR için optimize eder"""

        return extracted

        try:        try:

    def _ai_field_extraction(self, text: str, field_name: str, config: Dict) -> Optional[str]:

        """Tek field için AI extraction"""            img_array = np.array(image)            img_array = np.array(image)

        

        # Primary pattern'leri dene                        

        for pattern in config['primary']:

            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)            # Gri tonlama            # Gri tonlama

            for match in matches:

                if config['validation'](match):            if len(img_array.shape) == 3:            if len(img_array.shape) == 3:

                    logger.debug(f"Found {field_name}: {match}")

                    return match                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        

        # Context-based search            else:            else:

        return self._context_based_search(text, field_name, config)

                gray = img_array                gray = img_array

    def _context_based_search(self, text: str, field_name: str, config: Dict) -> Optional[str]:

        """Context tabanlı akıllı arama"""                        

        

        lines = text.split('\n')            # Kontrast artırma            # Kontrast artırma

        context_clues = config['context_clues']

                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))

        for i, line in enumerate(lines):

            line_lower = line.lower()            enhanced = clahe.apply(gray)            enhanced = clahe.apply(gray)

            

            # Context clue bulundu mu?                        

            for clue in context_clues:

                if clue.lower() in line_lower:            # Gürültü giderme            # Gürültü giderme

                    # Bu satır ve komşu satırlarda değer ara

                    search_lines = lines[max(0,i-1):min(len(lines),i+3)]            denoised = cv2.medianBlur(enhanced, 3)            denoised = cv2.medianBlur(enhanced, 3)

                    search_text = ' '.join(search_lines)

                                            

                    for pattern in config['primary']:

                        matches = re.findall(pattern, search_text, re.IGNORECASE)            # Threshold            # Threshold

                        for match in matches:

                            if config['validation'](match):            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                                return match

                                

        return None

            # PIL'e geri çevir            # PIL'e geri çevir

    def _ai_post_process(self, text: str, extracted: Dict) -> Dict:

        """AI post-processing iyileştirmeleri"""            processed_image = Image.fromarray(binary)            processed_image = Image.fromarray(binary)

        

        # Elektrik faturası özel işlemleri                        

        if any(word in text.lower() for word in ['elektrik', 'kwh', 'enerji']):

            extracted['invoice_type'] = 'electricity'            return processed_image, 0.85            return processed_image, 0.85

            

            # KWH tüketimi                        

            kwh_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*KWH', text, re.IGNORECASE)

            if kwh_match:        except Exception as e:        except Exception as e:

                extracted['consumption'] = f"{kwh_match.group(1)} KWH"

                    logger.error(f"Image preprocessing error: {e}")            logger.error(f"Image preprocessing error: {e}")

        # Fatura numarası iyileştirme

        if not extracted.get('invoice_number'):            return image, 0.5            return image, 0.5

            # TR ile başlayan herhangi bir değer

            tr_match = re.search(r'(TR[\d\.]+)', text)

            if tr_match:

                extracted['invoice_number'] = tr_match.group(1)    def extract_text_from_image(self, image: Image.Image) -> Tuple[str, float]:    def extract_text_from_image(self, image: Image.Image) -> Tuple[str, float]:

        

        # Firma adı iyileştirme        """Tesseract ile OCR"""        """Tesseract ile OCR"""

        if not extracted.get('company_name'):

            lines = text.split('\n')        try:        try:

            for line in lines[:3]:  # İlk 3 satır

                line = line.strip()            # Ön işleme            # Ön işleme

                if len(line) > 3 and line[0].isupper() and not re.search(r'\d{3,}', line):

                    extracted['company_name'] = line[:40]            processed_image, quality = self.preprocess_image(image)            processed_image, quality = self.preprocess_image(image)

                    break

                                

        # Tarih normalize etme

        if extracted.get('date'):            # OCR            # OCR

            extracted['date'] = self._normalize_date(extracted['date'])

                    text = pytesseract.image_to_string(processed_image, config=self.tesseract_config)            text = pytesseract.image_to_string(processed_image, config=self.tesseract_config)

        # Tutar normalize etme

        if extracted.get('total_amount'):                        

            extracted['total_amount'] = self._normalize_amount(extracted['total_amount'])

                    # Güven skoru hesapla            # Güven skoru hesapla

        return extracted

            confidence = self._calculate_confidence(processed_image, text)            confidence = self._calculate_confidence(processed_image, text)

    def _normalize_date(self, date_str: str) -> str:

        """Tarih formatını normalize et"""                        

        try:

            formats = ['%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y', '%Y-%m-%d']            logger.info(f"OCR completed - Text: {len(text)} chars, Confidence: {confidence:.3f}")            logger.info(f"OCR completed - Text: {len(text)} chars, Confidence: {confidence:.3f}")

            for fmt in formats:

                try:                        

                    date_obj = datetime.strptime(date_str, fmt)

                    return date_obj.strftime('%Y-%m-%d')            return text, confidence * quality            return text, confidence * quality

                except:

                    continue                        

            return date_str

        except:        except Exception as e:        except Exception as e:

            return date_str

            logger.error(f"OCR error: {e}")            logger.error(f"OCR error: {e}")

    def _normalize_amount(self, amount_str: str) -> float:

        """Tutar formatını normalize et"""            return "", 0.0            return "", 0.0

        try:

            # Türk format: 1.234,56 -> 1234.56

            clean = amount_str.replace('.', '').replace(',', '.')

            clean = re.sub(r'[^\d\.]', '', clean)    def _calculate_confidence(self, image: Image.Image, text: str) -> float:    def _calculate_confidence(self, image: Image.Image, text: str) -> float:

            return float(clean) if clean else 0.0

        except:        """Güven skoru hesaplama"""        """Güven skoru hesaplama"""

            return 0.0

        try:        try:

    def process_document(self, file_content: bytes, file_type: str) -> OCRResult:

        """Ana AI destekli OCR işlemi"""            # Tesseract confidence            # Tesseract confidence

        try:

            logger.info(f"AI OCR Processing - Size: {len(file_content)} bytes")            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT,             data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, 

            

            # Resim yükle                                           config=self.tesseract_config)                                           config=self.tesseract_config)

            image = Image.open(io.BytesIO(file_content))

                        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]

            # OCR ile metin çıkar

            raw_text, confidence = self.extract_text_from_image(image)                        

            

            if not raw_text.strip():            if confidences:            if confidences:

                logger.warning("No text extracted from image")

                return OCRResult(                base_conf = sum(confidences) / len(confidences) / 100.0                base_conf = sum(confidences) / len(confidences) / 100.0

                    raw_text="OCR could not extract any text",

                    confidence=0.0,            else:            else:

                    extracted_fields={}

                )                base_conf = 0.3                base_conf = 0.3

            

            logger.info(f"Raw text extracted: {len(raw_text)} characters")                        

            

            # AI ile alanları çıkar            # Metin kalitesi bonusu            # Metin kalitesi bonusu

            extracted_fields = self.ai_extract_fields(raw_text)

                        text_quality = self._assess_text_quality(text)            text_quality = self._assess_text_quality(text)

            # Sonuçları logla

            found_fields = [k for k, v in extracted_fields.items() if v]                        

            logger.info(f"AI found fields: {', '.join(found_fields)}")

                        return min(base_conf * text_quality, 1.0)            return min(base_conf * text_quality, 1.0)

            return OCRResult(

                raw_text=raw_text,                        

                confidence=confidence,

                extracted_fields=extracted_fields        except:        except:

            )

                        return 0.3            return 0.3

        except Exception as e:

            logger.error(f"AI OCR processing error: {e}")

            return OCRResult(

                raw_text=f"AI OCR Error: {str(e)}",    def _assess_text_quality(self, text: str) -> float:    def _assess_text_quality(self, text: str) -> float:

                confidence=0.0,

                extracted_fields={}        """Metin kalitesi değerlendirmesi"""        """Metin kalitesi değerlendirmesi"""

            )

        if not text:        if not text:

# Global AI OCR instance

ocr_engine = AIInvoiceOCR()            return 0.1            return 0.1

                

        quality_score = 0.5  # Base score        quality_score = 0.5  # Base score

                

        # Uzunluk bonusu        # Uzunluk bonusu

        if len(text) > 50:        if len(text) > 50:

            quality_score += 0.2            quality_score += 0.2

                

        # Sayı varlığı (faturalarda önemli)        # Sayı varlığı (faturalarda önemli)

        if re.search(r'\d+', text):        if re.search(r'\d+', text):

            quality_score += 0.2            quality_score += 0.2

                

        # Tarih pattern'i        # Tarih pattern'i

        if re.search(r'\d{1,2}[\-\/\.]\d{1,2}[\-\/\.]\d{2,4}', text):        if re.search(r'\d{1,2}[\-\/\.]\d{1,2}[\-\/\.]\d{2,4}', text):

            quality_score += 0.1            quality_score += 0.1

                

        return min(quality_score, 1.0)        return min(quality_score, 1.0)



    def ai_extract_fields(self, text: str) -> Dict[str, any]:    def ai_extract_fields(self, text: str) -> Dict[str, any]:

        """AI destekli alan çıkarma sistemi"""        """AI destekli alan çıkarma sistemi"""

        extracted = {}        extracted = {}

                

        try:        try:

            # Her field için AI pattern matching            # Her field için AI pattern matching

            for field_name, config in self.ai_patterns.items():            for field_name, config in self.ai_patterns.items():

                result = self._ai_field_extraction(text, field_name, config)                result = self._ai_field_extraction(text, field_name, config)

                extracted[field_name] = result                extracted[field_name] = result

                        

            # AI post-processing            # AI post-processing

            extracted = self._ai_post_process(text, extracted)            extracted = self._ai_post_process(text, extracted)

                        

            logger.info(f"AI extraction completed: {len([v for v in extracted.values() if v])} fields found")            logger.info(f"AI extraction completed: {len([v for v in extracted.values() if v])} fields found")

                        

        except Exception as e:        except Exception as e:

            logger.error(f"AI extraction error: {e}")            logger.error(f"AI extraction error: {e}")

                        

        return extracted        return extracted



    def _ai_field_extraction(self, text: str, field_name: str, config: Dict) -> Optional[str]:    def _ai_field_extraction(self, text: str, field_name: str, config: Dict) -> Optional[str]:

        """Tek field için AI extraction"""        """Tek field için AI extraction"""

                

        # Primary pattern'leri dene        # Primary pattern'leri dene

        for pattern in config['primary']:        for pattern in config['primary']:

            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)

            for match in matches:            for match in matches:

                if config['validation'](match):                if config['validation'](match):

                    logger.debug(f"Found {field_name}: {match}")                    logger.debug(f"Found {field_name}: {match}")

                    return match                    return match

                

        # Context-based search        # Context-based search

        return self._context_based_search(text, field_name, config)        return self._context_based_search(text, field_name, config)



    def _context_based_search(self, text: str, field_name: str, config: Dict) -> Optional[str]:    def _context_based_search(self, text: str, field_name: str, config: Dict) -> Optional[str]:

        """Context tabanlı akıllı arama"""        """Context tabanlı akıllı arama"""

                

        lines = text.split('\n')        lines = text.split('\n')

        context_clues = config['context_clues']        context_clues = config['context_clues']

                

        for i, line in enumerate(lines):        for i, line in enumerate(lines):

            line_lower = line.lower()            line_lower = line.lower()

                        

            # Context clue bulundu mu?            # Context clue bulundu mu?

            for clue in context_clues:            for clue in context_clues:

                if clue.lower() in line_lower:                if clue.lower() in line_lower:

                    # Bu satır ve komşu satırlarda değer ara                    # Bu satır ve komşu satırlarda değer ara

                    search_lines = lines[max(0,i-1):min(len(lines),i+3)]                    search_lines = lines[max(0,i-1):min(len(lines),i+3)]

                    search_text = ' '.join(search_lines)                    search_text = ' '.join(search_lines)

                                        

                    for pattern in config['primary']:                    for pattern in config['primary']:

                        matches = re.findall(pattern, search_text, re.IGNORECASE)                        matches = re.findall(pattern, search_text, re.IGNORECASE)

                        for match in matches:                        for match in matches:

                            if config['validation'](match):                            if config['validation'](match):

                                return match                                return match

                

        return None        return None



    def _ai_post_process(self, text: str, extracted: Dict) -> Dict:    def _ai_post_process(self, text: str, extracted: Dict) -> Dict:

        """AI post-processing iyileştirmeleri"""        """AI post-processing iyileştirmeleri"""

                

        # Elektrik faturası özel işlemleri        # Elektrik faturası özel işlemleri

        if any(word in text.lower() for word in ['elektrik', 'kwh', 'enerji']):        if any(word in text.lower() for word in ['elektrik', 'kwh', 'enerji']):

            extracted['invoice_type'] = 'electricity'            extracted['invoice_type'] = 'electricity'

                        

            # KWH tüketimi            # KWH tüketimi

            kwh_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*KWH', text, re.IGNORECASE)            kwh_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*KWH', text, re.IGNORECASE)

            if kwh_match:            if kwh_match:

                extracted['consumption'] = f"{kwh_match.group(1)} KWH"                extracted['consumption'] = f"{kwh_match.group(1)} KWH"

                

        # Fatura numarası iyileştirme        # Fatura numarası iyileştirme

        if not extracted.get('invoice_number'):        if not extracted.get('invoice_number'):

            # TR ile başlayan herhangi bir değer            # TR ile başlayan herhangi bir değer

            tr_match = re.search(r'(TR[\d\.]+)', text)            tr_match = re.search(r'(TR[\d\.]+)', text)

            if tr_match:            if tr_match:

                extracted['invoice_number'] = tr_match.group(1)                extracted['invoice_number'] = tr_match.group(1)

                

        # Firma adı iyileştirme        # Firma adı iyileştirme

        if not extracted.get('company_name'):        if not extracted.get('company_name'):

            lines = text.split('\n')            lines = text.split('\n')

            for line in lines[:3]:  # İlk 3 satır            for line in lines[:3]:  # İlk 3 satır

                line = line.strip()                line = line.strip()

                if len(line) > 3 and line[0].isupper() and not re.search(r'\d{3,}', line):                if len(line) > 3 and line[0].isupper() and not re.search(r'\d{3,}', line):

                    extracted['company_name'] = line[:40]                    extracted['company_name'] = line[:40]

                    break                    break

                

        # Tarih normalize etme        # Tarih normalize etme

        if extracted.get('date'):        if extracted.get('date'):

            extracted['date'] = self._normalize_date(extracted['date'])            extracted['date'] = self._normalize_date(extracted['date'])

                

        # Tutar normalize etme        # Tutar normalize etme

        if extracted.get('total_amount'):        if extracted.get('total_amount'):

            extracted['total_amount'] = self._normalize_amount(extracted['total_amount'])            extracted['total_amount'] = self._normalize_amount(extracted['total_amount'])

                

        return extracted        return extracted



    def _normalize_date(self, date_str: str) -> str:    def _normalize_date(self, date_str: str) -> str:

        """Tarih formatını normalize et"""        """Tarih formatını normalize et"""

        try:        try:

            formats = ['%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y', '%Y-%m-%d']            formats = ['%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y', '%Y-%m-%d']

            for fmt in formats:            for fmt in formats:

                try:                try:

                    date_obj = datetime.strptime(date_str, fmt)                    date_obj = datetime.strptime(date_str, fmt)

                    return date_obj.strftime('%Y-%m-%d')                    return date_obj.strftime('%Y-%m-%d')

                except:                except:

                    continue                    continue

            return date_str            return date_str

        except:        except:

            return date_str            return date_str



    def _normalize_amount(self, amount_str: str) -> float:    def _normalize_amount(self, amount_str: str) -> float:

        """Tutar formatını normalize et"""        """Tutar formatını normalize et"""

        try:        try:

            # Türk format: 1.234,56 -> 1234.56            # Türk format: 1.234,56 -> 1234.56

            clean = amount_str.replace('.', '').replace(',', '.')            clean = amount_str.replace('.', '').replace(',', '.')

            clean = re.sub(r'[^\d\.]', '', clean)            clean = re.sub(r'[^\d\.]', '', clean)

            return float(clean) if clean else 0.0            return float(clean) if clean else 0.0

        except:        except:

            return 0.0            return 0.0



    def process_document(self, file_content: bytes, file_type: str) -> OCRResult:    def process_document(self, file_content: bytes, file_type: str) -> OCRResult:

        """Ana AI destekli OCR işlemi"""        """Ana AI destekli OCR işlemi"""

        try:        try:

            logger.info(f"AI OCR Processing - Size: {len(file_content)} bytes")            logger.info(f"AI OCR Processing - Size: {len(file_content)} bytes")

                        

            # Resim yükle            # Resim yükle

            image = Image.open(io.BytesIO(file_content))            image = Image.open(io.BytesIO(file_content))

                        

            # OCR ile metin çıkar            # OCR ile metin çıkar

            raw_text, confidence = self.extract_text_from_image(image)            raw_text, confidence = self.extract_text_from_image(image)

                        

            if not raw_text.strip():            if not raw_text.strip():

                logger.warning("No text extracted from image")                logger.warning("No text extracted from image")

                return OCRResult(                return OCRResult(

                    raw_text="OCR could not extract any text",                    raw_text="OCR could not extract any text",

                    confidence=0.0,                    confidence=0.0,

                    extracted_fields={}                    extracted_fields={}

                )                )

                        

            logger.info(f"Raw text extracted: {len(raw_text)} characters")            logger.info(f"Raw text extracted: {len(raw_text)} characters")

                        

            # AI ile alanları çıkar            # AI ile alanları çıkar

            extracted_fields = self.ai_extract_fields(raw_text)            extracted_fields = self.ai_extract_fields(raw_text)

                        

            # Sonuçları logla            # Sonuçları logla

            found_fields = [k for k, v in extracted_fields.items() if v]            found_fields = [k for k, v in extracted_fields.items() if v]

            logger.info(f"AI found fields: {', '.join(found_fields)}")            logger.info(f"AI found fields: {', '.join(found_fields)}")

                        

            return OCRResult(            return OCRResult(

                raw_text=raw_text,                raw_text=raw_text,

                confidence=confidence,                confidence=confidence,

                extracted_fields=extracted_fields                extracted_fields=extracted_fields

            )            )

                        

        except Exception as e:        except Exception as e:

            logger.error(f"AI OCR processing error: {e}")            logger.error(f"AI OCR processing error: {e}")

            return OCRResult(            return OCRResult(

                raw_text=f"AI OCR Error: {str(e)}",                raw_text=f"AI OCR Error: {str(e)}",

                confidence=0.0,                confidence=0.0,

                extracted_fields={}                extracted_fields={}

            )            )



# Global AI OCR instance# Global AI OCR instance

ocr_engine = AIInvoiceOCR()ocr_engine = AIInvoiceOCR()