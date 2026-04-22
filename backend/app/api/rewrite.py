
import json
import os
from fastapi import APIRouter, HTTPException
from app.models.schemas import RewriteRequest, RewriteResponse
from app.services.nanochat_zh_rewriter import NanoChatZHRewriter

router = APIRouter(prefix="/api", tags=["rewrite"])

DATA_DIR = "./data/styles"
SAMPLES_DIR = "./data/samples"


@router.post("/rewrite", response_model=RewriteResponse)
async def rewrite_article(request: RewriteRequest):
    style_path = os.path.join(DATA_DIR, f"{request.style_id}.json")
    if not os.path.exists(style_path):
        raise HTTPException(status_code=404, detail="Style profile not found")
    
    with open(style_path, 'r', encoding='utf-8') as f:
        style_data = json.load(f)
    
    rewritten_text = await NanoChatZHRewriter.rewrite(
        source_text=request.source_text,
        style_id=request.style_id,
        style_name=style_data['name'],
        style_strength=request.style_strength,
        max_length=request.max_length
    )
    
    return RewriteResponse(
        rewritten_text=rewritten_text,
        retrieved_sample_ids=[],
        generation_metadata={
            "style_strength": request.style_strength,
            "source_length": len(request.source_text),
            "rewritten_length": len(rewritten_text),
            "engine": "nanochat-zh"
        }
    )

