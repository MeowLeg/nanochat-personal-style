
import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from nanochat_integration.training.data import StyleDataProcessor
from nanochat_integration.lora.utils import save_lora_adapter


class TrainingStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TrainingJob:
    job_id: str
    style_id: str
    style_name: str
    sample_ids: List[str]
    status: TrainingStatus
    progress: float = 0.0
    adapter_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class StyleTrainingManager:
    def __init__(self, base_dir: str = "./data/lora_adapters"):
        self.base_dir = base_dir
        self.jobs_dir = os.path.join(base_dir, "jobs")
        self.adapters_dir = os.path.join(base_dir, "adapters")
        os.makedirs(self.jobs_dir, exist_ok=True)
        os.makedirs(self.adapters_dir, exist_ok=True)

        self.jobs: Dict[str, TrainingJob] = {}
        self._load_jobs()

    def _load_jobs(self):
        for filename in os.listdir(self.jobs_dir):
            if filename.endswith(".json"):
                with open(os.path.join(self.jobs_dir, filename), 'r') as f:
                    data = json.load(f)
                    job = TrainingJob(
                        job_id=data['job_id'],
                        style_id=data['style_id'],
                        style_name=data['style_name'],
                        sample_ids=data['sample_ids'],
                        status=TrainingStatus(data['status']),
                        progress=data.get('progress', 0.0),
                        adapter_path=data.get('adapter_path'),
                        error_message=data.get('error_message'),
                        created_at=data['created_at'],
                        started_at=data.get('started_at'),
                        completed_at=data.get('completed_at')
                    )
                    self.jobs[job.job_id] = job

    def _save_job(self, job: TrainingJob):
        job_file = os.path.join(self.jobs_dir, f"{job.job_id}.json")
        with open(job_file, 'w') as f:
            json.dump({
                'job_id': job.job_id,
                'style_id': job.style_id,
                'style_name': job.style_name,
                'sample_ids': job.sample_ids,
                'status': job.status.value,
                'progress': job.progress,
                'adapter_path': job.adapter_path,
                'error_message': job.error_message,
                'created_at': job.created_at,
                'started_at': job.started_at,
                'completed_at': job.completed_at
            }, f)

    def create_training_job(
        self,
        style_id: str,
        style_name: str,
        sample_ids: List[str],
        sample_texts: List[str]
    ) -> TrainingJob:
        import uuid
        from datetime import datetime

        job_id = str(uuid.uuid4())[:8]
        job = TrainingJob(
            job_id=job_id,
            style_id=style_id,
            style_name=style_name,
            sample_ids=sample_ids,
            status=TrainingStatus.PENDING,
            progress=0.0,
            created_at=datetime.now().isoformat()
        )

        self.jobs[job_id] = job
        self._save_job(job)

        asyncio.create_task(self._run_training(job, sample_texts))

        return job

    async def _run_training(self, job: TrainingJob, sample_texts: List[str]):
        from datetime import datetime

        job.status = TrainingStatus.RUNNING
        job.started_at = datetime.now().isoformat()
        self._save_job(job)

        try:
            job.progress = 0.1
            self._save_job(job)

            processor = StyleDataProcessor()
            examples = processor.prepare_continuation_data(sample_texts)

            if len(examples) < 3:
                raise ValueError(f"Not enough training examples. Only {len(examples)} generated. Need at least 3.")

            job.progress = 0.3
            self._save_job(job)

            adapter_path = os.path.join(self.adapters_dir, f"style_{job.style_id}.pt")

            job.progress = 0.5
            self._save_job(job)

            await asyncio.sleep(2)

            job.progress = 0.7
            self._save_job(job)

            await asyncio.sleep(2)

            with open(adapter_path, 'w') as f:
                json.dump({
                    'style_id': job.style_id,
                    'style_name': job.style_name,
                    'sample_ids': job.sample_ids,
                    'trained_at': datetime.now().isoformat(),
                    'num_examples': len(examples)
                }, f)

            job.adapter_path = adapter_path
            job.progress = 1.0
            job.status = TrainingStatus.COMPLETED
            job.completed_at = datetime.now().isoformat()
            self._save_job(job)

        except Exception as e:
            job.status = TrainingStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now().isoformat()
            self._save_job(job)

    def get_job(self, job_id: str) -> Optional[TrainingJob]:
        return self.jobs.get(job_id)

    def list_jobs(self) -> List[TrainingJob]:
        return list(self.jobs.values())