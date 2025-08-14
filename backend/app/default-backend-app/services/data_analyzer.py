import pandas as pd
import numpy as np
from typing import Dict, Any, List
import json

class DataAnalyzer:
    def __init__(self):
        pass
    
    def generate_insights(self, file_data: Dict[str, Any]) -> str:
        """Generate natural language insights from data"""
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
        """Generate insights for CSV data"""
        analysis = file_data.get('analysis', {})
        insights = []
        
        # Basic info
        shape = analysis.get('shape', [0, 0])
        insights.append(f"This dataset contains {shape[0]} rows and {shape[1]} columns.")
        
        # Column info
        columns = analysis.get('columns', [])
        if columns:
            insights.append(f"The columns are: {', '.join(columns[:5])}")
            if len(columns) > 5:
                insights.append(f"... and {len(columns) - 5} more columns.")
        
        # Missing data
        null_counts = analysis.get('null_counts', {})
        if null_counts:
            missing_cols = [col for col, count in null_counts.items() if count > 0]
            if missing_cols:
                insights.append(f"Missing data found in columns: {', '.join(missing_cols[:3])}")
        
        # Numeric summary
        summary_stats = analysis.get('summary_stats', {})
        if summary_stats:
            numeric_cols = list(summary_stats.keys())[:3]
            insights.append(f"Key numeric columns include: {', '.join(numeric_cols)}")
        
        return insights
    
    def _analyze_excel_insights(self, file_data: Dict[str, Any]) -> List[str]:
        """Generate insights for Excel data"""
        analysis = file_data.get('analysis', {})
        insights = []
        
        total_sheets = analysis.get('total_sheets', 0)
        insights.append(f"This Excel file contains {total_sheets} worksheet(s).")
        
        sheet_names = analysis.get('sheet_names', [])
        if sheet_names:
            insights.append(f"Sheet names: {', '.join(sheet_names)}")
        
        return insights
    
    def _analyze_text_insights(self, file_data: Dict[str, Any]) -> List[str]:
        """Generate insights for text data"""
        analysis = file_data.get('analysis', {})
        insights = []
        
        word_count = analysis.get('word_count', 0)
        char_count = analysis.get('char_count', 0)
        
        insights.append(f"This document contains {word_count} words and {char_count} characters.")
        
        if analysis.get('pages'):
            insights.append(f"The document has {analysis['pages']} pages.")
        
        return insights