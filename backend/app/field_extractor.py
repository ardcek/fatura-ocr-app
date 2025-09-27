import re
import spacy
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)

@dataclass
class ExtractedField:
    value: Any
    confidence: float
    source_text: str
    method: str  # regex, nlp, rule-based

class AdvancedFieldExtractor:
    def __init__(self):
        # spaCy modelini yükle (Turkish model gerekirse indirilecek)
        try:
            self.nlp = spacy.load("tr_core_news_sm")
        except OSError:
            # Türkçe model yoksa İngilizce kullan
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.warning("Turkish spaCy model not found, using English model")
            except OSError:
                self.nlp = None
                logger.warning("No spaCy model found, using regex-only extraction")
        
        # Gelişmiş regex pattern'leri
        self.advanced_patterns = {
            'invoice_number': [
                r'(?:fatura\s*(?:no|numarası|num)?[:.\s]*)\s*([A-Z0-9\-/\.]+)',
                r'(?:belge\s*(?:no|numarası)?[:.\s]*)\s*([A-Z0-9\-/\.]+)',
                r'(?:seri\s*(?:no|sıra\s*no)?[:.\s]*)\s*([A-Z0-9\-/\.]+)',
                r'(?:invoice\s*(?:no|number)?[:.\s]*)\s*([A-Z0-9\-/\.]+)',
                r'(?:fiş\s*no[:.\s]*)\s*([A-Z0-9\-/\.]+)'
            ],
            'date': [
                r'(?:tarih|date|düzenleme\s*tarihi)[:.\s]*(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})',
                r'(?:\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})',
                r'(?:fiş\s*tarihi[:.\s]*)(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})',
                r'(?:düzenlenme\s*tarihi[:.\s]*)(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})'
            ],
            'tax_number': [
                r'(?:vergi\s*(?:no|numarası)[:.\s]*)(\d{10,11})',
                r'(?:vkn|v\.k\.n)[:.\s]*(\d{10,11})',
                r'(?:tc|t\.c)[:.\s]*(\d{11})',
                r'(?:tax\s*(?:no|id)[:.\s]*)(\d{10,11})'
            ],
            'company_name': [
                r'(?:unvan|firma\s*adı|company)[:.\s]*([A-ZÇĞIİÖŞÜa-zçğıiöşü\s.&\-\'\"]+?)(?:\s+(?:LTD|A\.Ş|SAN|TİC|INC|LLC)\.?)*',
                r'^([A-ZÇĞIİÖŞÜ][A-Za-zçğıiöşü\s.&\-\'\"]+)(?:\s+(?:LTD|A\.Ş|SAN|TİC|INC|LLC)\.?)*',
                r'(?:satıcı|seller)[:.\s]*([A-ZÇĞIİÖŞÜa-zçğıiöşü\s.&\-\'\"]+)'
            ],
            'total_amount': [
                r'(?:toplam|total|genel\s*toplam|grand\s*total)[:.\s]*([0-9.,]+)(?:\s*(?:TL|₺|USD|EUR))?',
                r'(?:ödenecek\s*tutar|amount\s*due)[:.\s]*([0-9.,]+)(?:\s*(?:TL|₺|USD|EUR))?',
                r'(?:brüt\s*tutar|gross\s*amount)[:.\s]*([0-9.,]+)(?:\s*(?:TL|₺|USD|EUR))?',
                r'(?:ara\s*toplam|subtotal)[:.\s]*([0-9.,]+)(?:\s*(?:TL|₺|USD|EUR))?'
            ],
            'net_amount': [
                r'(?:net\s*tutar|net\s*amount)[:.\s]*([0-9.,]+)(?:\s*(?:TL|₺|USD|EUR))?',
                r'(?:vergisiz\s*tutar|tax\s*exclusive)[:.\s]*([0-9.,]+)(?:\s*(?:TL|₺|USD|EUR))?'
            ],
            'vat_amount': [
                r'(?:kdv|ktv|vat)[:.\s]*([0-9.,]+)(?:\s*(?:TL|₺|USD|EUR))?',
                r'(?:katma\s*değer\s*vergisi)[:.\s]*([0-9.,]+)(?:\s*(?:TL|₺|USD|EUR))?',
                r'(?:%\s*(?:18|8|1))[:.\s]*([0-9.,]+)(?:\s*(?:TL|₺|USD|EUR))?'
            ],
            'vat_rate': [
                r'(?:kdv\s*oranı|vat\s*rate)[:.\s]*(?:%\s*)?(\d{1,2})',
                r'(%\s*(?:18|8|1))',
                r'(?:vergi\s*oranı)[:.\s]*(?:%\s*)?(\d{1,2})'
            ],
            'currency': [
                r'(TL|₺|USD|EUR|GBP)(?:\s|$)',
                r'(?:para\s*birimi|currency)[:.\s]*(TL|USD|EUR|GBP)'
            ],
            'iban': [
                r'(?:iban|hesap\s*no)[:.\s]*(TR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2})',
                r'(TR\d{24})'
            ],
            'due_date': [
                r'(?:vade\s*tarihi|due\s*date)[:.\s]*(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})',
                r'(?:son\s*ödeme\s*tarihi)[:.\s]*(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})'
            ]
        }
        
        # Türk lirası format recognizer
        self.turkish_number_pattern = r'\d{1,3}(?:\.\d{3})*(?:,\d{2})?'
        
        # Şirket türü kısaltmaları
        self.company_suffixes = [
            'LTD', 'LTD.', 'LIMITED', 'LİMİTED',
            'A.Ş.', 'A.Ş', 'ANONİM', 'ANONIM',
            'SAN.', 'SAN', 'SANAYİ', 'SANAYI',
            'TİC.', 'TİC', 'TİCARET', 'TICARET',
            'INC', 'INC.', 'LLC', 'CORP'
        ]

    def extract_all_fields(self, text: str) -> Dict[str, ExtractedField]:
        """
        Metinden tüm fatura alanlarını çıkarır
        """
        results = {}
        
        # Metni temizle
        cleaned_text = self._preprocess_text(text)
        
        # Her alan için extraction
        for field_name in self.advanced_patterns.keys():
            extracted = self._extract_field_with_confidence(cleaned_text, field_name)
            if extracted:
                results[field_name] = extracted
        
        # spaCy ile NLP-based extraction (eğer model mevcutsa)
        if self.nlp:
            nlp_results = self._extract_with_nlp(cleaned_text)
            
            # NLP sonuçlarını mevcut sonuçlarla birleştir
            for field_name, nlp_result in nlp_results.items():
                if field_name not in results or nlp_result.confidence > results[field_name].confidence:
                    results[field_name] = nlp_result
        
        # Özel extraction kuralları
        special_extractions = self._apply_special_rules(cleaned_text)
        results.update(special_extractions)
        
        # Line items extraction
        line_items = self._extract_line_items(cleaned_text)
        if line_items:
            results['line_items'] = ExtractedField(
                value=line_items,
                confidence=0.8,
                source_text="Multiple lines",
                method="rule-based"
            )
        
        return results

    def _preprocess_text(self, text: str) -> str:
        """
        Metni temizle ve normalize et
        """
        # Çoklu boşlukları tek boşluk yap
        text = re.sub(r'\s+', ' ', text)
        
        # OCR hatalarını düzelt
        ocr_corrections = {
            'İ': 'I',
            'ı': 'i', 
            'O': '0',  # Rakam context'inde
            'l': '1',  # Rakam context'inde
            'S': '5',  # Rakam context'inde
        }
        
        # Yaygın Türkçe karakterleri normalize et
        text = text.replace('İ', 'I').replace('ı', 'i')
        text = text.replace('Ş', 'S').replace('ş', 's')
        text = text.replace('Ç', 'C').replace('ç', 'c')
        text = text.replace('Ğ', 'G').replace('ğ', 'g')
        text = text.replace('Ü', 'U').replace('ü', 'u')
        text = text.replace('Ö', 'O').replace('ö', 'o')
        
        return text.strip()

    def _extract_field_with_confidence(self, text: str, field_name: str) -> Optional[ExtractedField]:
        """
        Belirli bir alan için pattern matching ile confidence score
        """
        patterns = self.advanced_patterns.get(field_name, [])
        
        for i, pattern in enumerate(patterns):
            try:
                matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
                
                if matches:
                    # En güvenilir match'i seç
                    best_match = max(matches, key=lambda m: len(m.group(1)))
                    
                    # Confidence hesapla (ilk pattern daha güvenilir)
                    base_confidence = 0.9 - (i * 0.1)  # İlk pattern %90, sonrakiler daha az
                    length_bonus = min(len(best_match.group(1)) / 20, 0.1)
                    
                    confidence = min(base_confidence + length_bonus, 0.95)
                    
                    # Alan türüne göre post-processing
                    processed_value = self._post_process_field(field_name, best_match.group(1))
                    
                    if processed_value is not None:
                        return ExtractedField(
                            value=processed_value,
                            confidence=confidence,
                            source_text=best_match.group(0),
                            method="regex"
                        )
                        
            except Exception as e:
                logger.debug(f"Pattern {pattern} failed for {field_name}: {e}")
                continue
        
        return None

    def _extract_with_nlp(self, text: str) -> Dict[str, ExtractedField]:
        """
        spaCy ile NLP-based field extraction
        """
        results = {}
        
        try:
            doc = self.nlp(text)
            
            # Named Entity Recognition
            for ent in doc.ents:
                if ent.label_ == "MONEY":
                    # Para miktarlarını yakala
                    amount = self._parse_money_entity(ent.text)
                    if amount and 'total_amount' not in results:
                        results['total_amount'] = ExtractedField(
                            value=amount,
                            confidence=0.7,
                            source_text=ent.text,
                            method="nlp-ner"
                        )
                
                elif ent.label_ == "DATE":
                    # Tarihleri yakala
                    date_str = self._parse_date_entity(ent.text)
                    if date_str and 'date' not in results:
                        results['date'] = ExtractedField(
                            value=date_str,
                            confidence=0.75,
                            source_text=ent.text,
                            method="nlp-ner"
                        )
                
                elif ent.label_ in ["ORG", "PERSON"]:
                    # Organizasyon/kişi isimlerini yakala
                    if 'company_name' not in results:
                        results['company_name'] = ExtractedField(
                            value=ent.text.strip(),
                            confidence=0.6,
                            source_text=ent.text,
                            method="nlp-ner"
                        )
            
            # Token-based extraction
            tokens = [token.text for token in doc]
            
            # IBAN detection
            for i, token in enumerate(tokens):
                if token.upper().startswith('TR') and len(token) >= 24:
                    iban = self._validate_iban(token)
                    if iban:
                        results['iban'] = ExtractedField(
                            value=iban,
                            confidence=0.9,
                            source_text=token,
                            method="nlp-token"
                        )
            
        except Exception as e:
            logger.error(f"NLP extraction error: {e}")
        
        return results

    def _parse_money_entity(self, text: str) -> Optional[float]:
        """
        Para entitisini parse et
        """
        try:
            # Rakamları çıkar
            numbers = re.findall(r'[\d.,]+', text)
            if numbers:
                return self._parse_turkish_number(numbers[-1])  # Son rakamı al
        except:
            pass
        return None

    def _parse_date_entity(self, text: str) -> Optional[str]:
        """
        Tarih entitisini parse et
        """
        date_patterns = [
            r'\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}',
            r'\d{2,4}[./\-]\d{1,2}[./\-]\d{1,2}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return self._normalize_date(match.group())
        
        return None

    def _apply_special_rules(self, text: str) -> Dict[str, ExtractedField]:
        """
        Özel kuralları uygula
        """
        results = {}
        
        # Toplam tutar kuralları
        total_patterns = [
            r'(?:toplam|ödenecek).*?(\d+[.,]\d{2})',
            r'(\d+[.,]\d{2})\s*(?:TL|₺)'
        ]
        
        for pattern in total_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                amounts = [self._parse_turkish_number(m) for m in matches if self._parse_turkish_number(m)]
                if amounts:
                    # En büyük miktarı toplam olarak kabul et
                    max_amount = max(amounts)
                    results['total_amount_rule'] = ExtractedField(
                        value=max_amount,
                        confidence=0.8,
                        source_text=f"Detected from multiple amounts: {amounts}",
                        method="rule-based"
                    )
        
        return results

    def _extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """
        Fatura satır kalemlerini çıkar
        """
        items = []
        
        try:
            lines = text.split('\n')
            
            # Tablo formatını algıla
            table_patterns = [
                # Miktar Açıklama BirimFiyat Tutar
                r'(\d+(?:[.,]\d+)?)\s+([A-Za-zçğıiöşü\s\-\.]+?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)',
                # Açıklama Miktar BirimFiyat Tutar
                r'([A-Za-zçğıiöşü\s\-\.]+?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)',
                # Daha esnek pattern
                r'(.+?)\s+(\d+[.,]?\d*)\s+(\d+[.,]?\d*)\s+(\d+[.,]?\d*)\s*(?:TL|₺)?'
            ]
            
            for line in lines:
                line = line.strip()
                if len(line) < 10:  # Çok kısa satırları atla
                    continue
                
                for pattern in table_patterns:
                    match = re.search(pattern, line)
                    if match:
                        try:
                            groups = match.groups()
                            
                            # Pattern türüne göre parse et
                            if len(groups) == 4:
                                desc, qty, price, total = groups
                                
                                # Sayıları parse et
                                quantity = self._parse_turkish_number(qty)
                                unit_price = self._parse_turkish_number(price)
                                line_total = self._parse_turkish_number(total)
                                
                                if quantity and unit_price and line_total:
                                    items.append({
                                        'description': desc.strip(),
                                        'quantity': quantity,
                                        'unit_price': unit_price,
                                        'total': line_total,
                                        'unit': 'adet'  # Default
                                    })
                                    break
                                    
                        except Exception as e:
                            logger.debug(f"Line item parsing error: {e}")
                            continue
            
        except Exception as e:
            logger.error(f"Line items extraction error: {e}")
        
        return items

    def _post_process_field(self, field_name: str, value: str) -> Any:
        """
        Alan türüne göre post-processing
        """
        if field_name in ['total_amount', 'vat_amount', 'net_amount']:
            return self._parse_turkish_number(value)
        
        elif field_name in ['date', 'due_date']:
            return self._normalize_date(value)
        
        elif field_name == 'tax_number':
            return re.sub(r'\D', '', value)  # Sadece rakamlar
        
        elif field_name == 'company_name':
            return self._clean_company_name(value)
        
        elif field_name == 'vat_rate':
            rate = re.sub(r'[^\d]', '', value)
            return int(rate) if rate.isdigit() else None
        
        elif field_name == 'iban':
            return self._validate_iban(value)
        
        elif field_name == 'currency':
            currency_map = {'₺': 'TRY', 'TL': 'TRY'}
            return currency_map.get(value.upper(), value.upper())
        
        return value.strip()

    def _parse_turkish_number(self, number_str: str) -> Optional[float]:
        """
        Türk formatındaki sayıyı parse et: 1.234,56 -> 1234.56
        """
        try:
            if not number_str:
                return None
            
            # Temizle
            cleaned = str(number_str).strip()
            
            # Türk formatını algıla: 1.234,56
            if re.match(r'^\d{1,3}(?:\.\d{3})*,\d{2}$', cleaned):
                # Noktaları kaldır, virgülü noktaya çevir
                cleaned = cleaned.replace('.', '').replace(',', '.')
            
            # Diğer karakterleri temizle
            cleaned = re.sub(r'[^\d.,]', '', cleaned)
            
            # Son kontrol
            if ',' in cleaned and '.' in cleaned:
                # Hangisi decimal separator?
                if cleaned.rindex(',') > cleaned.rindex('.'):
                    # Virgül decimal
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                else:
                    # Nokta decimal
                    parts = cleaned.split('.')
                    if len(parts) > 2:  # 1.234.56 formatı
                        cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
            
            elif ',' in cleaned:
                # Sadece virgül var - decimal olabilir
                if len(cleaned.split(',')[-1]) <= 2:
                    cleaned = cleaned.replace(',', '.')
            
            return float(cleaned) if cleaned else None
            
        except Exception as e:
            logger.debug(f"Number parsing error for '{number_str}': {e}")
            return None

    def _normalize_date(self, date_str: str) -> Optional[str]:
        """
        Tarih formatını normalize et
        """
        try:
            # Yaygın Türk tarih formatları
            formats = [
                '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y',
                '%d.%m.%y', '%d/%m/%y', '%d-%m-%y',
                '%Y-%m-%d', '%Y.%m.%d', '%Y/%m/%d'
            ]
            
            cleaned_date = date_str.strip()
            
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(cleaned_date, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Date parsing error for '{date_str}': {e}")
            return None

    def _clean_company_name(self, name: str) -> str:
        """
        Şirket adını temizle
        """
        cleaned = name.strip()
        
        # Şirket türü kısaltmalarını kaldır
        for suffix in self.company_suffixes:
            if cleaned.upper().endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
                break
        
        return cleaned

    def _validate_iban(self, iban: str) -> Optional[str]:
        """
        IBAN formatını doğrula
        """
        try:
            # Temizle
            iban = re.sub(r'\s', '', iban.upper())
            
            # Türk IBAN formatı: TR + 24 rakam
            if re.match(r'^TR\d{24}$', iban):
                return iban
            
            return None
            
        except:
            return None

# Global extractor instance
field_extractor = AdvancedFieldExtractor()