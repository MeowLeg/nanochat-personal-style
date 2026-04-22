import os
import json
import threading
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.schemas import StyleProfile
from nanochat_integration.training.mlx_style_trainer import MLXStyleTrainingManager
from nanochat_integration.training.nanochat_zh_trainer import AVAILABLE_MODELS

router = APIRouter(prefix="/api/training", tags=["training"])

training_manager = MLXStyleTrainingManager()

SAMPLES_DIR = "./data/samples"


class CreateTrainingJobRequest(BaseModel):
    style_profile: StyleProfile
    model_name: Optional[str] = Field(None, description="可选，指定使用的模型")


@router.get("/models")
async def list_available_models():
    models = training_manager.list_available_models()
    return {"models": models}


@router.get("/models/zh")
async def list_nanochat_models():
    return {
        "models": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "params": m.params,
                "min_vram_gb": m.min_vram_gb,
                "recommended_batch_size": m.recommended_batch_size
            }
            for m in AVAILABLE_MODELS
        ]
    }


@router.post("/jobs")
async def create_training_job(request: CreateTrainingJobRequest, background_tasks: BackgroundTasks):
    style_profile = request.style_profile
    model_name = request.model_name

    sample_texts = []
    for sample_id in style_profile.sample_ids:
        sample_path = os.path.join(SAMPLES_DIR, f"{sample_id}.json")
        if not os.path.exists(sample_path):
            raise HTTPException(status_code=404, detail=f"Sample {sample_id} not found")

        with open(sample_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sample_texts.append(data['text'])

    if len(sample_texts) == 0:
        raise HTTPException(status_code=400, detail="No valid samples found")

    job = training_manager.create_training_job(
        style_id=style_profile.id,
        style_name=style_profile.name,
        sample_ids=style_profile.sample_ids,
        sample_texts=sample_texts,
        model_name=model_name
    )

    background_tasks.add_task(training_manager.run_training_sync, job, sample_texts)

    return {
        "job_id": job.job_id,
        "style_id": job.style_id,
        "style_name": job.style_name,
        "model_name": job.model_name,
        "status": job.status.value,
        "created_at": job.created_at
    }


@router.get("/jobs")
async def list_training_jobs():
    jobs = training_manager.list_jobs()
    return [
        {
            "job_id": job.job_id,
            "style_id": job.style_id,
            "style_name": job.style_name,
            "model_name": job.model_name,
            "status": job.status.value,
            "progress": job.progress,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "error_message": job.error_message
        }
        for job in jobs
    ]


@router.get("/jobs/{job_id}")
async def get_training_job(job_id: str):
    job = training_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.job_id,
        "style_id": job.style_id,
        "style_name": job.style_name,
        "model_name": job.model_name,
        "status": job.status.value,
        "progress": job.progress,
        "adapter_path": job.adapter_path,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "error_message": job.error_message
    }


@router.delete("/jobs/{job_id}")
async def delete_training_job(job_id: str):
    success = training_manager.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted successfully"}