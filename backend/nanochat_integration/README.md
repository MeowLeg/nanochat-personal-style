# NanoChat 风格训练集成

这个目录存放 nanochat 的核心模块和风格训练相关代码。

## 目录结构

```
nanochat_integration/
├── nanochat/              # 从 karpathy/nanochat 复制的核心模块
│   ├── gpt.py            # GPT 模型定义
│   ├── engine.py         # 推理引擎 (KV Cache)
│   ├── tokenizer.py      # Tokenizer
│   └── common.py         # 工具函数
├── lora/                 # LoRA 实现
│   ├── layers.py         # LoRA 线性层
│   └── utils.py          # LoRA 工具函数
├── training/             # 训练相关
│   ├── data.py           # 风格语料数据加载
│   ├── sft.py            # 监督微调脚本
│   └── trainer.py        # 训练器
└── inference/            # 推理相关
    ├── generator.py      # 风格改写生成器
    └── model_loader.py   # 模型 + LoRA 加载
```