import os
import json
import tempfile
import subprocess
from typing import List, Tuple, Dict, Any, Optional, Callable
from pathlib import Path


class MLXLoRATrainer:
    def __init__(self, model_path: str, adapter_path: str = "./adapters"):
        self.model_path = model_path
        self.adapter_path = Path(adapter_path)
        self.adapter_path.mkdir(parents=True, exist_ok=True)

    def prepare_training_data(
        self,
        examples: List[Tuple[str, str]],
        output_path: Optional[str] = None
    ) -> str:
        if output_path is None:
            output_path = tempfile.mktemp(suffix=".jsonl")
        
        data = []
        for prompt, completion in examples:
            data.append({
                "prompt": prompt,
                "completion": completion
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        return output_path

    def train(
        self,
        train_data_path: str,
        num_epochs: int = 3,
        num_layers: int = 16,
        batch_size: int = 4,
        learning_rate: float = 1e-4,
        lora_rank: int = 8,
        lora_alpha: int = 16,
        progress_callback: Optional[Callable[[float], None]] = None
    ):
        cmd = [
            "mlx_lm.lora",
            "--model", self.model_path,
            "--train",
            "--data", train_data_path,
            "--adapter-path", str(self.adapter_path),
            "--iters", str(num_epochs * 100),
            "--num-layers", str(num_layers),
            "--batch-size", str(batch_size),
            "--lr", str(learning_rate),
        ]

        print(f"[MLX LoRA] Running command: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        total_steps = num_epochs * 100
        current_step = 0

        for line in process.stdout:
            print(line, end='')
            
            if "Iter:" in line:
                current_step += 1
                if progress_callback:
                    progress = current_step / total_steps
                    progress_callback(progress)

        process.wait()

        if process.returncode != 0:
            raise RuntimeError(f"MLX LoRA training failed with code {process.returncode}")

        adapter_file = self.adapter_path / "adapters.safetensors"
        if not adapter_file.exists():
            raise RuntimeError(f"Adapter file not found: {adapter_file}")

        return str(adapter_file)


def create_style_transfer_examples(
    sample_texts: List[str],
    author_name: str = "author"
) -> List[Tuple[str, str]]:
    examples = []

    for text in sample_texts:
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        for para in paragraphs:
            if len(para) < 100:
                continue

            split_idx = len(para) // 3
            prompt = para[:split_idx].rstrip()
            completion = para[split_idx:].lstrip()

            if len(prompt) > 30 and len(completion) > 30:
                instruction = f"Continue the following text in {author_name}'s writing style:\n\n{prompt}"
                examples.append((instruction, completion))

    return examples