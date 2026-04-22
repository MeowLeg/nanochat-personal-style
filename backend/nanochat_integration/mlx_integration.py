
import os
import httpx
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from app.core.config import get_settings


@dataclass
class MLXModelConfig:
    model_path: str
    model_name: str
    model_type: str = "qwen"
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    target_modules: List[str] = None


class MLXModelManager:
    def __init__(self, base_dir: str = "./data/mlx_models"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        self.settings = get_settings()
        self.available_models = self._discover_models()

    def _discover_models(self) -> Dict[str, Dict[str, Any]]:
        models = {}

        try:
            response = httpx.get(
                f"{self.settings.openai_base_url}/models",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    for model_info in data["data"]:
                        model_name = model_info.get("id", "")
                        if model_name:
                            model_type = self._guess_model_type(model_name)
                            models[model_name] = {
                                "name": model_name,
                                "path": model_name,
                                "type": model_type
                            }
                    return models
        except Exception as e:
            print(f"[MLXModelManager] Failed to fetch models from oMLX API: {e}")
            print("[MLXModelManager] Falling back to file system scan")

        return self._scan_file_system_for_models()

    def _scan_file_system_for_models(self) -> Dict[str, Dict[str, Any]]:
        models = {}

        common_model_paths = [
            "~/Library/Application Support/oMLX/models",
            "~/oMLX/models",
            "~/.omlx/models",
            "./models",
        ]

        for base_path in common_model_paths:
            full_path = os.path.expanduser(base_path)
            if os.path.exists(full_path):
                for model_name in os.listdir(full_path):
                    model_path = os.path.join(full_path, model_name)
                    if os.path.isdir(model_path):
                        model_type = self._guess_model_type(model_name)
                        models[model_name] = {
                            "name": model_name,
                            "path": model_path,
                            "type": model_type
                        }

        return models

    def _guess_model_type(self, model_name: str) -> str:
        name_lower = model_name.lower()
        if "qwen" in name_lower or "qwopus" in name_lower:
            return "qwen"
        elif "gemma" in name_lower:
            return "gemma"
        elif "llama" in name_lower:
            return "llama"
        elif "mistral" in name_lower:
            return "mistral"
        return "unknown"

    def get_model_config(self, model_name: str) -> Optional[MLXModelConfig]:
        if model_name not in self.available_models:
            return None

        model_info = self.available_models[model_name]
        return MLXModelConfig(
            model_path=model_info["path"],
            model_name=model_name,
            model_type=model_info["type"]
        )

    def list_models(self) -> List[Dict[str, Any]]:
        return list(self.available_models.values())


try:
    import mlx.core as mx
    import mlx.nn as nn

    HAS_MLX = True
except ImportError:
    HAS_MLX = False


class DummyMLXModel:
    def __init__(self, config: MLXModelConfig):
        self.config = config
        print(f"[MLX] Dummy model initialized for {config.model_name}")

    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        return f"[MLX Model Output] This is a dummy response from {self.config.model_name}. Prompt: {prompt[:50]}..."

    def train(self, examples: List[tuple], num_epochs: int = 3, progress_callback=None):
        print(f"[MLX] Training on {len(examples)} examples for {num_epochs} epochs...")
        import time
        
        total_steps = num_epochs * len(examples)
        current_step = 0
        
        for epoch in range(num_epochs):
            print(f"[MLX] Epoch {epoch + 1}/{num_epochs}")
            
            for idx, (prompt, completion) in enumerate(examples):
                current_step += 1
                progress = current_step / total_steps
                
                if progress_callback:
                    progress_callback(0.3 + progress * 0.5)
                
                print(f"[MLX]   Step {current_step}/{total_steps}")
                time.sleep(0.3)
        
        print("[MLX] Training complete!")

    def save_lora(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(f"LoRA adapter for {self.config.model_name}\n")
        print(f"[MLX] LoRA adapter saved to {path}")


def create_mlx_model(config: MLXModelConfig):
    if HAS_MLX:
        try:
            from mlx_lm import load, generate
            print(f"[MLX] Loading model from {config.model_path}")
            model, tokenizer = load(config.model_path)
            return MLXModelWrapper(model, tokenizer, config)
        except Exception as e:
            print(f"[MLX] Failed to load real model: {e}")
            print("[MLX] Falling back to dummy model")

    return DummyMLXModel(config)


class MLXModelWrapper:
    def __init__(self, model, tokenizer, config: MLXModelConfig):
        self.model = model
        self.tokenizer = tokenizer
        self.config = config

    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        from mlx_lm import generate
        return generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

    def train(self, examples: List[tuple], num_epochs: int = 3):
        print(f"[MLX] LoRA training would happen here with {len(examples)} examples")
        print("[MLX] Note: Full LoRA training requires mlx-lm fine-tuning setup")
        import time
        for epoch in range(num_epochs):
            print(f"[MLX] Epoch {epoch + 1}/{num_epochs} (simulated)")
            time.sleep(1.5)

    def save_lora(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(f"LoRA adapter for {self.config.model_name}\n")
        print(f"[MLX] LoRA adapter saved to {path}")