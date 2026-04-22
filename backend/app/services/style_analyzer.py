import json
import re
from typing import Dict, Any, List
from collections import Counter
import statistics


class StyleAnalyzer:
    @staticmethod
    def analyze_style(texts: List[str]) -> Dict[str, Any]:
        all_text = "\n\n".join(texts)
        
        features = {
            "lexical_density": StyleAnalyzer._calculate_lexical_density(all_text),
            "avg_sentence_length": StyleAnalyzer._calculate_avg_sentence_length(all_text),
            "avg_word_length": StyleAnalyzer._calculate_avg_word_length(all_text),
            "punctuation_patterns": StyleAnalyzer._analyze_punctuation(all_text),
            "formality_score": StyleAnalyzer._estimate_formality(all_text),
            "sentence_structure_variance": StyleAnalyzer._analyze_sentence_variance(all_text),
            "vocabulary_richness": StyleAnalyzer._calculate_vocab_richness(all_text),
        }
        
        return features
    
    @staticmethod
    def _calculate_lexical_density(text: str) -> float:
        words = re.findall(r'\b\w+\b', text)
        if not words:
            return 0.0
        content_words = [w for w in words if len(w) > 3]
        return len(content_words) / len(words)
    
    @staticmethod
    def _calculate_avg_sentence_length(text: str) -> float:
        sentences = re.split(r'[.!?。！？]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 0.0
        lengths = [len(re.findall(r'\b\w+\b', s)) for s in sentences]
        return statistics.mean(lengths) if lengths else 0
    
    @staticmethod
    def _calculate_avg_word_length(text: str) -> float:
        words = re.findall(r'\b\w+\b', text)
        if not words:
            return 0.0
        lengths = [len(w) for w in words]
        return statistics.mean(lengths)
    
    @staticmethod
    def _analyze_punctuation(text: str) -> Dict[str, float]:
        total_chars = len(text)
        if total_chars == 0:
            return {}
        
        punctuations = {
            'comma': text.count(','),
            'period': text.count('.'),
            'exclamation': text.count('!'),
            'question': text.count('?'),
            'colon': text.count(':'),
            'semicolon': text.count(';'),
            'dash': text.count('—') + text.count('–'),
        }
        
        return {k: v / total_chars * 1000 for k, v in punctuations.items()}
    
    @staticmethod
    def _estimate_formality(text: str) -> float:
        formal_indicators = ['因此', '然而', '此外', '综上所述', '基于', '根据', '因此']
        informal_indicators = ['哈哈', '哦', '嗯', '啦', '吧', '呢', '嘛']
        
        formal_count = sum(text.count(word) for word in formal_indicators)
        informal_count = sum(text.count(word) for word in informal_indicators)
        total = formal_count + informal_count
        
        if total == 0:
            return 0.5
        
        return formal_count / total
    
    @staticmethod
    def _analyze_sentence_variance(text: str) -> float:
        sentences = re.split(r'[.!?。！？]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) < 2:
            return 0.0
        
        lengths = [len(s) for s in sentences]
        return statistics.variance(lengths) if len(lengths) > 1 else 0
    
    @staticmethod
    def _calculate_vocab_richness(text: str) -> float:
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return 0.0
        unique_words = set(words)
        return len(unique_words) / len(words)