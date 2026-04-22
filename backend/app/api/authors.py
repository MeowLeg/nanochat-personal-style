import os
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import List

from app.models.schemas import AuthorProfile, AuthorProfileCreate

router = APIRouter(prefix="/api", tags=["authors"])

AUTHORS_DIR = "./data/authors"
SAMPLES_DIR = "./data/samples"
STYLES_DIR = "./data/styles"

os.makedirs(AUTHORS_DIR, exist_ok=True)


def get_next_id() -> str:
    return str(uuid.uuid4())


@router.post("/authors", response_model=AuthorProfile)
async def create_author(author_data: AuthorProfileCreate):
    author_id = get_next_id()
    author = AuthorProfile(
        id=author_id,
        user_id="default",
        name=author_data.name,
        description=author_data.description,
        sample_count=0,
        style_count=0,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    with open(os.path.join(AUTHORS_DIR, f"{author_id}.json"), 'w', encoding='utf-8') as f:
        json.dump(author.model_dump(), f, ensure_ascii=False, default=str)
    
    return author


@router.get("/authors", response_model=List[AuthorProfile])
async def list_authors():
    authors = []
    for filename in os.listdir(AUTHORS_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(AUTHORS_DIR, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['created_at'] = datetime.fromisoformat(data['created_at'])
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                author_id = data['id']
                sample_count = 0
                style_count = 0
                
                for sample_file in os.listdir(SAMPLES_DIR):
                    if sample_file.endswith('.json'):
                        with open(os.path.join(SAMPLES_DIR, sample_file), 'r') as f:
                            sample_data = json.load(f)
                            if sample_data.get('author_id') == author_id:
                                sample_count += 1
                
                for style_file in os.listdir(STYLES_DIR):
                    if style_file.endswith('.json'):
                        with open(os.path.join(STYLES_DIR, style_file), 'r') as f:
                            style_data = json.load(f)
                            if style_data.get('author_id') == author_id:
                                style_count += 1
                
                data['sample_count'] = sample_count
                data['style_count'] = style_count
                
                authors.append(AuthorProfile(**data))
    return authors


@router.get("/authors/{author_id}", response_model=AuthorProfile)
async def get_author(author_id: str):
    filepath = os.path.join(AUTHORS_DIR, f"{author_id}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Author not found")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        author_id = data['id']
        sample_count = 0
        style_count = 0
        
        if os.path.exists(SAMPLES_DIR):
            for sample_file in os.listdir(SAMPLES_DIR):
                if sample_file.endswith('.json'):
                    with open(os.path.join(SAMPLES_DIR, sample_file), 'r') as f:
                        sample_data = json.load(f)
                        if sample_data.get('author_id') == author_id:
                            sample_count += 1
        
        if os.path.exists(STYLES_DIR):
            for style_file in os.listdir(STYLES_DIR):
                if style_file.endswith('.json'):
                    with open(os.path.join(STYLES_DIR, style_file), 'r') as f:
                        style_data = json.load(f)
                        if style_data.get('author_id') == author_id:
                            style_count += 1
        
        data['sample_count'] = sample_count
        data['style_count'] = style_count
        
        return AuthorProfile(**data)


@router.delete("/authors/{author_id}")
async def delete_author(author_id: str):
    filepath = os.path.join(AUTHORS_DIR, f"{author_id}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Author not found")
    
    os.remove(filepath)
    return {"message": "Author deleted successfully"}


@router.get("/authors/{author_id}/samples", response_model=List[dict])
async def get_author_samples(author_id: str):
    """获取指定作者的所有稿件"""
    from app.models.schemas import WritingSample
    
    samples = []
    if os.path.exists(SAMPLES_DIR):
        for filename in os.listdir(SAMPLES_DIR):
            if filename.endswith('.json'):
                with open(os.path.join(SAMPLES_DIR, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('author_id') == author_id:
                        data['created_at'] = datetime.fromisoformat(data['created_at']).isoformat()
                        data['date_collected'] = datetime.fromisoformat(data['date_collected']).isoformat()
                        samples.append(data)
    return samples