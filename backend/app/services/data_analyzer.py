import pandas as pd
import numpy as np
from typing import Dict, Any, List
import json

class DataAnalyzer:
    def __init__(self):
        pass

    def generate_insights(self, file_data: Dict[str, Any]) -> str:
        file_type = file_data.get('type')
        insights = []

        if file_type == 'csv':
            insights = self._analyze_csv_insights(file_data)
        elif file_type == 'excel':
            insights = self._analyze_excel_insights(file_data)
        elif file_type in ['pdf', 'docx', 'txt']:
            insights = self._analyze_text_insights(file_data)

        return "\n".join(insights)

    def _analyze_csv_insights(self, file_data: Dict[str, Any]) -> List[str]:
        analysis_summary = file_data.get('analysis_summary', {})
        insights = []
        
        shape = analysis_summary.get('shape', [0, 0])
        total_rows, total_cols = shape[0], shape[1]
        
        insights.append(f"File ini berisi {total_rows} baris dan {total_cols} kolom.")
        
        columns = analysis_summary.get('columns', [])
        if len(columns) > 0:
            insights.append(f"Kolom yang terdeteksi adalah: {', '.join(columns)}.")
            
        total_missing = analysis_summary.get('total_missing', 0)
        total_duplicates = analysis_summary.get('total_duplicates', 0)
        
        if total_missing > 0:
            insights.append(f"Terdapat total {total_missing} nilai yang hilang.")
        
        if total_duplicates > 0:
            insights.append(f"Ditemukan {total_duplicates} duplikasi baris, yang merupakan {round((total_duplicates/total_rows)*100, 2) if total_rows > 0 else 0}% dari total data.")
        
        quality_score = analysis_summary.get('data_quality', {}).get('data_quality_score', 'N/A')
        insights.append(f"Skor kualitas data keseluruhan: {quality_score}/100.")
        
        missing_columns = [col for col, info in analysis_summary.get('column_types', {}).items() if info.get('missing_count', 0) > 0]
        if missing_columns:
            insights.append(f"Kolom dengan nilai yang hilang: {', '.join(missing_columns)}.")
        
        return insights

    def _analyze_excel_insights(self, file_data: Dict[str, Any]) -> List[str]:
        analysis_summary = file_data.get('analysis_summary', {})
        insights = []

        total_sheets = analysis_summary.get('total_sheets', 0)
        sheet_names = analysis_summary.get('sheet_names', [])
        
        insights.append(f"File Excel ini berisi {total_sheets} lembar kerja.")
        if sheet_names:
            insights.append(f"Nama-nama lembar kerja: {', '.join(sheet_names)}.")
        
        shape = analysis_summary.get('shape', [0, 0])
        total_rows, total_columns = shape[0], shape[1]
        insights.append(f"Secara total, file ini memiliki {total_rows} baris dan {total_columns} kolom unik.")

        quality_score = analysis_summary.get('overall_data_quality_score', 0)
        insights.append(f"Skor kualitas data rata-rata di seluruh sheet adalah {quality_score}/100.")
        
        total_missing = analysis_summary.get('total_missing_values', 0)
        total_duplicates = analysis_summary.get('total_duplicates', 0)
        
        if total_missing > 0:
            insights.append(f"Terdapat total {total_missing} nilai yang hilang di seluruh lembar kerja.")
        
        if total_duplicates > 0:
            insights.append(f"Ditemukan total {total_duplicates} duplikasi baris di seluruh lembar kerja.")

        return insights

    def _analyze_text_insights(self, file_data: Dict[str, Any]) -> List[str]:
        analysis_summary = file_data.get('analysis_summary', {})
        insights = []

        if 'pages' in analysis_summary:
            insights.append(f"Dokumen ini memiliki {analysis_summary['pages']} halaman.")

        if 'word_count' in analysis_summary:
            insights.append(f"Total jumlah kata: {analysis_summary['word_count']:,}.")
            
        if 'reading_time_minutes' in analysis_summary:
            insights.append(f"Estimasi waktu membaca: sekitar {analysis_summary['reading_time_minutes']} menit.")

        if analysis_summary.get('ai_summary'):
            insights.append("\nRingkasan AI:\n" + analysis_summary['ai_summary'])

        return insights