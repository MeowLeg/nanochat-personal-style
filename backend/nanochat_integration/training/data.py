import random
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class TrainingExample:
    prompt: str
    completion: str


class StyleDataProcessor:
    @staticmethod
    def prepare_continuation_data(texts: List[str], min_length: int = 100, max_length: int = 500) -> List[TrainingExample]:
        examples = []
        for text in texts:
            if len(text) < min_length + 50:
                continue

            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
            for para in paragraphs:
                if len(para) < min_length:
                    continue

                max_split = min(len(para) // 2, max_length)
                if max_split <= min_length:
                    continue
                split_idx = random.randint(min_length, max_split)
                prompt = para[:split_idx].rstrip()
                completion = para[split_idx:].lstrip()

                if len(prompt) > 20 and len(completion) > 20:
                    examples.append(TrainingExample(prompt=prompt, completion=completion))

        return examples

    @staticmethod
    def prepare_rewrite_data(texts: List[str], num_augments: int = 2) -> List[TrainingExample]:
        examples = []

        for text in texts:
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

            for para in paragraphs:
                if len(para) < 50:
                    continue

                prompt = f"Rewrite the following text in the author's style:\n\n{para}"
                examples.append(TrainingExample(prompt=prompt, completion=para))

        return examples

    @staticmethod
    def build_chat_format(example: TrainingExample) -> Tuple[str, str]:
        system_prompt = "You are a writing assistant that continues text in the author's style."
        user_prompt = f"Continue this text:\n\n{example.prompt}"
        return system_prompt, user_prompt + example.completion

    @staticmethod
    def concatenate_for_training(examples: List[TrainingExample], sep_token: str = "\n\n") -> str:
        chunks = []
        for ex in examples:
            chunks.append(f"{ex.prompt}{ex.completion}")
        return sep_token.join(chunks)