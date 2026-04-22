
import os
import json
import tempfile
import subprocess
import sys
from typing import List, Tuple, Dict, Any, Optional, Callable
from pathlib import Path


class SimpleMLXLoRATrainer:
    def __init__(self, model_path: str, adapter_path: str = "./adapters"):
        self.model_path = model_path
        self.adapter_path = Path(adapter_path)
        self.adapter_path.mkdir(parents=True, exist_ok=True)

    def prepare_simple_data(
        self,
        sample_texts: List[str],
        output_path: Optional[str] = None
    ) -> str:
        if output_path is None:
            output_path = tempfile.mktemp(suffix=".jsonl")
        
        data = []
        for text in sample_texts:
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
            
            for para in paragraphs:
                if len(para) < 200:
                    continue

                split_idx = len(para) // 2
                prompt = para[:split_idx].rstrip()
                completion = para[split_idx:].lstrip()

                if len(prompt) > 50 and len(completion) > 50:
                    data.append({
                        "prompt": prompt,
                        "completion": completion
                    })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"[SimpleMLXLoRA] Prepared {len(data)} training examples")
        return output_path

    def train(
        self,
        train_data_path: str,
        num_epochs: int = 1,
        num_layers: int = 8,
        batch_size: int = 1,
        progress_callback: Optional[Callable[[float], None]] = None
    ):
        raise RuntimeError(
            "MLX LoRA training is not supported. "
            "Please use NanoChat PyTorch trainer instead. "
            "See nanochat_integration/training/nanochat_trainer.py"
        )

