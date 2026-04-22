import os
import time
import torch
import torch.nn as nn
from typing import Optional, Callable
from dataclasses import dataclass


@dataclass
class TrainingConfig:
    batch_size: int = 4
    learning_rate: float = 3e-4
    num_epochs: int = 3
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    log_every: int = 10
    save_every: int = 100
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class StyleTrainer:
    def __init__(
        self,
        model: nn.Module,
        config: TrainingConfig,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Callable] = None
    ):
        self.model = model.to(config.device)
        self.config = config
        self.optimizer = optimizer or self._create_optimizer()
        self.scheduler = scheduler
        self.scaler = torch.cuda.amp.GradScaler() if torch.cuda.is_available() else None

    def _create_optimizer(self):
        params = [p for p in self.model.parameters() if p.requires_grad]
        return torch.optim.AdamW(
            params,
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay
        )

    def train_step(self, batch: torch.Tensor) -> dict:
        self.model.train()
        self.optimizer.zero_grad()

        batch = batch.to(self.config.device)

        with torch.cuda.amp.autocast(enabled=self.scaler is not None):
            loss = self.model(batch)

        if self.scaler:
            self.scaler.scale(loss).backward()
            self.scaler.unscale_(self.optimizer)
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
            self.optimizer.step()

        if self.scheduler:
            self.scheduler.step()

        return {"loss": loss.item()}

    def train_epoch(self, dataloader, epoch: int) -> dict:
        total_loss = 0.0
        num_batches = 0

        start_time = time.time()

        for batch_idx, batch in enumerate(dataloader):
            metrics = self.train_step(batch)
            total_loss += metrics["loss"]
            num_batches += 1

            if batch_idx % self.config.log_every == 0:
                elapsed = time.time() - start_time
                print(f"Epoch {epoch}, Batch {batch_idx}, Loss: {metrics['loss']:.4f}, Elapsed: {elapsed:.2f}s")

        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        return {"avg_loss": avg_loss, "num_batches": num_batches}

    def train(self, dataloader, num_epochs: Optional[int] = None) -> dict:
        epochs = num_epochs or self.config.num_epochs
        training_metrics = []

        for epoch in range(epochs):
            print(f"\n=== Epoch {epoch + 1}/{epochs} ===")
            epoch_metrics = self.train_epoch(dataloader, epoch)
            training_metrics.append(epoch_metrics)
            print(f"Epoch {epoch + 1} complete. Avg Loss: {epoch_metrics['avg_loss']:.4f}")

        return {"epochs": epochs, "metrics": training_metrics}