import os
import torch
import torch.nn as nn


def save_lora_adapter(model: nn.Module, path: str) -> None:
    lora_state_dict = {}
    for name, param in model.named_parameters():
        if 'lora_' in name:
            lora_state_dict[name] = param.detach().cpu().clone()

    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(lora_state_dict, path)


def load_lora_adapter(model: nn.Module, path: str, device: str = 'cpu') -> nn.Module:
    lora_state_dict = torch.load(path, map_location=device)

    model_dict = model.state_dict()
    model_dict.update(lora_state_dict)
    model.load_state_dict(model_dict)

    return model


def get_lora_state_dict(model: nn.Module) -> dict:
    return {
        name: param.detach().cpu().clone()
        for name, param in model.named_parameters()
        if 'lora_' in name
    }