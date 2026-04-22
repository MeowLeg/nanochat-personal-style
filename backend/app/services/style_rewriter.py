from typing import List, Dict, Any
from app.core.llm import call_llm


class StyleRewriter:
    @staticmethod
    async def rewrite(
        source_text: str,
        style_samples: List[str],
        style_features: Dict[str, Any],
        style_strength: float = 0.7
    ) -> str:
        system_prompt = StyleRewriter._build_system_prompt(style_strength)
        user_prompt = StyleRewriter._build_user_prompt(source_text, style_samples, style_features)
        
        result = await call_llm(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3 + (style_strength * 0.4)
        )
        
        return result
    
    @staticmethod
    def _build_system_prompt(style_strength: float) -> str:
        base_instruction = """你是一个专业的写作风格改写助手。你的任务是将给定的文本改写成指定作者的写作风格，同时保持原文的核心意思和信息完整性。

改写原则：
1. 保持原文的所有信息和核心观点不变
2. 模仿目标作者的用词习惯、句式结构和语气
3. 保持内容的准确性和专业性
4. 不要添加原文没有的信息，也不要遗漏重要内容
5. 如果原文有引用、数据或具体事实，请完整保留"""

        strength_note = f"""
风格强度设置为 {style_strength:.2f}（0-1之间）：
- 接近 0：保持原文结构，仅微调用词
- 接近 1：深度重构，充分体现目标风格特征"""

        return base_instruction + strength_note
    
    @staticmethod
    def _build_user_prompt(
        source_text: str,
        style_samples: List[str],
        style_features: Dict[str, Any]
    ) -> str:
        samples_section = StyleRewriter._format_samples(style_samples)
        features_section = StyleRewriter._format_features(style_features)
        
        return f"""请将以下文本改写成指定作者的写作风格。

【目标作者的写作样本】
{samples_section}

【风格特征分析】
{features_section}

【需要改写的原文】
{source_text}

请只输出改写后的文本，不要包含其他解释或说明。"""
    
    @staticmethod
    def _format_samples(samples: List[str]) -> str:
        formatted = []
        for i, sample in enumerate(samples[:3], 1):
            preview = sample[:500] + "..." if len(sample) > 500 else sample
            formatted.append(f"样本 {i}:\n{preview}\n")
        return "\n".join(formatted)
    
    @staticmethod
    def _format_features(features: Dict[str, Any]) -> str:
        feature_desc = []
        if 'avg_sentence_length' in features:
            feature_desc.append(f"- 平均句长: {features['avg_sentence_length']:.1f} 词")
        if 'formality_score' in features:
            formality = "正式" if features['formality_score'] > 0.6 else "非正式" if features['formality_score'] < 0.4 else "中性"
            feature_desc.append(f"- 语气风格: {formality}")
        if 'vocabulary_richness' in features:
            richness = "丰富" if features['vocabulary_richness'] > 0.7 else "简洁" if features['vocabulary_richness'] < 0.4 else "中等"
            feature_desc.append(f"- 词汇丰富度: {richness}")
        
        return "\n".join(feature_desc) if feature_desc else "未提供详细特征"