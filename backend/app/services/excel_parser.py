import io
import pandas as pd
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class ExcelRow:
    title: str
    content: str


class ExcelParser:
    @staticmethod
    def parse_excel(file_content: bytes, filename: str) -> List[ExcelRow]:
        rows = []
        
        try:
            df = pd.read_excel(io.BytesIO(file_content))
            
            title_col = None
            content_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if '标题' in col_lower or 'title' in col_lower:
                    title_col = col
                elif '内容' in col_lower or 'content' in col_lower or '正文' in col_lower:
                    content_col = col
            
            if title_col is None and len(df.columns) >= 1:
                title_col = df.columns[0]
            if content_col is None and len(df.columns) >= 2:
                content_col = df.columns[1]
            elif content_col is None and len(df.columns) == 1:
                content_col = title_col
            
            for _, row in df.iterrows():
                title = str(row.get(title_col, '')) if title_col else ''
                content = str(row.get(content_col, '')) if content_col else ''
                
                if pd.isna(title):
                    title = ''
                if pd.isna(content):
                    content = ''
                
                if content.strip():
                    rows.append(ExcelRow(title=title, content=content))
        
        except Exception as e:
            raise ValueError(f"Excel 解析失败: {str(e)}")
        
        return rows

    @staticmethod
    def combine_title_content(title: str, content: str) -> str:
        if title and title.strip():
            return f"{title}\n\n{content}"
        return content

    @staticmethod
    def get_sample_texts_from_excel(file_content: bytes, filename: str) -> List[Tuple[str, str]]:
        rows = ExcelParser.parse_excel(file_content, filename)
        return [(row.title, ExcelParser.combine_title_content(row.title, row.content)) for row in rows]