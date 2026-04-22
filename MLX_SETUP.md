# MLX 模型设置指南

本项目支持使用你本地的 MLX 模型进行 LoRA 微调。

## 模型发现路径

系统会自动在以下位置搜索 MLX 模型：

```
~/Library/Application Support/oMLX/models
~/oMLX/models
./models
```

## 你的可用模型

根据你的描述，你有以下模型可以使用：

| 模型 | 推荐度 | 说明 |
|------|--------|------|
| **MLX-Qwopus3.5-27B-v3-4bit** | ⭐⭐⭐⭐⭐ 首选 | 中文支持最好 |
| Qwen3-Coder-30B-A3B-Instruct-MLX-4bit | ⭐⭐⭐⭐ | 代码能力强 |
| gemma-4-26b-a4b-it-4bit | ⭐⭐⭐ | 通用 |
| gemma-4-31b-it-4bit | ⭐⭐⭐ | 通用 |

## 模型目录结构

确保你的模型目录结构如下：

```
~/Library/Application Support/oMLX/models/
├── MLX-Qwopus3.5-27B-v3-4bit/
│   ├── config.json
│   ├── model.safetensors
│   └── tokenizer.json
├── Qwen3-Coder-30B-A3B-Instruct-MLX-4bit/
│   └── ...
└── ...
```

## 使用流程

1. 在「创建风格」页面，点击「训练模型」
2. 在弹出的对话框中选择你的 MLX 模型（推荐选 Qwopus）
3. 确认训练，在「训练模型」页面监控进度
4. 训练完成后即可使用该风格进行改写

## 注意事项

✅ **你的原始模型文件不会被修改**
✅ LoRA Adapter 独立保存（~50MB）
✅ 可以随时删除 LoRA Adapter 不影响原始模型
✅ M3 Max 64GB 可以流畅运行 27B-4bit 模型