from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime

class ArticleState(TypedDict):
    """Estado compartido del artículo a través de todos los nodos"""
    
    # Selección inicial
    selected_keyword: Optional[str]
    selected_stage: Optional[str]  # conciencia, consideracion, compra
    
    # Contenido del artículo
    title: Optional[str]
    content: Optional[str]
    meta_description: Optional[str]
    
    # Categorización
    category: Optional[str]
    tags: Optional[List[str]]
    
    # Imagen destacada
    featured_image_prompt: Optional[str]
    featured_image_url: Optional[str]
    featured_image_alt: Optional[str]
    
    # Enlaces internos
    internal_links: Optional[List[Dict[str, str]]]  # [{"url": "", "anchor": "", "context": ""}]
    
    # CTA
    cta_title: Optional[str]
    cta_content: Optional[str]
    cta_link: Optional[str]
    
    # Estado del proceso
    errors: Optional[List[str]]
    warnings: Optional[List[str]]
    current_step: Optional[str]
    is_complete: bool
    needs_revision: bool
    supervisor_decision: Optional[str]
    retry_count: int
    skip_wordpress_publishing: bool
    
    # WordPress
    wordpress_id: Optional[int]
    is_published: bool
    
    # Metadatos
    created_at: datetime
    processing_log: Optional[List[str]]
    last_supervisor_check: Optional[datetime]
    workflow_validations: Optional[List[str]]