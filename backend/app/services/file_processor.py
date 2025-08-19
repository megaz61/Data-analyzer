# app/services/file_processor.py
# ---------------------------------------------------------
# Tugas file ini:
# - Deteksi tipe file & pengambilan metadata dasar
# - Membaca CSV/Excel/PDF menjadi objek Python
# - Memanggil DataAnalyzer untuk semua ANALISIS + CHART
# - Mengembalikan struktur hasil SAMA seperti versi lama
# ---------------------------------------------------------

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

import pandas as pd
import numpy as np
import PyPDF2
from dotenv import load_dotenv
import google.generativeai as genai

from app.services.data_analyzer import DataAnalyzer

load_dotenv()

# app/services/file_processor.py
# ...
class EnhancedFileProcessor:
    def __init__(self):
        # ...
        self.gemini_model = None
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel(os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash"))
                print("✅ Gemini model 'gemini-1.5-flash' initialized successfully for PDF summarization.")
            except Exception as e:
                print(f"❌ Gemini model initialization failed: {e}")
                self.gemini_model = None
        else:
            print("⚠️ GEMINI_API_KEY not found. PDF summarization feature will be unavailable.")
    # ------------------- DETEKSI TIPE FILE -------------------

    def detect_file_type(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        ext = os.path.splitext(original_filename)[1].lower()
        size = os.path.getsize(file_path)
        info = {
            'extension': ext,
            'size_bytes': size,
            'size_mb': round(size / (1024 * 1024), 2),
            'filename': original_filename,
            'is_supported': ext in self.supported_formats
        }

        if ext == '.csv':
            info.update(self._detect_csv_details(file_path))
        elif ext in ['.xlsx', '.xls']:
            info.update(self._detect_excel_details(file_path))
        elif ext == '.pdf':
            info.update(self._detect_pdf_details(file_path))

        return info

    def _detect_csv_details(self, file_path: str) -> Dict[str, Any]:
        details = {'type': 'csv'}
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    first_lines = [f.readline().strip() for _ in range(3)]
                first_line = first_lines[0] if first_lines else ""
                delimiters = [',', ';', '\t', '|']
                counts = {d: first_line.count(d) for d in delimiters}
                delim = max(counts, key=counts.get)
                details.update({
                    'encoding': enc,
                    'delimiter': delim,
                    'estimated_columns': counts[delim] + 1,
                    'sample_lines': first_lines
                })
                break
            except Exception:
                continue
        return details

    def _detect_excel_details(self, file_path: str) -> Dict[str, Any]:
        details = {'type': 'excel'}
        try:
            xls = pd.ExcelFile(file_path)
            details.update({
                'sheet_count': len(xls.sheet_names),
                'sheet_names': xls.sheet_names,
                'engine': 'openpyxl' if file_path.endswith('.xlsx') else 'xlrd'
            })
            if xls.sheet_names:
                first = xls.sheet_names[0]
                df_sample = pd.read_excel(file_path, sheet_name=first, nrows=5)
                details.update({
                    'sample_columns': df_sample.columns.tolist(),
                    'estimated_rows': len(pd.read_excel(file_path, sheet_name=first))
                })
        except Exception as e:
            details['error'] = str(e)
        return details

    def _detect_pdf_details(self, file_path: str) -> Dict[str, Any]:
        details = {'type': 'pdf'}
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                details.update({
                    'page_count': len(reader.pages),
                    'is_encrypted': reader.is_encrypted,
                    'metadata': {}
                })
                if reader.metadata:
                    meta = {}
                    for k, v in reader.metadata.items():
                        if v:
                            meta[k.replace('/', '').lower()] = str(v)
                    details['metadata'] = meta
                if len(reader.pages) > 0:
                    text = reader.pages[0].extract_text()
                    details.update({
                        'first_page_chars': len(text or ""),
                        'estimated_extractable': bool((text or "").strip()),
                        'sample_text': (text or "")[:200]
                    })
        except Exception as e:
            details['error'] = str(e)
        return details

    # ------------------- PROSES FILE (EKSTRAK + ANALISIS) -------------------

    def process_file(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        detection = self.detect_file_type(file_path, original_filename)
        if not detection['is_supported']:
            raise ValueError(f"Unsupported file format: {detection['extension']}. Supported: {', '.join(self.supported_formats)}")

        file_id = str(uuid.uuid4())
        ext = detection['extension']

        base = {
            'file_id': file_id,
            'filename': original_filename,
            'file_detection': detection,
            'processed_at': datetime.now().isoformat()
        }

        if ext == '.csv':
            result = self._process_csv(file_path, detection)
        elif ext in ['.xlsx', '.xls']:
            result = self._process_excel(file_path, detection)
        elif ext == '.pdf':
            result = self._process_pdf(file_path, detection)
        else:
            result = {}

        result.update(base)
        return result

    def _process_csv(self, file_path: str, detection: Dict[str, Any]) -> Dict[str, Any]:
        try:
            enc = detection.get('encoding', 'utf-8')
            delim = detection.get('delimiter', ',')
            df = pd.read_csv(file_path, encoding=enc, delimiter=delim)

            analysis = self.analyzer.analyze_dataframe(df)

            return {
                'type': 'csv',
                'data': df.to_dict('records')[:100],   # tetap: 100 baris pertama
                'analysis_summary': analysis,
                'full_data': df.to_json(),
                'processing_info': {
                    'encoding_used': enc,
                    'delimiter_used': delim,
                    'total_rows_processed': len(df)
                }
            }
        except Exception as e:
            raise Exception(f"Error processing CSV: {str(e)}")

    def _process_excel(self, file_path: str, detection: Dict[str, Any]) -> Dict[str, Any]:
        try:
            sheets_data, excel_summary = self.analyzer.analyze_excel_workbook(file_path)
            excel_summary['file_size_mb'] = detection.get('size_mb', 0)  # agar sama seperti versi lama
            return {
                'type': 'excel',
                'sheets': list(sheets_data.keys()),
                'data': sheets_data,
                'analysis_summary': excel_summary
            }
        except Exception as e:
            raise Exception(f"Error processing Excel: {str(e)}")

    def _process_pdf(self, file_path: str, detection: Dict[str, Any]) -> Dict[str, Any]:
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                full_text = ""
                page_texts: List[Dict[str, Any]] = []

                for i, page in enumerate(reader.pages):
                    try:
                        txt = page.extract_text() or ""
                        page_texts.append({
                            'page_number': i + 1,
                            'text': txt,
                            'char_count': len(txt),
                            'word_count': len(txt.split()) if txt else 0
                        })
                        full_text += (txt + "\n")
                    except Exception as e:
                        page_texts.append({'page_number': i + 1, 'error': str(e), 'char_count': 0, 'word_count': 0})

                analysis_summary = self.analyzer.analyze_pdf(
                    full_text=full_text,
                    page_texts=page_texts,
                    metadata=detection.get('metadata', {}),
                    gemini_model=self.gemini_model
                )

                return {
                    'type': 'pdf',
                    'text': full_text,
                    'page_texts': page_texts,
                    'analysis_summary': analysis_summary
                }
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
