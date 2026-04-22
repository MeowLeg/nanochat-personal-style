
import os
from typing import List, Dict, Any

from nanochat_integration.training.nanochat_zh_trainer import NanoChatZHGenerator


class NanoChatZHRewriter:
    @staticmethod
    async def rewrite(
        source_text,
        style_id,
        style_name="",
        style_samples=None,
        style_features=None,
        style_strength=0.7,
        max_length=1000
    ):
        rewritten_text = await NanoChatZHGenerator.generate(
            source_text=source_text,
            style_id=style_id,
            style_name=style_name,
            temperature=0.7 + (style_strength * 0.3),
            max_length=max_length
        )
        return rewritten_text

