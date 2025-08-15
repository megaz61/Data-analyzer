import pandas as pd
import numpy as np
import PyPDF2
import docx
import json
import os
from typing import Dict, Any, List, Optional, Tuple
import uuid
import re
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import time

load_dotenv()

class EnhancedFileProcessor:
    def __init__(self):
        # Remove txt support, only support csv, xlsx, xls, pdf
        self.supported_formats = ['.csv', '.xlsx', '.xls', '.pdf']
        
        # Initialize Gemini for PDF summarization
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_model = None
    
    def detect_file_type(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """Enhanced file type detection with detailed information"""
        file_extension = os.path.splitext(original_filename)[1].lower()
        file_size = os.path.getsize(file_path)
        
        # Basic file info
        file_info = {
            'extension': file_extension,
            'size_bytes': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'filename': original_filename,
            'is_supported': file_extension in self.supported_formats
        }
        
        # Detailed type detection
        if file_extension == '.csv':
            file_info.update(self._detect_csv_details(file_path))
        elif file_extension in ['.xlsx', '.xls']:
            file_info.update(self._detect_excel_details(file_path))
        elif file_extension == '.pdf':
            file_info.update(self._detect_pdf_details(file_path))
        
        return file_info
    
    def _detect_csv_details(self, file_path: str) -> Dict[str, Any]:
        """Detect CSV file details and encoding"""
        details = {'type': 'csv'}
        
        # Try different encodings to detect the best one
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                # Read first few lines to detect structure
                with open(file_path, 'r', encoding=encoding) as f:
                    first_lines = [f.readline().strip() for _ in range(3)]
                
                # Detect delimiter
                first_line = first_lines[0] if first_lines else ""
                delimiters = [',', ';', '\t', '|']
                delimiter_counts = {delim: first_line.count(delim) for delim in delimiters}
                detected_delimiter = max(delimiter_counts, key=delimiter_counts.get)
                
                details.update({
                    'encoding': encoding,
                    'delimiter': detected_delimiter,
                    'estimated_columns': delimiter_counts[detected_delimiter] + 1,
                    'sample_lines': first_lines
                })
                break
                
            except Exception:
                continue
        
        return details
    
    def _detect_excel_details(self, file_path: str) -> Dict[str, Any]:
        """Detect Excel file details"""
        details = {'type': 'excel'}
        
        try:
            excel_file = pd.ExcelFile(file_path)
            details.update({
                'sheet_count': len(excel_file.sheet_names),
                'sheet_names': excel_file.sheet_names,
                'engine': 'openpyxl' if file_path.endswith('.xlsx') else 'xlrd'
            })
            
            # Get info about first sheet
            if excel_file.sheet_names:
                first_sheet = excel_file.sheet_names[0]
                df_sample = pd.read_excel(file_path, sheet_name=first_sheet, nrows=5)
                details.update({
                    'sample_columns': df_sample.columns.tolist(),
                    'estimated_rows': len(pd.read_excel(file_path, sheet_name=first_sheet))
                })
                
        except Exception as e:
            details['error'] = str(e)
        
        return details
    
    def _detect_pdf_details(self, file_path: str) -> Dict[str, Any]:
        """Detect PDF file details"""
        details = {'type': 'pdf'}
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Basic PDF info
                details.update({
                    'page_count': len(pdf_reader.pages),
                    'is_encrypted': pdf_reader.is_encrypted,
                    'metadata': {}
                })
                
                # Extract metadata if available
                if pdf_reader.metadata:
                    metadata = {}
                    for key, value in pdf_reader.metadata.items():
                        if value:
                            clean_key = key.replace('/', '').lower()
                            metadata[clean_key] = str(value)
                    details['metadata'] = metadata
                
                # Sample first page text to estimate content
                if len(pdf_reader.pages) > 0:
                    first_page_text = pdf_reader.pages[0].extract_text()
                    details.update({
                        'first_page_chars': len(first_page_text),
                        'estimated_extractable': bool(first_page_text.strip()),
                        'sample_text': first_page_text[:200] if first_page_text else ""
                    })
                    
        except Exception as e:
            details['error'] = str(e)
        
        return details
    
    def process_file(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """Enhanced file processing with improved type detection"""
        # First detect file type and details
        file_detection = self.detect_file_type(file_path, original_filename)
        
        if not file_detection['is_supported']:
            raise ValueError(f"Unsupported file format: {file_detection['extension']}. Supported formats: {', '.join(self.supported_formats)}")
        
        file_id = str(uuid.uuid4())
        file_extension = file_detection['extension']
        
        try:
            base_result = {
                'file_id': file_id,
                'filename': original_filename,
                'file_detection': file_detection,
                'processed_at': datetime.now().isoformat()
            }
            
            if file_extension == '.csv':
                result = self._process_enhanced_csv(file_path, file_id, original_filename, file_detection)
            elif file_extension in ['.xlsx', '.xls']:
                result = self._process_enhanced_excel(file_path, file_id, original_filename, file_detection)
            elif file_extension == '.pdf':
                result = self._process_enhanced_pdf(file_path, file_id, original_filename, file_detection)
            
            result.update(base_result)
            return result
            
        except Exception as e:
            raise Exception(f"Error processing file: {str(e)}")
    
    def _detect_column_types(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Enhanced column type detection with detailed analysis"""
        column_types = {}
        
        for column in df.columns:
            col_data = df[column].dropna()
            if len(col_data) == 0:
                column_types[column] = {
                    'detected_type': 'empty',
                    'pandas_dtype': str(df[column].dtype),
                    'null_percentage': 100.0,
                    'sample_values': []
                }
                continue
            
            # Calculate null percentage
            null_percentage = (df[column].isnull().sum() / len(df)) * 100
            
            # Get sample values (non-null)
            sample_values = col_data.head(5).tolist()
            
            # Detect type
            detected_type = self._analyze_column_content(col_data)
            
            column_types[column] = {
                'detected_type': detected_type['type'],
                'confidence': detected_type['confidence'],
                'pandas_dtype': str(df[column].dtype),
                'null_percentage': round(null_percentage, 2),
                'unique_count': col_data.nunique(),
                'sample_values': sample_values,
                'additional_info': detected_type.get('additional_info', {})
            }
        
        return column_types
    
    def _analyze_column_content(self, col_data: pd.Series) -> Dict[str, Any]:
        """Analyze column content to determine the most appropriate data type"""
        sample_values = col_data.head(20).astype(str).tolist()
        
        # Patterns for different data types
        patterns = {
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'phone': re.compile(r'^[\+]?[1-9][\d]{0,15}$'),
            'url': re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE),
            'date_iso': re.compile(r'^\d{4}-\d{2}-\d{2}'),
            'date_us': re.compile(r'^\d{1,2}/\d{1,2}/\d{2,4}$'),
            'date_eu': re.compile(r'^\d{1,2}\.\d{1,2}\.\d{2,4}$'),
            'time': re.compile(r'^\d{1,2}:\d{2}(:\d{2})?'),
            'currency': re.compile(r'^[\$€£¥₹]?\d+([,.]\d{2})?$'),
            'percentage': re.compile(r'^\d+(\.\d+)?%$'),
            'ip_address': re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        }
        
        # Test for special patterns first
        for pattern_name, pattern in patterns.items():
            matches = sum(1 for val in sample_values if pattern.match(str(val).strip()))
            if matches / len(sample_values) > 0.7:  # 70% confidence
                return {
                    'type': pattern_name,
                    'confidence': (matches / len(sample_values)) * 100,
                    'additional_info': {'pattern_matches': matches, 'total_samples': len(sample_values)}
                }
        
        # Try numeric conversion
        try:
            numeric_data = pd.to_numeric(col_data, errors='coerce')
            non_null_numeric = numeric_data.dropna()
            
            if len(non_null_numeric) / len(col_data) > 0.8:  # 80% are numeric
                # Determine if integer or float
                is_integer = all(x.is_integer() for x in non_null_numeric if pd.notna(x))
                
                return {
                    'type': 'integer' if is_integer else 'float',
                    'confidence': (len(non_null_numeric) / len(col_data)) * 100,
                    'additional_info': {
                        'min_value': float(non_null_numeric.min()),
                        'max_value': float(non_null_numeric.max()),
                        'mean_value': float(non_null_numeric.mean())
                    }
                }
        except:
            pass
        
        # Try datetime conversion
        try:
            datetime_data = pd.to_datetime(col_data, errors='coerce', infer_datetime_format=True)
            non_null_datetime = datetime_data.dropna()
            
            if len(non_null_datetime) / len(col_data) > 0.7:  # 70% are datetime
                return {
                    'type': 'datetime',
                    'confidence': (len(non_null_datetime) / len(col_data)) * 100,
                    'additional_info': {
                        'earliest_date': str(non_null_datetime.min()),
                        'latest_date': str(non_null_datetime.max())
                    }
                }
        except:
            pass
        
        # Check for boolean-like data
        unique_values = set(str(val).lower().strip() for val in col_data.unique())
        boolean_sets = [
            {'true', 'false'},
            {'yes', 'no'},
            {'y', 'n'},
            {'1', '0'},
            {'on', 'off'},
            {'active', 'inactive'}
        ]
        
        for bool_set in boolean_sets:
            if unique_values.issubset(bool_set):
                return {
                    'type': 'boolean',
                    'confidence': 95.0,
                    'additional_info': {'boolean_values': list(unique_values)}
                }
        
        # Check if categorical (limited unique values)
        unique_count = col_data.nunique()
        total_count = len(col_data)
        
        if unique_count <= 20 and unique_count / total_count < 0.5:
            return {
                'type': 'categorical',
                'confidence': 80.0,
                'additional_info': {
                    'categories': col_data.value_counts().head(10).to_dict(),
                    'category_count': unique_count
                }
            }
        
        # Default to text
        return {
            'type': 'text',
            'confidence': 60.0,
            'additional_info': {
                'avg_length': col_data.astype(str).str.len().mean(),
                'max_length': col_data.astype(str).str.len().max()
            }
        }
    
    def _intelligent_chart_selection(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """AI-powered intelligent chart selection based on data characteristics"""
        charts = {}
        columns = df.columns.tolist()
        
        # Get column types for intelligent analysis
        column_types = self._detect_column_types(df)
        
        # Separate different types of columns
        numeric_cols = [col for col, info in column_types.items() 
                       if info['detected_type'] in ['integer', 'float']]
        categorical_cols = [col for col, info in column_types.items() 
                           if info['detected_type'] in ['categorical', 'text'] and info['unique_count'] <= 20]
        datetime_cols = [col for col, info in column_types.items() 
                        if info['detected_type'] == 'datetime']
        
        # 1. Time Series Detection (Line Chart)
        if datetime_cols and numeric_cols:
            for date_col in datetime_cols[:1]:  # Use first datetime column
                for num_col in numeric_cols[:2]:  # Use first 2 numeric columns
                    try:
                        df_time = df[[date_col, num_col]].dropna()
                        if len(df_time) > 5:
                            # Sort by date and aggregate if needed
                            df_time[date_col] = pd.to_datetime(df_time[date_col], errors='coerce')
                            df_time = df_time.sort_values(date_col)
                            
                            # Group by date if too many points
                            if len(df_time) > 50:
                                df_time = df_time.groupby(df_time[date_col].dt.date)[num_col].sum().reset_index()
                            
                            charts[f"trend_{num_col}_over_time"] = {
                                'type': 'line',
                                'title': f'Tren {num_col} dari Waktu ke Waktu',
                                'x_data': [str(x) for x in df_time[date_col].head(20).tolist()],
                                'y_data': df_time[num_col].head(20).tolist(),
                                'x_label': date_col,
                                'y_label': num_col,
                                'chart_purpose': 'time_series'
                            }
                    except Exception:
                        continue
        
        # 2. Top Categories Analysis (Horizontal Bar Chart)
        for col in categorical_cols[:3]:  # Analyze top 3 categorical columns
            try:
                value_counts = df[col].value_counts().head(10)
                if len(value_counts) > 1:
                    # Determine if this could be related to sales/performance
                    col_lower = col.lower()
                    if any(keyword in col_lower for keyword in ['produk', 'product', 'kategori', 'category', 'brand', 'nama']):
                        chart_title = f'Top {col} Berdasarkan Frekuensi'
                        if numeric_cols:
                            # If there's a numeric column that could represent sales/revenue
                            sales_col = None
                            for num_col in numeric_cols:
                                num_col_lower = num_col.lower()
                                if any(keyword in num_col_lower for keyword in ['total', 'harga', 'price', 'sales', 'revenue', 'penjualan']):
                                    sales_col = num_col
                                    break
                            
                            if sales_col:
                                # Group by category and sum the sales
                                sales_by_category = df.groupby(col)[sales_col].sum().sort_values(ascending=False).head(10)
                                charts[f"top_{col}_by_{sales_col}"] = {
                                    'type': 'horizontal_bar',
                                    'title': f'Top {col} Berdasarkan {sales_col}',
                                    'x_data': sales_by_category.values.tolist(),
                                    'y_data': sales_by_category.index.tolist(),
                                    'x_label': sales_col,
                                    'y_label': col,
                                    'chart_purpose': 'ranking'
                                }
                                continue
                    
                    # Default frequency chart
                    charts[f"frequency_{col}"] = {
                        'type': 'horizontal_bar',
                        'title': f'Distribusi {col}',
                        'x_data': value_counts.values.tolist(),
                        'y_data': value_counts.index.tolist(),
                        'x_label': 'Jumlah',
                        'y_label': col,
                        'chart_purpose': 'distribution'
                    }
            except Exception:
                continue
        
        # 3. Numeric Distribution Analysis (Histogram or Box Plot)
        for col in numeric_cols[:3]:  # Analyze top 3 numeric columns
            try:
                col_data = df[col].dropna()
                if len(col_data) > 10:
                    # Check if data is suitable for histogram
                    if col_data.nunique() > 5:  # Good spread for histogram
                        # Calculate optimal bins
                        q75, q25 = np.percentile(col_data, [75, 25])
                        iqr = q75 - q25
                        if iqr > 0:
                            bin_width = 2 * iqr / (len(col_data) ** (1/3))
                            bins = max(min(int(np.ceil((col_data.max() - col_data.min()) / bin_width)), 20), 5)
                        else:
                            bins = 10
                        
                        counts, bin_edges = np.histogram(col_data, bins=bins)
                        bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges)-1)]
                        
                        charts[f"distribution_{col}"] = {
                            'type': 'histogram',
                            'title': f'Distribusi {col}',
                            'bins': bin_edges.tolist(),
                            'counts': counts.tolist(),
                            'bin_centers': bin_centers,
                            'x_label': col,
                            'y_label': 'Frekuensi',
                            'stats': {
                                'mean': float(col_data.mean()),
                                'median': float(col_data.median()),
                                'std': float(col_data.std())
                            },
                            'chart_purpose': 'distribution'
                        }
            except Exception:
                continue
        
        # 4. Correlation Analysis (Scatter Plot)
        if len(numeric_cols) >= 2:
            for i, col1 in enumerate(numeric_cols[:2]):
                for col2 in numeric_cols[i+1:3]:  # Avoid duplicate pairs
                    try:
                        df_corr = df[[col1, col2]].dropna()
                        if len(df_corr) > 10:
                            # Calculate correlation
                            correlation = df_corr[col1].corr(df_corr[col2])
                            if abs(correlation) > 0.3:  # Only show if there's some correlation
                                # Sample data if too many points
                                if len(df_corr) > 100:
                                    df_corr = df_corr.sample(100)
                                
                                charts[f"correlation_{col1}_vs_{col2}"] = {
                                    'type': 'scatter',
                                    'title': f'Korelasi {col1} vs {col2}',
                                    'x_data': df_corr[col1].tolist(),
                                    'y_data': df_corr[col2].tolist(),
                                    'x_label': col1,
                                    'y_label': col2,
                                    'correlation': round(correlation, 3),
                                    'chart_purpose': 'correlation'
                                }
                                break  # Only one correlation chart per column
                    except Exception:
                        continue
        
        # 5. Pie Chart for Categorical Distribution (when appropriate)
        for col in categorical_cols[:2]:  # Max 2 pie charts
            try:
                value_counts = df[col].value_counts()
                if 3 <= len(value_counts) <= 8:  # Pie charts work best with 3-8 categories
                    # Only show pie chart if no single category dominates too much
                    if (value_counts.iloc[0] / value_counts.sum()) < 0.7:
                        charts[f"pie_{col}"] = {
                            'type': 'pie',
                            'title': f'Proporsi {col}',
                            'labels': value_counts.index.tolist(),
                            'data': value_counts.values.tolist(),
                            'chart_purpose': 'proportion'
                        }
            except Exception:
                continue
        
        # 6. Area Chart for Cumulative Analysis
        if datetime_cols and numeric_cols:
            for date_col in datetime_cols[:1]:
                for num_col in numeric_cols[:1]:
                    try:
                        df_area = df[[date_col, num_col]].dropna()
                        if len(df_area) > 10:
                            df_area[date_col] = pd.to_datetime(df_area[date_col], errors='coerce')
                            df_area = df_area.sort_values(date_col)
                            
                            # Calculate cumulative sum
                            df_area['cumulative'] = df_area[num_col].cumsum()
                            
                            if len(df_area) > 50:
                                df_area = df_area.iloc[::len(df_area)//50]  # Sample every nth row
                            
                            charts[f"cumulative_{num_col}"] = {
                                'type': 'area',
                                'title': f'Akumulasi {num_col} dari Waktu ke Waktu',
                                'x_data': [str(x) for x in df_area[date_col].tolist()],
                                'y_data': df_area['cumulative'].tolist(),
                                'x_label': date_col,
                                'y_label': f'Kumulatif {num_col}',
                                'chart_purpose': 'cumulative'
                            }
                            break
                    except Exception:
                        continue
        
        return charts
    
    def _process_enhanced_csv(self, file_path: str, file_id: str, filename: str, file_detection: Dict) -> Dict[str, Any]:
        """Enhanced CSV processing with intelligent chart generation"""
        try:
            # Use detected encoding and delimiter
            encoding = file_detection.get('encoding', 'utf-8')
            delimiter = file_detection.get('delimiter', ',')
            
            df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
            
            # Enhanced analysis with column type detection
            analysis = self._analyze_dataframe_enhanced(df)
            
            # Add column type detection
            column_types = self._detect_column_types(df)
            analysis['column_types'] = column_types
            
            # Data quality assessment
            analysis['data_quality'] = self._assess_data_quality(df)
            
            # Intelligent chart generation
            intelligent_charts = self._intelligent_chart_selection(df)
            analysis['intelligent_charts'] = intelligent_charts
            
            return {
                'type': 'csv',
                'data': df.to_dict('records')[:100],  # First 100 rows
                'analysis_summary': analysis,
                'full_data': df.to_json(),
                'processing_info': {
                    'encoding_used': encoding,
                    'delimiter_used': delimiter,
                    'total_rows_processed': len(df)
                }
            }
        except Exception as e:
            raise Exception(f"Error processing CSV: {str(e)}")
    
    def _process_enhanced_excel(self, file_path: str, file_id: str, filename: str, file_detection: Dict) -> Dict[str, Any]:
        """Enhanced Excel processing with intelligent chart generation for each sheet"""
        try:
            excel_file = pd.ExcelFile(file_path)
            sheets_data = {}
            
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Enhanced analysis for each sheet
                    analysis = self._analyze_dataframe_enhanced(df)
                    column_types = self._detect_column_types(df)
                    analysis['column_types'] = column_types
                    analysis['data_quality'] = self._assess_data_quality(df)
                    
                    # Intelligent chart generation for each sheet
                    intelligent_charts = self._intelligent_chart_selection(df)
                    analysis['intelligent_charts'] = intelligent_charts
                    
                    sheets_data[sheet_name] = {
                        'data': df.to_dict('records')[:50],  # 50 rows per sheet
                        'analysis': analysis
                    }
                except Exception as e:
                    sheets_data[sheet_name] = {
                        'data': [],
                        'analysis': {'error': str(e)}
                    }
            
            return {
                'type': 'excel',
                'sheets': list(sheets_data.keys()),
                'data': sheets_data,
                'analysis_summary': self._analyze_excel_file_enhanced(sheets_data, file_detection)
            }
        except Exception as e:
            raise Exception(f"Error processing Excel: {str(e)}")
    
    def _process_enhanced_pdf(self, file_path: str, file_id: str, filename: str, file_detection: Dict) -> Dict[str, Any]:
        """Enhanced PDF processing with detailed statistics and summarization"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                full_text = ""
                page_texts = []
                
                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        page_texts.append({
                            'page_number': page_num + 1,
                            'text': page_text,
                            'char_count': len(page_text),
                            'word_count': len(page_text.split()) if page_text else 0
                        })
                        full_text += page_text + "\n"
                    except Exception as e:
                        page_texts.append({
                            'page_number': page_num + 1,
                            'error': str(e),
                            'char_count': 0,
                            'word_count': 0
                        })
                
                # Enhanced document statistics
                doc_stats = self._calculate_pdf_statistics(full_text, page_texts)
                
                # Generate summary using Gemini if available
                summary = self._generate_pdf_summary(full_text) if full_text.strip() else "No text content found"
                
                return {
                    'type': 'pdf',
                    'text': full_text,
                    'page_texts': page_texts,
                    'analysis_summary': {
                        **doc_stats,
                        'ai_summary': summary,
                        'metadata': file_detection.get('metadata', {}),
                        'extraction_info': {
                            'total_pages_processed': len(page_texts),
                            'pages_with_text': sum(1 for p in page_texts if p.get('word_count', 0) > 0),
                            'extraction_success_rate': (sum(1 for p in page_texts if 'error' not in p) / len(page_texts) * 100) if page_texts else 0
                        }
                    }
                }
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def _calculate_pdf_statistics(self, full_text: str, page_texts: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive PDF statistics"""
        if not full_text.strip():
            return {
                'pages': len(page_texts),
                'word_count': 0,
                'char_count': 0,
                'paragraph_count': 0,
                'sentence_count': 0,
                'average_words_per_page': 0
            }
        
        # Basic counts
        words = full_text.split()
        paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]
        sentences = re.split(r'[.!?]+', full_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Page-level statistics
        pages_with_content = [p for p in page_texts if p.get('word_count', 0) > 0]
        avg_words_per_page = sum(p['word_count'] for p in pages_with_content) / len(pages_with_content) if pages_with_content else 0
        
        # Content analysis
        lines = full_text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        #Hitung durasi proses
        start_time = time.time()
        end_time = time.time()
        processing_time_seconds = end_time - start_time

        
        return {
            'pages': len(page_texts),
            'word_count': len(words),
            'char_count': len(full_text),
            'char_count_no_spaces': len(full_text.replace(' ', '')),
            'paragraph_count': len(paragraphs),
            'sentence_count': len(sentences),
            'line_count': len(lines),
            'non_empty_lines': len(non_empty_lines),
            'average_words_per_page': round(avg_words_per_page, 2),
            'average_chars_per_page': round(len(full_text) / len(page_texts), 2) if page_texts else 0,
            'longest_paragraph': max(len(p) for p in paragraphs) if paragraphs else 0,
            'average_paragraph_length': round(sum(len(p) for p in paragraphs) / len(paragraphs), 2) if paragraphs else 0,
            'reading_time_minutes': round(len(words) / 300, 1), # Assuming people read 300 words per minute
            'processing_time_seconds': f'{processing_time_seconds:.4f}',# Assuming 200 words per minute
        }
    
    def _generate_pdf_summary(self, text: str) -> str:
        """Generate AI summary of PDF content using Gemini"""
        if not self.gemini_model or not text.strip():
            return "Summary not available"
        
        try:
            # Limit text for summarization (first 4000 characters)
            text_for_summary = text[:4000] if len(text) > 4000 else text
            
            prompt = f"""Silakan buat ringkasan komprehensif dari dokumen berikut dalam bahasa Indonesia. 
Berikan ringkasan yang mencakup:
1. Topik utama dokumen
2. Poin-poin kunci
3. Kesimpulan atau temuan penting

Dokumen:
{text_for_summary}

Ringkasan:"""
            
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=500
                )
            )
            
            return response.text.strip() if response.text else "Tidak dapat menghasilkan ringkasan"
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def _analyze_dataframe_enhanced(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Enhanced DataFrame analysis with charts and insights"""
        try:
            analysis = {
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'dtypes': {str(k): str(v) for k, v in df.dtypes.to_dict().items()},
                'null_counts': df.isnull().sum().to_dict(),
                'null_percentages': (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
                'summary_stats': {},
                'charts': {}
            }
            
            # Separate numeric and categorical columns
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_columns = [col for col in df.columns if col not in numeric_columns]
            
            # Summary statistics for numeric columns
            if numeric_columns:
                stats_df = df[numeric_columns].describe()
                analysis['summary_stats'] = {
                    str(col): {str(stat): round(val, 4) if isinstance(val, (int, float)) else val 
                              for stat, val in stats_df[col].items()}
                    for col in stats_df.columns
                }
            
            # Keep legacy chart format for backward compatibility
            # Generate chart data for numeric columns (histograms)
            for col in numeric_columns[:5]:  # Limit to 5 columns
                try:
                    col_data = df[col].dropna()
                    if len(col_data) > 0:
                        # Calculate optimal bin count using Freedman-Diaconis rule
                        q75, q25 = np.percentile(col_data, [75, 25])
                        iqr = q75 - q25
                        if iqr > 0:
                            bin_width = 2 * iqr / (len(col_data) ** (1/3))
                            bins = max(min(int(np.ceil((col_data.max() - col_data.min()) / bin_width)), 30), 5)
                        else:
                            bins = 10
                        
                        counts, bin_edges = np.histogram(col_data, bins=bins)
                        analysis['charts'][col] = {
                            'type': 'histogram',
                            'bins': bin_edges.tolist(),
                            'counts': counts.tolist(),
                            'stats': {
                                'mean': float(col_data.mean()),
                                'median': float(col_data.median()),
                                'std': float(col_data.std())
                            }
                        }
                except Exception:
                    continue
            
            # Generate chart data for categorical columns (bar charts)
            for col in categorical_columns[:5]:  # Limit to 5 columns
                try:
                    value_counts = df[col].value_counts().head(10)
                    if not value_counts.empty:
                        analysis['charts'][col] = {
                            'type': 'bar',
                            'categories': value_counts.index.astype(str).tolist(),
                            'counts': value_counts.tolist(),
                            'total_unique': df[col].nunique(),
                            'top_category_percentage': round((value_counts.iloc[0] / len(df)) * 100, 2)
                        }
                except Exception:
                    continue
            
            return analysis
            
        except Exception as e:
            return {
                'shape': df.shape if df is not None else [0, 0],
                'columns': [],
                'error': str(e)
            }
    
    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data quality metrics"""
        total_cells = df.shape[0] * df.shape[1]
        null_cells = df.isnull().sum().sum()
        
        # Duplicate rows
        duplicate_rows = df.duplicated().sum()
        
        # Columns with high null percentage
        high_null_cols = []
        for col in df.columns:
            null_pct = (df[col].isnull().sum() / len(df)) * 100
            if null_pct > 50:
                high_null_cols.append({'column': col, 'null_percentage': round(null_pct, 2)})
        
        return {
            'completeness_percentage': round((1 - null_cells / total_cells) * 100, 2),
            'duplicate_rows': duplicate_rows,
            'duplicate_percentage': round((duplicate_rows / len(df)) * 100, 2),
            'high_null_columns': high_null_cols,
            'data_quality_score': self._calculate_quality_score(df, null_cells, total_cells, duplicate_rows)
        }
    
    def _calculate_quality_score(self, df: pd.DataFrame, null_cells: int, total_cells: int, duplicate_rows: int) -> float:
        """Calculate overall data quality score (0-100)"""
        # Completeness score (0-40 points)
        completeness_score = max(0, 40 * (1 - null_cells / total_cells))
        
        # Uniqueness score (0-30 points)
        uniqueness_score = max(0, 30 * (1 - duplicate_rows / len(df)))
        
        # Consistency score (0-30 points) - simplified version
        consistency_score = 30  # Placeholder for now
        
        total_score = completeness_score + uniqueness_score + consistency_score
        return round(total_score, 2)
    
    def _analyze_excel_file_enhanced(self, sheets_data: Dict, file_detection: Dict) -> Dict[str, Any]:
        """Enhanced Excel file analysis"""
        try:
            total_rows = sum(
                sheet_data.get('analysis', {}).get('shape', [0])[0] 
                for sheet_data in sheets_data.values()
            )
            
            total_columns = sum(
                sheet_data.get('analysis', {}).get('shape', [0, 0])[1] 
                for sheet_data in sheets_data.values()
            )
            
            # Analyze data quality across all sheets
            sheets_quality = {}
            for sheet_name, sheet_data in sheets_data.items():
                analysis = sheet_data.get('analysis', {})
                if 'data_quality' in analysis:
                    sheets_quality[sheet_name] = analysis['data_quality']
            
            return {
                'total_sheets': len(sheets_data),
                'total_rows': total_rows,
                'total_columns': total_columns,
                'sheet_names': list(sheets_data.keys()),
                'file_size_mb': file_detection.get('size_mb', 0),
                'sheets_quality_summary': sheets_quality,
                'overall_quality_score': round(
                    sum(sq.get('data_quality_score', 0) for sq in sheets_quality.values()) / len(sheets_quality), 2
                ) if sheets_quality else 0
            }
        except Exception as e:
            return {
                'total_sheets': len(sheets_data),
                'error': str(e)
            }