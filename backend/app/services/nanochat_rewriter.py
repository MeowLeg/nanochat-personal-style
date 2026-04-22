
import os
import json
import torch
import torch.nn.functional as F
from typing import List, Dict, Any
from pathlib import Path

from nanochat_integration.nanochat.gpt import GPT, GPTConfig
from nanochat_integration.training.nanochat_trainer import NanoChatStyleTrainer


class NanoChatStyleRewriter:
    _model_cache = {}
    
    @classmethod
    def _load_model(cls, style_id: str, base_dir: str = "./data/lora_adapters/adapters"):
        if style_id in cls._model_cache:
            return cls._model_cache[style_id]
        
        adapter_path = os.path.join(base_dir, style_id)
        
        if not os.path.exists(adapter_path):
            raise ValueError(f"Style model not found for {style_id}")
        
        trainer = NanoChatStyleTrainer.load(adapter_path)
        cls._model_cache[style_id] = trainer
        return trainer
    
    @staticmethod
    def _encode_text(text: str, vocab: List[str]) -> List[int]:
        stoi = {ch: i for i, ch in enumerate(vocab)}
        tokens = []
        for c in text:
            if c in stoi:
                tokens.append(stoi[c])
        return tokens
    
    @staticmethod
    def _decode_tokens(tokens: List[int], vocab: List[str]) -> str:
        itos = {i: ch for i, ch in enumerate(vocab)}
        return ''.join([itos.get(t, '') for t in tokens])
    
    @classmethod
    def _top_p_sampling(cls, logits, top_p=0.9):
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
        
        sorted_indices_to_remove = cumulative_probs > top_p
        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
        sorted_indices_to_remove[..., 0] = 0
        
        indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
        logits[indices_to_remove] = float('-inf')
        
        probs = F.softmax(logits, dim=-1)
        return torch.multinomial(probs, num_samples=1)
    
    @classmethod
    async def rewrite(
        cls,
        source_text: str,
        style_id: str,
        style_samples: List[str] = None,
        max_new_tokens: int = 800,
        temperature: float = 0.7
    ) -> str:
        trainer = cls._load_model(style_id)
        
        vocab_path = os.path.join(trainer.adapter_path, "vocab.json")
        with open(vocab_path, 'r', encoding='utf-8') as f:
            vocab = json.load(f)
        
        model = trainer.model
        model.eval()
        device = next(model.parameters()).device
        
        if style_samples and len(style_samples) > 0:
            prompt = style_samples[0][:150] + "\n\n" + source_text[:100]
        else:
            prompt = source_text[:150] if len(source_text) > 150 else source_text
        
        input_tokens = cls._encode_text(prompt, vocab)
        
        if len(input_tokens) == 0:
            input_tokens = [0]
        
        idx = torch.tensor(input_tokens, dtype=torch.long, device=device).unsqueeze(0)
        
        block_size = model.config.block_size
        
        for step in range(max_new_tokens):
            idx_cond = idx if idx.size(1) <= block_size else idx[:, -block_size:]
            
            with torch.no_grad():
                logits = model(idx_cond)
                logits = logits[:, -1, :] / temperature
                
                idx_next = cls._top_p_sampling(logits, top_p=0.9)
                idx = torch.cat((idx, idx_next), dim=1)
        
        generated_tokens = idx[0].tolist()
        generated_text = cls._decode_tokens(generated_tokens, vocab)
        
        return generated_text
    
    @classmethod
    def clear_cache(cls):
        cls._model_cache.clear()

