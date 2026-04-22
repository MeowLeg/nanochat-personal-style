
import os
import json
import torch
from pathlib import Path
from dataclasses import dataclass

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM
)
from peft import LoraConfig, get_peft_model
from datasets import load_dataset


@dataclass
class ModelConfig:
    name: str
    display_name: str
    params: str
    min_vram_gb: int
    recommended_batch_size: int


AVAILABLE_MODELS = [
    ModelConfig(
        name="Qwen/Qwen2.5-0.5B-Instruct",
        display_name="Qwen2.5 0.5B",
        params="5亿",
        min_vram_gb=2,
        recommended_batch_size=4
    ),
    ModelConfig(
        name="Qwen/Qwen2.5-1.5B-Instruct",
        display_name="Qwen2.5 1.5B",
        params="15亿",
        min_vram_gb=4,
        recommended_batch_size=2
    ),
    ModelConfig(
        name="Qwen/Qwen2.5-3B-Instruct",
        display_name="Qwen2.5 3B",
        params="30亿",
        min_vram_gb=8,
        recommended_batch_size=2
    ),
    ModelConfig(
        name="Qwen/Qwen2.5-7B-Instruct",
        display_name="Qwen2.5 7B",
        params="70亿",
        min_vram_gb=16,
        recommended_batch_size=1
    ),
]


@dataclass
class NanoChatZHTrainingConfig:
    base_model_name = "Qwen/Qwen2.5-3B-Instruct"
    batch_size = 2
    learning_rate = 2e-4
    num_epochs = 3
    max_seq_length = 1024
    lora_r = 8
    lora_alpha = 16
    lora_dropout = 0.05


class NanoChatZHTrainer:
    def __init__(
        self,
        adapter_path,
        config=None
    ):
        self.adapter_path = Path(adapter_path)
        self.adapter_path.mkdir(parents=True, exist_ok=True)
        self.config = config or NanoChatZHTrainingConfig()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
        
        print(f"[NanoChatZHTrainer] Initialized on device: {self.device}")
    
    def prepare_instruction_dataset(
        self,
        texts,
        style_name,
        style_description=""
    ):
        from app.services.data_cleaner import ArticleDataCleaner
        
        dataset = []
        
        style_prompt = f"请以{style_name}的写作风格生成稿件"
        if style_description:
            style_prompt += f"，风格特点：{style_description}"
        
        cleaned_texts = ArticleDataCleaner.clean_articles(texts)
        
        for text in cleaned_texts:
            chunks = [text[i:i+1500] for i in range(0, len(text), 1000)]
            
            for chunk in chunks:
                if len(chunk) > 200:
                    data_item = {
                        "instruction": style_prompt,
                        "input": "",
                        "output": chunk
                    }
                    dataset.append(data_item)
        
        dataset_path = self.adapter_path / "style_dataset.json"
        with open(dataset_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        
        print(f"[NanoChatZHTrainer] Prepared {len(dataset)} training examples")
        return str(dataset_path)
    
    def train(
        self,
        dataset_path,
        progress_callback=None
    ):
        print(f"[NanoChatZHTrainer] Starting LoRA training...")
        
        tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model_name,
            trust_remote_code=True
        )
        
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else "auto",
            device_map="auto",
            trust_remote_code=True
        )
        
        lora_config = LoraConfig(
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=self.config.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
        
        raw_dataset = load_dataset("json", data_files=dataset_path)
        
        # 将数据转换为 "text" 字段格式
        def add_text_field(examples):
            texts = []
            for inst, out in zip(examples["instruction"], examples["output"]):
                texts.append(f"指令：{inst}\n输出：{out}")
            return {"text": texts}
        
        raw_dataset = raw_dataset["train"].map(
            add_text_field,
            batched=True,
            remove_columns=raw_dataset["train"].column_names
        )
        
        from trl import SFTConfig, SFTTrainer
        
        training_args = SFTConfig(
            output_dir=str(self.adapter_path),
            per_device_train_batch_size=self.config.batch_size,
            num_train_epochs=self.config.num_epochs,
            learning_rate=self.config.learning_rate,
            logging_steps=10,
            save_strategy="epoch",
            optim="adamw_torch",
            fp16=torch.cuda.is_available() or (torch.backends.mps.is_available() and False),
            report_to="none",
            max_length=self.config.max_seq_length
        )
        
        trainer = SFTTrainer(
            model=model,
            train_dataset=raw_dataset,
            args=training_args,
            processing_class=tokenizer
        )
        
        trainer.train()
        
        model.save_pretrained(self.adapter_path)
        tokenizer.save_pretrained(self.adapter_path)
        
        final_model_path = self.adapter_path / "adapter_model.bin"
        print(f"[NanoChatZHTrainer] Training complete! Saved to: {final_model_path}")
        return str(final_model_path)
    
    @classmethod
    def load(cls, adapter_path):
        from peft import PeftModel, PeftConfig
        
        adapter_path = Path(adapter_path)
        
        config = PeftConfig.from_pretrained(adapter_path)
        base_model = AutoModelForCausalLM.from_pretrained(
            config.base_model_name_or_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else "auto",
            device_map="auto",
            trust_remote_code=True
        )
        tokenizer = AutoTokenizer.from_pretrained(
            config.base_model_name_or_path,
            trust_remote_code=True
        )
        
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = PeftModel.from_pretrained(base_model, adapter_path)
        model = model.to("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        model.eval()
        
        return model, tokenizer


class NanoChatZHGenerator:
    _model_cache = {}
    _tokenizer_cache = {}
    
    @classmethod
    def _load_model(cls, style_id, base_dir="./data/lora_adapters/adapters"):
        if style_id in cls._model_cache:
            return cls._model_cache[style_id], cls._tokenizer_cache[style_id]
        
        adapter_path = os.path.join(base_dir, style_id)
        
        if not os.path.exists(adapter_path):
            raise ValueError(f"Style model not found for {style_id}")
        
        model, tokenizer = NanoChatZHTrainer.load(adapter_path)
        cls._model_cache[style_id] = model
        cls._tokenizer_cache[style_id] = tokenizer
        
        return model, tokenizer
    
    @classmethod
    async def generate(
        cls,
        source_text,
        style_id,
        style_name="",
        max_new_tokens=None,
        temperature=0.7,
        max_length=1000
    ):
        model, tokenizer = cls._load_model(style_id)
        
        if max_new_tokens is None:
            max_new_tokens = max_length
        
        prompt = f"指令：按{style_name}的写作风格改写文章，请将输出严格控制在{max_length}字以内\n输入：{source_text}\n输出："
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=0.9,
                repetition_penalty=1.1,
                do_sample=True
            )
        
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        generated_content = result.replace(prompt, "").strip()
        
        return generated_content
    
    @classmethod
    def clear_cache(cls):
        cls._model_cache.clear()
        cls._tokenizer_cache.clear()

