
import os
import json
import torch

style_id = "7aab255d-3a6b-4693-9567-c450540fff2e"
base_dir = "./data/lora_adapters/adapters"

adapter_path = os.path.join(base_dir, style_id)

print("=== 1. 检查文件 ===")
print(f"Adapter path: {adapter_path}")
print(f"Files: {os.listdir(adapter_path)}")

print("\n=== 2. 加载词汇表 ===")
with open(os.path.join(adapter_path, "vocab.json"), 'r', encoding='utf-8') as f:
    vocab = json.load(f)
print(f"Vocab size: {len(vocab)}")
print(f"First 50 chars: {vocab[:50]}")

print("\n=== 3. 测试编码解码 ===")
test_text = "春风拂大地，植树正当时。"
print(f"Input: {test_text}")

stoi = {ch: i for i, ch in enumerate(vocab)}
tokens = [stoi[c] for c in test_text if c in stoi]
print(f"Encoded: {tokens}")

itos = {i: ch for i, ch in enumerate(vocab)}
decoded = ''.join([itos[t] for t in tokens])
print(f"Decoded: {decoded}")

print("\n=== 4. 加载模型测试 ===")
sys.path.insert(0, '.')
from nanochat_integration.training.nanochat_trainer import NanoChatStyleTrainer

trainer = NanoChatStyleTrainer.load(adapter_path)
print(f"Model loaded!")
print(f"Model config: {trainer.model.config}")

print("\n=== 5. 简单生成测试 ===")
model = trainer.model
model.eval()
device = next(model.parameters()).device

prompt = "春风"
input_tokens = [stoi[c] for c in prompt if c in stoi]
print(f"Prompt: {prompt}")
print(f"Prompt tokens: {input_tokens}")

idx = torch.tensor(input_tokens, dtype=torch.long, device=device).unsqueeze(0)
print(f"Input shape: {idx.shape}")

for i in range(20):
    idx_cond = idx if idx.size(1) <= model.config.block_size else idx[:, -model.config.block_size:]
    
    with torch.no_grad():
        logits = model(idx_cond)
        logits = logits[:, -1, :] / 0.8
        
        probs = torch.softmax(logits, dim=-1)
        idx_next = torch.multinomial(probs, num_samples=1)
        idx = torch.cat((idx, idx_next), dim=1)
        
        next_token = idx_next.item()
        next_char = itos.get(next_token, f'[{next_token}]')
        print(f"Step {i+1}: token={next_token}, char='{next_char}'")

final_tokens = idx[0].tolist()
final_text = ''.join([itos.get(t, f'[{t}]') for t in final_tokens])
print(f"\nFinal generated: {final_text}")

