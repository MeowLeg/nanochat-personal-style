from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class WritingSampleBase(BaseModel):
    author_name: str = Field(..., description="作者名称")
    source: Optional[str] = Field(None, description="来源")
    language: str = Field(default="zh", description="语言")
    text: str = Field(..., description="文本内容")
    title: Optional[str] = Field(None, description="标题")


class WritingSampleCreate(WritingSampleBase):
    author_id: Optional[str] = Field(None, description="作者档案ID")


class WritingSample(WritingSampleBase):
    id: str
    user_id: str
    author_id: Optional[str]
    length_chars: int
    date_collected: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class AuthorProfileBase(BaseModel):
    name: str = Field(..., description="作者名称")
    description: Optional[str] = Field(None, description="作者描述/备注")


class AuthorProfileCreate(AuthorProfileBase):
    pass


class AuthorProfile(AuthorProfileBase):
    id: str
    user_id: str
    sample_count: int = 0
    style_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StyleProfileBase(BaseModel):
    name: str = Field(..., description="风格名称")
    description: Optional[str] = Field(None, description="风格描述")


class StyleProfileCreate(StyleProfileBase):
    author_id: Optional[str] = Field(None, description="作者档案ID")
    sample_ids: List[str] = Field(..., description="关联的样本ID列表")


class StyleProfile(StyleProfileBase):
    id: str
    user_id: str
    author_id: Optional[str]
    sample_ids: List[str]
    features: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RewriteRequest(BaseModel):
    style_id: str = Field(..., description="风格ID")
    source_text: str = Field(..., description="源文本")
    style_strength: float = Field(default=0.7, ge=0.0, le=1.0, description="风格强度")
    max_length: int = Field(default=1000, ge=100, le=5000, description="生成最大字数")


class RewriteResponse(BaseModel):
    rewritten_text: str
    retrieved_sample_ids: List[str]
    generation_metadata: Dict[str, Any]