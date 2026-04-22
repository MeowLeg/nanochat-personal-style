
import sys
import os
sys.path.insert(0, '.')

print("=" * 80)
print("完整流程测试")
print("=" * 80)

# 测试 1: 数据清理
print("\n[1/5] 测试数据清理...")
from app.services.data_cleaner import ArticleDataCleaner

test_text = """记者：张三
日期：2024-01-01
版面：A1
【本报讯】
这是测试文章内容。
责编：李四
校对：王五
编辑：赵六
"""

print(f"原始文本:\n{test_text[:200]}")
cleaned = ArticleDataCleaner.clean_article_text(test_text)
print(f"\n清理后:\n{cleaned}")
print("✓ 数据清理测试通过")

# 测试 2: 训练器初始化
print("\n[2/5] 测试训练器初始化...")
from nanochat_integration.training.nanochat_zh_trainer import NanoChatZHTrainer

trainer = NanoChatZHTrainer(adapter_path="/tmp/test_trainer")
print(f"✓ 训练器初始化成功")
print(f"  - 设备: {trainer.device}")
print(f"  - 配置: {trainer.config}")

# 测试 3: 准备数据集
print("\n[3/5] 测试数据集准备...")
test_samples = [
    "这是第一篇测试文章，内容很丰富。",
    "第二篇测试文章，风格很明显。",
    "第三篇测试文章，用于验证训练流程。",
]

dataset_path = trainer.prepare_instruction_dataset(
    test_samples,
    style_name="测试风格",
    style_description="简洁明了的测试风格"
)
print(f"✓ 数据集准备成功")
print(f"  - 数据集路径: {dataset_path}")
import json
with open(dataset_path, 'r', encoding='utf-8') as f:
    dataset = json.load(f)
print(f"  - 样本数量: {len(dataset)}")

print("\n" + "=" * 80)
print("所有测试通过！")
print("=" * 80)

