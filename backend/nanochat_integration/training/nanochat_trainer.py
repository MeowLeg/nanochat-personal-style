
import os
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from dataclasses import dataclass
from pathlib import Path
from tqdm import tqdm

from nanochat_integration.nanochat.gpt import GPT, GPTConfig


class StyleDataset(Dataset):
    def __init__(self, texts, max_length=256):
        self.texts = texts
        self.max_length = max_length
        
        self.vocab = self._build_vocab(texts)
        self.stoi = {ch: i for i, ch in enumerate(self.vocab)}
        self.itos = {i: ch for i, ch in enumerate(self.vocab)}
    
    def _build_vocab(self, texts):
        chars = sorted(list(set(''.join(texts))))
        if len(chars) < 10:
            chars = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !.,?')
        return chars
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        
        tokens = []
        for c in text:
            if c in self.stoi:
                tokens.append(self.stoi[c])
        
        if len(tokens) < 2:
            tokens = [self.stoi.get('a', 0), self.stoi.get('b', 1)]
        
        if len(tokens) > self.max_length + 1:
            tokens = tokens[:self.max_length + 1]
        
        return {
            'input_ids': torch.tensor(tokens[:-1], dtype=torch.long),
            'labels': torch.tensor(tokens[1:], dtype=torch.long)
        }


def collate_fn(batch):
    input_ids = [item['input_ids'] for item in batch]
    labels = [item['labels'] for item in batch]
    
    input_ids = torch.nn.utils.rnn.pad_sequence(input_ids, batch_first=True, padding_value=0)
    labels = torch.nn.utils.rnn.pad_sequence(labels, batch_first=True, padding_value=-1)
    
    return {
        'input_ids': input_ids,
        'labels': labels
    }


@dataclass
class TrainingConfig:
    batch_size: int = 4
    learning_rate: float = 5e-4
    num_epochs: int = 5
    max_length: int = 512
    save_every: int = 1


class NanoChatStyleTrainer:
    def __init__(
        self,
        adapter_path,
        model=None,
        config=None
    ):
        self.adapter_path = Path(adapter_path)
        self.adapter_path.mkdir(parents=True, exist_ok=True)
        
        self.config = config or TrainingConfig()
        self.model = model
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        if self.model is not None:
            self.model.to(self.device)
        
        print(f"[NanoChatTrainer] Initialized on device: {self.device}")
    
    def prepare_data(self, texts):
        data_file = self.adapter_path / "train_data.json"
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(texts, f, ensure_ascii=False)
        
        print(f"[NanoChatTrainer] Prepared {len(texts)} training samples")
        return str(data_file)
    
    def train(
        self,
        train_data_path,
        progress_callback=None
    ):
        print(f"[NanoChatTrainer] Starting training...")
        
        with open(train_data_path, 'r', encoding='utf-8') as f:
            texts = json.load(f)
        
        dataset = StyleDataset(texts, max_length=self.config.max_length)
        
        vocab_size = len(dataset.vocab)
        config = GPTConfig()
        config.vocab_size = vocab_size
        config.n_layer = 8
        config.n_head = 8
        config.n_embd = 512
        config.block_size = self.config.max_length
        
        self.model = GPT(config)
        self.model.to(self.device)
        
        print(f"[NanoChatTrainer] Model params: {sum(p.numel() for p in self.model.parameters()):,}")
        
        vocab_file = self.adapter_path / "vocab.json"
        with open(vocab_file, 'w', encoding='utf-8') as f:
            json.dump(dataset.vocab, f, ensure_ascii=False)
        
        def simple_collate(batch):
            max_len = max(len(item['input_ids']) for item in batch)
            
            input_ids = []
            labels = []
            
            for item in batch:
                pad_len = max_len - len(item['input_ids'])
                input_ids.append(torch.cat([item['input_ids'], torch.zeros(pad_len, dtype=torch.long)]))
                label_pad = torch.full((pad_len,), -100, dtype=torch.long)
                labels.append(torch.cat([item['labels'], label_pad]))
            
            return {
                'input_ids': torch.stack(input_ids),
                'labels': torch.stack(labels)
            }
        
        dataloader = DataLoader(
            dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            collate_fn=simple_collate
        )
        
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate
        )
        
        total_steps = len(dataloader) * self.config.num_epochs
        current_step = 0
        
        self.model.train()
        
        for epoch in range(self.config.num_epochs):
            print(f"[NanoChatTrainer] Epoch {epoch + 1}/{self.config.num_epochs}")
            
            epoch_loss = 0.0
            
            for batch_idx, batch in enumerate(tqdm(dataloader, desc=f"Epoch {epoch + 1}")):
                input_ids = batch['input_ids'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                optimizer.zero_grad()
                
                loss = self.model(input_ids, labels)
                
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                
                current_step += 1
                
                if progress_callback:
                    progress = current_step / total_steps
                    progress_callback(progress)
            
            avg_loss = epoch_loss / len(dataloader)
            print(f"[NanoChatTrainer] Epoch {epoch + 1} - Average loss: {avg_loss:.4f}")
        
        final_model_path = self._save_final_model()
        
        print(f"[NanoChatTrainer] Training complete! Model saved to: {final_model_path}")
        return final_model_path
    
    def _save_final_model(self):
        model_path = self.adapter_path / "model.pt"
        config_path = self.adapter_path / "config.json"
        
        torch.save(self.model.state_dict(), model_path)
        
        config = {
            'vocab_size': self.model.config.vocab_size,
            'n_layer': self.model.config.n_layer,
            'n_head': self.model.config.n_head,
            'n_embd': self.model.config.n_embd,
            'block_size': self.model.config.block_size,
            'dropout': self.model.config.dropout,
            'bias': self.model.config.bias,
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        return str(model_path)
    
    @classmethod
    def load(cls, adapter_path):
        adapter_path = Path(adapter_path)
        
        config_path = adapter_path / "config.json"
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        gpt_config = GPTConfig()
        gpt_config.vocab_size = config_data['vocab_size']
        gpt_config.n_layer = config_data['n_layer']
        gpt_config.n_head = config_data['n_head']
        gpt_config.n_embd = config_data['n_embd']
        gpt_config.block_size = config_data['block_size']
        
        model = GPT(gpt_config)
        
        model_path = adapter_path / "model.pt"
        model.load_state_dict(torch.load(model_path))
        
        trainer = cls(adapter_path=str(adapter_path), model=model)
        return trainer

