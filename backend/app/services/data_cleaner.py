
import re
from typing import List, Dict, Any


class ArticleDataCleaner:
    @staticmethod
    def clean_article_text(text):
        if not text:
            return text
        
        cleaned = text
        
        remove_patterns = [
            r"记者：.*?\n",
            r"日期：.*?\n",
            r"版面：.*?\n",
            r"【.*?】",
            r"责编：.*?\n",
            r"校对：.*?\n",
            r"编辑：.*?\n",
            r"^\s+|\s+$",
            r"\n{3,}",
            r"[^\u4e00-\u9fa5，。！？；：“”‘’、.,;?!\s]",
        ]
        
        for pattern in remove_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.MULTILINE)
        
        cleaned = re.sub(r"\n{2,}", "\n\n", cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    @staticmethod
    def clean_articles(texts: List[str]) -> List[str]:
        return [ArticleDataCleaner.clean_article_text(text) for text in texts]

