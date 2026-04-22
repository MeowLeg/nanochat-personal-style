import os
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List, Optional

from app.models.schemas import WritingSample, WritingSampleCreate, StyleProfile, StyleProfileCreate
from app.services.style_analyzer import StyleAnalyzer
from app.services.excel_parser import ExcelParser

router = APIRouter(prefix="/api", tags=["styles"])

DATA_DIR = "./data/styles"
SAMPLES_DIR = "./data/samples"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)


def get_next_id() -> str:
    return str(uuid.uuid4())


def is_excel_file(filename: str) -> bool:
    return filename.lower().endswith(('.xlsx', '.xls'))


@router.post("/samples/import", response_model=List[WritingSample])
async def import_samples(
    files: List[UploadFile] = File(...),
    author_name: str = Form(...),
    source: Optional[str] = Form(None),
    language: str = Form(default="zh"),
    author_id: Optional[str] = Form(None)
):
    samples = []
    
    for file in files:
        content = await file.read()
        filename = file.filename or "unknown"
        
        if is_excel_file(filename):
            try:
                excel_samples = ExcelParser.get_sample_texts_from_excel(content, filename)
                
                for idx, (title, text) in enumerate(excel_samples):
                    sample_id = get_next_id()
                    sample_source = source or f"{filename} - {idx + 1}"
                    if title:
                        sample_source = f"{sample_source} - {title}"
                    
                    sample = WritingSample(
                        id=sample_id,
                        user_id="default",
                        author_id=author_id,
                        author_name=author_name,
                        source=sample_source,
                        language=language,
                        text=text,
                        title=title,
                        length_chars=len(text),
                        date_collected=datetime.now(),
                        created_at=datetime.now()
                    )
                    
                    with open(os.path.join(SAMPLES_DIR, f"{sample_id}.json"), 'w', encoding='utf-8') as f:
                        json.dump(sample.model_dump(), f, ensure_ascii=False, default=str)
                    
                    samples.append(sample)
            
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Excel 文件解析失败: {filename}, 错误: {str(e)}")
        
        else:
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                text = content.decode('gbk', errors='ignore')
            
            sample_id = get_next_id()
            sample = WritingSample(
                id=sample_id,
                user_id="default",
                author_id=author_id,
                author_name=author_name,
                source=source or filename,
                language=language,
                text=text,
                title=filename,
                length_chars=len(text),
                date_collected=datetime.now(),
                created_at=datetime.now()
            )
            
            with open(os.path.join(SAMPLES_DIR, f"{sample_id}.json"), 'w', encoding='utf-8') as f:
                json.dump(sample.model_dump(), f, ensure_ascii=False, default=str)
            
            samples.append(sample)
    
    return samples


@router.get("/samples", response_model=List[WritingSample])
async def list_samples():
    samples = []
    for filename in os.listdir(SAMPLES_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(SAMPLES_DIR, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['date_collected'] = datetime.fromisoformat(data['date_collected'])
                data['created_at'] = datetime.fromisoformat(data['created_at'])
                samples.append(WritingSample(**data))
    return samples


@router.get("/samples/{sample_id}", response_model=WritingSample)
async def get_sample(sample_id: str):
    filepath = os.path.join(SAMPLES_DIR, f"{sample_id}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Sample not found")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        data['date_collected'] = datetime.fromisoformat(data['date_collected'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return WritingSample(**data)


@router.put("/samples/{sample_id}")
async def update_sample(sample_id: str, update_data: dict):
    filepath = os.path.join(SAMPLES_DIR, f"{sample_id}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Sample not found")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'title' in update_data:
        data['title'] = update_data['title']
    if 'source' in update_data:
        data['source'] = update_data['source']
    if 'text' in update_data:
        data['text'] = update_data['text']
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, default=str)
    
    return {"message": "Sample updated successfully"}


@router.post("/style_profiles", response_model=StyleProfile)
async def create_style_profile(profile_data: StyleProfileCreate):
    sample_texts = []
    for sample_id in profile_data.sample_ids:
        filepath = os.path.join(SAMPLES_DIR, f"{sample_id}.json")
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"Sample {sample_id} not found")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sample_texts.append(data['text'])
    
    features = StyleAnalyzer.analyze_style(sample_texts)
    
    profile_id = get_next_id()
    profile = StyleProfile(
        id=profile_id,
        user_id="default",
        author_id=profile_data.author_id,
        name=profile_data.name,
        description=profile_data.description,
        sample_ids=profile_data.sample_ids,
        features=features,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    with open(os.path.join(DATA_DIR, f"{profile_id}.json"), 'w', encoding='utf-8') as f:
        json.dump(profile.model_dump(), f, ensure_ascii=False, default=str)
    
    return profile


@router.get("/style_profiles", response_model=List[StyleProfile])
async def list_style_profiles():
    profiles = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['created_at'] = datetime.fromisoformat(data['created_at'])
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                profiles.append(StyleProfile(**data))
    return profiles


@router.get("/style_profiles/{profile_id}", response_model=StyleProfile)
async def get_style_profile(profile_id: str):
    filepath = os.path.join(DATA_DIR, f"{profile_id}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Style profile not found")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return StyleProfile(**data)


@router.delete("/style_profiles/{profile_id}")
async def delete_style_profile(profile_id: str):
    filepath = os.path.join(DATA_DIR, f"{profile_id}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Style profile not found")
    
    os.remove(filepath)
    
    return {"message": "Style profile deleted successfully"}