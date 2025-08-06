from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from database import get_db, init_db
from database.models import Article, Keyword, Category, Tag
from agents.workflow import run_article_generation_sync
from api.models import ArticleResponse, KeywordCreate, ArticleCreate, WorkflowStatus

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Agent Blogger API",
    description="API para generar y gestionar artículos de blog con IA",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Almacenar estado de workflows en ejecución
active_workflows = {}

@app.on_event("startup")
async def startup_event():
    """Inicializar base de datos al arrancar la aplicación"""
    logger.info("Inicializando base de datos...")
    init_db()
    logger.info("Base de datos inicializada")

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "Agent Blogger API",
        "version": "1.0.0",
        "description": "API para generar artículos de blog con IA",
        "endpoints": {
            "articles": "/articles",
            "generate": "/generate",
            "keywords": "/keywords",
            "categories": "/categories",
            "status": "/status"
        }
    }

@app.get("/articles", response_model=List[ArticleResponse])
async def get_articles(
    skip: int = 0, 
    limit: int = 10,
    stage: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Obtener lista de artículos"""
    query = db.query(Article)
    
    if stage:
        query = query.filter(Article.stage == stage)
    
    articles = query.offset(skip).limit(limit).all()
    return articles

@app.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """Obtener un artículo específico"""
    article = db.query(Article).filter(Article.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    
    return article

@app.post("/generate")
async def generate_article(background_tasks: BackgroundTasks):
    """
    Generar un nuevo artículo usando el workflow de IA.
    Ejecuta en background y retorna ID de seguimiento.
    """
    
    # Generar ID único para el workflow
    workflow_id = f"workflow_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    # Inicializar estado del workflow
    active_workflows[workflow_id] = {
        "status": "starting",
        "created_at": datetime.utcnow(),
        "progress": 0,
        "current_step": "initializing",
        "result": None,
        "errors": []
    }
    
    # Ejecutar workflow en background
    background_tasks.add_task(run_article_workflow, workflow_id)
    
    return {
        "workflow_id": workflow_id,
        "status": "started",
        "message": "Generación de artículo iniciada",
        "check_status_url": f"/status/{workflow_id}"
    }

@app.get("/status/{workflow_id}", response_model=WorkflowStatus)
async def get_workflow_status(workflow_id: str):
    """Obtener estado de un workflow en ejecución"""
    
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")
    
    workflow_data = active_workflows[workflow_id]
    
    return WorkflowStatus(
        workflow_id=workflow_id,
        status=workflow_data["status"],
        progress=workflow_data["progress"],
        current_step=workflow_data["current_step"],
        created_at=workflow_data["created_at"],
        errors=workflow_data["errors"],
        result=workflow_data["result"]
    )

@app.post("/generate/sync")
async def generate_article_sync():
    """
    Generar artículo de forma síncrona (para testing).
    ATENCIÓN: Puede tomar varios minutos en completarse.
    """
    
    try:
        logger.info("Iniciando generación síncrona de artículo")
        
        # Ejecutar workflow
        result = run_article_generation_sync()
        
        return {
            "status": "completed" if result.get('is_complete') else "failed",
            "current_step": result.get('current_step'),
            "errors": result.get('errors', []),
            "warnings": result.get('warnings', []),
            "article_data": {
                "title": result.get('title'),
                "keyword": result.get('selected_keyword'),
                "stage": result.get('selected_stage'),
                "category": result.get('category'),
                "wordpress_id": result.get('wordpress_id'),
                "is_published": result.get('is_published', False)
            },
            "processing_log": result.get('processing_log', [])
        }
        
    except Exception as e:
        logger.error(f"Error en generación síncrona: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/keywords", response_model=List[dict])
async def get_keywords(
    stage: Optional[str] = None,
    unused_only: bool = False,
    db: Session = Depends(get_db)
):
    """Obtener lista de keywords"""
    query = db.query(Keyword)
    
    if stage:
        query = query.filter(Keyword.stage == stage)
    
    if unused_only:
        query = query.filter(Keyword.is_used == False)
    
    keywords = query.order_by(Keyword.priority.desc()).all()
    
    return [
        {
            "id": k.id,
            "keyword": k.keyword,
            "stage": k.stage,
            "priority": k.priority,
            "is_used": k.is_used
        }
        for k in keywords
    ]

@app.post("/keywords")
async def create_keyword(keyword_data: KeywordCreate, db: Session = Depends(get_db)):
    """Crear nueva keyword"""
    
    # Verificar que no exista
    existing = db.query(Keyword).filter(Keyword.keyword == keyword_data.keyword).first()
    if existing:
        raise HTTPException(status_code=400, detail="Keyword ya existe")
    
    # Crear keyword
    new_keyword = Keyword(
        keyword=keyword_data.keyword,
        stage=keyword_data.stage,
        priority=keyword_data.priority
    )
    
    db.add(new_keyword)
    db.commit()
    db.refresh(new_keyword)
    
    return {
        "id": new_keyword.id,
        "keyword": new_keyword.keyword,
        "stage": new_keyword.stage,
        "priority": new_keyword.priority,
        "message": "Keyword creada exitosamente"
    }

@app.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Obtener lista de categorías"""
    categories = db.query(Category).all()
    
    return [
        {
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "article_count": len(cat.articles)
        }
        for cat in categories
    ]

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Obtener estadísticas del sistema"""
    
    # Contar artículos por etapa
    stage_counts = {}
    for stage in ['conciencia', 'consideracion', 'compra']:
        count = db.query(Article).filter(Article.stage == stage).count()
        stage_counts[stage] = count
    
    # Estadísticas generales
    total_articles = db.query(Article).count()
    published_articles = db.query(Article).filter(Article.is_published == True).count()
    total_keywords = db.query(Keyword).count()
    unused_keywords = db.query(Keyword).filter(Keyword.is_used == False).count()
    
    return {
        "articles": {
            "total": total_articles,
            "published": published_articles,
            "by_stage": stage_counts
        },
        "keywords": {
            "total": total_keywords,
            "unused": unused_keywords
        },
        "active_workflows": len(active_workflows),
        "categories": db.query(Category).count(),
        "tags": db.query(Tag).count()
    }

@app.delete("/workflows/{workflow_id}")
async def cancel_workflow(workflow_id: str):
    """Cancelar un workflow en ejecución"""
    
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")
    
    # Marcar como cancelado
    active_workflows[workflow_id]["status"] = "cancelled"
    
    return {"message": "Workflow cancelado"}

async def run_article_workflow(workflow_id: str):
    """
    Función para ejecutar el workflow en background.
    Actualiza el estado del workflow mientras se ejecuta.
    """
    
    try:
        # Actualizar estado
        active_workflows[workflow_id]["status"] = "running"
        active_workflows[workflow_id]["current_step"] = "starting_workflow"
        active_workflows[workflow_id]["progress"] = 10
        
        # Ejecutar workflow
        result = run_article_generation_sync()
        
        # Actualizar con resultado
        if result.get('is_complete') and not result.get('errors'):
            active_workflows[workflow_id]["status"] = "completed"
            active_workflows[workflow_id]["progress"] = 100
        else:
            active_workflows[workflow_id]["status"] = "failed"
            active_workflows[workflow_id]["errors"] = result.get('errors', [])
        
        active_workflows[workflow_id]["current_step"] = result.get('current_step', 'unknown')
        active_workflows[workflow_id]["result"] = {
            "title": result.get('title'),
            "keyword": result.get('selected_keyword'),
            "stage": result.get('selected_stage'),
            "wordpress_id": result.get('wordpress_id'),
            "is_published": result.get('is_published', False)
        }
        
    except Exception as e:
        logger.error(f"Error en workflow {workflow_id}: {str(e)}")
        active_workflows[workflow_id]["status"] = "error"
        active_workflows[workflow_id]["errors"] = [str(e)]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)