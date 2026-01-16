from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# 语义分析Agent输出
class SemanticAnalysisOutput(BaseModel):
    energy: int  # 1-5
    tension: int  # 1-5
    control: int  # 1-5
    needs: List[str]  # 三种情感需求
    response_text: str  # 300字回复
    subtle_emotions: List[str]
    tone: str
    themes: List[str]


# 鸡尾酒调配Agent输出
class CocktailIngredient(BaseModel):
    name: str
    category: str
    amount: str


class BaseCocktail(BaseModel):
    name: str
    recipe: str
    description: str


class CocktailMixOutput(BaseModel):
    base_cocktail: BaseCocktail
    customized_recipe: str
    customized_description: str
    adjustment_rationale: str
    ingredients: List[CocktailIngredient]


# 呈现Agent输出
class PresentationOutput(BaseModel):
    cocktail_name: str
    name_candidates: List[str]
    production_video_url: Optional[str] = None
    cocktail_image_url: Optional[str] = None
    final_presentation_image_url: Optional[str] = None
    user_response: str


# 排版Agent输出
class LayoutOutput(BaseModel):
    simplified_response: str  # 2句话
    ink_style_image_url: str
    final_card_url: str


# 完整处理结果
class ProcessingResult(BaseModel):
    task_id: str
    status: TaskStatus
    semantic_analysis: Optional[SemanticAnalysisOutput] = None
    cocktail_mix: Optional[CocktailMixOutput] = None
    presentation: Optional[PresentationOutput] = None
    layout: Optional[LayoutOutput] = None
    error: Optional[str] = None
    progress: Dict[str, Any] = {}


# API请求/响应模型
class AudioUploadResponse(BaseModel):
    task_id: str
    message: str


class ProcessStoryRequest(BaseModel):
    audio_url: Optional[str] = None
    text: Optional[str] = None


class ProcessStoryResponse(BaseModel):
    task_id: str
    status: TaskStatus


class ProcessStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: Dict[str, Any]
    result: Optional[ProcessingResult] = None
