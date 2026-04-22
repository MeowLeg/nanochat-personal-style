"""
Real MLX LoRA fine-tuning implementation.
This is a simplified but actual LoRA training using MLX.
"""
import os
import time
import json
import math
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass

try:
    import mlx.core as mx
    import mlx.nn as nn
    from mlx.utils import tree_flatten, tree_unflatten
    HAS_MLX = True
except ImportError:
    HAS_MLX = False


@dataclass
class LoRAConfig:
    r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.0
    target_modules: List[str] = None


class LoRALinear(nn.Module):
    def __init__(
        self,
        in_features: int,
        out_features: int,
        config: LoRAConfig,
        bias: bool = True
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.config = config
        self.r = config.r
        self.lora_alpha = config.lora_alpha
        self.scaling = self.lora_alpha / self.r

        self.linear = nn.Linear(in_features, out_features, bias=bias)
        self.linear.weight.requires_grad = False
        if self.linear.bias is not None:
            self.linear.bias.requires_grad = False

        if self.r > 0:
            self.lora_a = nn.Linear(in_features, self.r, bias=False)
            self.lora_b = nn.Linear(self.r, out_features, bias=False)
            nn.init.zeros_(self.lora_a.weight)
            nn.init.zeros_(self.lora_b.weight)

    def __call__(self, x):
        result = self.linear(x)
        if self.r > 0:
            lora_x = self.lora_a(x)
            lora_x = self.lora_b(lora_x)
            result = result + lora_x * self.scaling
        return result


def inject_lora(model, config: LoRAConfig):
    """Inject LoRA layers into a model."""
    if config.target_modules is None:
        config.target_modules = ['q_proj', 'k_proj', 'v_proj', 'o_proj']

    for name, module in model.named_modules():
        if isinstance(module, nn.Linear) and any(t in name for t in config.target_modules):
            lora_layer = LoRALinear(
                module.in_features,
                module.out_features,
                config,
                bias=module.bias is not None
            )
            lora_layer.linear.weight = module.weight
            if module.bias is not None:
                lora_layer.linear.bias = module.bias
            setattr(model, name, lora_layer)

    return model


def save_lora_adapter(model, path: str):
    """Save LoRA adapter weights."""
    lora_state = {}
    for name, param in model.named_parameters():
        if 'lora_' in name:
            lora_state[name] = param
    mx.save(path, lora_state)


def load_lora_adapter(model, path: str):
    """Load LoRA adapter weights."""
    lora_state = mx.load(path)
    model.update(lora_state)
    return model


class MLXLoRATrainer:
    def __init__(self, model, tokenizer, config: LoRAConfig):
        self.model = model
        self.tokenizer = tokenizer
        self.config = config
        self.optimizer = None
        self.loss_fn = nn.losses.CrossEntropyLoss()

    def prepare_training_examples(self, examples: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """Prepare examples for training."""
        training_examples = []
        for prompt, completion in examples:
            full_text = prompt + completion
            tokens = self.tokenizer.encode(full_text)
            prompt_tokens = self.tokenizer.encode(prompt)

            training_examples.append({
                'input_ids': mx.array(tokens),
                'labels': mx.array(tokens),
                'prompt_length': len(prompt_tokens)
            })
        return training_examples

    def train_step(self, example: Dict[str, Any]) -> float:
        """Single training step."""
        input_ids = example['input_ids']
        labels = example['labels']
        prompt_len = example['prompt_length']

        with mx.trace():
            logits = self.model(input_ids)
            shift_logits = logits[..., :-1, :]
            shift_labels = labels[..., 1:]

            if prompt_len > 0:
                shift_labels = shift_labels[..., prompt_len:]
                shift_logits = shift_logits[..., prompt_len:, :]

            loss = self.loss_fn(shift_logits.reshape(-1, shift_logits.shape[-1]), shift_labels.reshape(-1))

        if self.optimizer is None:
            self.optimizer = mx.optim.AdamW(learning_rate=1e-4)
            self.optimizer.init(self.model.trainable_parameters())

        loss_value, grads = mx.value_and_grad(self.model)(input_ids, labels)
        self.optimizer.update(self.model, grads)

        return loss_value.item()

    def train(self, examples: List[Tuple[str, str]], num_epochs: int = 3, progress_callback=None):
        """Full training loop."""
        training_examples = self.prepare_training_examples(examples)

        self.model.train()

        for epoch in range(num_epochs):
            total_loss = 0.0
            num_examples = 0

            for idx, example in enumerate(training_examples):
                loss = self.train_step(example)
                total_loss += loss
                num_examples += 1

                if progress_callback:
                    progress = (epoch * len(training_examples) + idx + 1) / (num_epochs * len(training_examples))
                    progress_callback(progress)

            avg_loss = total_loss / num_examples if num_examples > 0 else 0.0
            print(f"[MLX LoRA] Epoch {epoch + 1}/{num_epochs}, Loss: {avg_loss:.4f}")

        return self.model