from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ArticleResponse(BaseModel):
    """Modelo de respuesta para artículos"""
    id: int
    title: str
    slug: str
    main_keyword: str
    stage: str
    category: str
    tags: List[str]
    is_published: bool
    created_at: datetime
    wordpress_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class ArticleCreate(BaseModel):
    """Modelo para crear artículos manualmente"""
    title: str
    content: str
    main_keyword: str
    stage: str
    category: str
    tags: List[str]
    meta_description: Optional[str] = None

class KeywordCreate(BaseModel):
    """Modelo para crear keywords"""
    keyword: str
    stage: str  # conciencia, consideracion, compra
    priority: int = 1  # 1-5

class KeywordResponse(BaseModel):
    """Modelo de respuesta para keywords"""
    id: int
    keyword: str
    stage: str
    priority: int
    is_used: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class CategoryResponse(BaseModel):
    """Modelo de respuesta para categorías"""
    id: int
    name: str
    slug: str
    article_count: int

class WorkflowStatus(BaseModel):
    """Modelo para estado de workflows"""
    workflow_id: str
    status: str  # starting, running, completed, failed, cancelled, error
    progress: int  # 0-100
    current_step: str
    created_at: datetime
    errors: List[str]
    result: Optional[Dict[str, Any]] = None

class GenerateArticleRequest(BaseModel):
    """Modelo para solicitud de generación de artículo"""
    force_keyword: Optional[str] = None
    force_stage: Optional[str] = None
    skip_wordpress: bool = False

class StatsResponse(BaseModel):
    """Modelo para estadísticas del sistema"""
    articles: Dict[str, Any]
    keywords: Dict[str, Any]
    active_workflows: int
    categories: int
    tags: int