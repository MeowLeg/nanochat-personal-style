import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class LoRALinear(nn.Linear):
    def __init__(
        self,
        in_features: int,
        out_features: int,
        r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.0,
        fan_in_fan_out: bool = False,
        merge_weights: bool = False,
        **kwargs
    ):
        super().__init__(in_features, out_features, **kwargs)
        self.r = r
        self.lora_alpha = lora_alpha
        self.lora_dropout = nn.Dropout(p=lora_dropout) if lora_dropout > 0.0 else nn.Identity()
        self.fan_in_fan_out = fan_in_fan_out
        self.merge_weights = merge_weights

        if r > 0:
            self.lora_A = nn.Parameter(torch.zeros((r, in_features)))
            self.lora_B = nn.Parameter(torch.zeros((out_features, r)))
            self.scaling = self.lora_alpha / self.r
            self.weight.requires_grad = False

        self.reset_parameters()

    def reset_parameters(self):
        super().reset_parameters()
        if hasattr(self, 'lora_A'):
            nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
            nn.init.zeros_(self.lora_B)

    def merge(self):
        if self.r > 0 and self.merge_weights:
            if self.fan_in_fan_out:
                self.weight.data += (self.lora_B @ self.lora_A).T * self.scaling
            else:
                self.weight.data += self.lora_B @ self.lora_A * self.scaling
            self.r = 0

    def unmerge(self):
        if self.r == 0 and hasattr(self, 'lora_A'):
            if self.fan_in_fan_out:
                self.weight.data -= (self.lora_B @ self.lora_A).T * self.scaling
            else:
                self.weight.data -= self.lora_B @ self.lora_A * self.scaling
            self.r = self.lora_A.shape[0]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        result = F.linear(x, self.weight, self.bias)
        if self.r > 0 and not self.merge_weights:
            if self.fan_in_fan_out:
                lora_result = (self.lora_dropout(x) @ self.lora_A.T @ self.lora_B.T) * self.scaling
            else:
                lora_result = (self.lora_dropout(x) @ self.lora_A.T @ self.lora_B.T) * self.scaling
            result = result + lora_result
        return result


def mark_only_lora_as_trainable(model: nn.Module, bias: str = 'none') -> None:
    for n, p in model.named_parameters():
        if 'lora_' not in n:
            p.requires_grad = False
        else:
            p.requires_grad = True

    if bias == 'none':
        return
    elif bias == 'all':
        for n, p in model.named_parameters():
            if 'bias' in n:
                p.requires_grad = True
    elif bias == 'lora_only':
        for m in model.modules():
            if isinstance(m, LoRALinear) and hasattr(m, 'bias') and m.bias is not None:
                m.bias.requires_grad = True


def inject_lora(
    model: nn.Module,
    r: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.0,
    target_modules: list = None
) -> nn.Module:
    if target_modules is None:
        target_modules = ['q_proj', 'k_proj', 'v_proj', 'o_proj', 'c_fc', 'c_proj']

    for name, module in model.named_children():
        if isinstance(module, nn.Linear) and any(t in name for t in target_modules):
            in_features = module.in_features
            out_features = module.out_features
            bias = module.bias is not None

            lora_layer = LoRALinear(
                in_features,
                out_features,
                r=r,
                lora_alpha=lora_alpha,
                lora_dropout=lora_dropout,
                bias=bias
            )
            lora_layer.weight.data = module.weight.data.clone()
            if bias:
                lora_layer.bias.data = module.bias.data.clone()

            setattr(model, name, lora_layer)
        else:
            inject_lora(module, r, lora_alpha, lora_dropout, target_modules)

    return model