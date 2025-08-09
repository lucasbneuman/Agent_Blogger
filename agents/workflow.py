from langgraph.graph import StateGraph, END
from agents.state import ArticleState
from agents.supervisor import supervisor_node, workflow_validator_node, decision_router
from agents.nodes.selector import article_selector_node, keyword_selector_node
from agents.nodes.content_creator import content_creator_node, title_creator_node, meta_description_creator_node
from agents.nodes.categorizer import categorizer_node
from agents.nodes.image_creator import image_creator_node
from agents.nodes.internal_links import internal_links_node
from agents.nodes.cta_creator import cta_creator_node
from agents.nodes.reviewer import reviewer_node, quality_checker_node
from agents.nodes.wordpress_publisher import wordpress_publisher_node, article_assembler_node

# Wrapper limpio para WordPress publisher
def wordpress_publisher_with_logging(state):
    import sys
    print(f"\n=== PUBLICANDO: {state.get('category')} | Tags: {len(state.get('tags', []))} ===", flush=True)
    sys.stdout.flush()
    
    result = wordpress_publisher_node(state)
    
    if result.get('wordpress_id'):
        print(f"=== PUBLICADO: ID {result.get('wordpress_id')} ===\n", flush=True)
    else:
        print(f"=== ERROR EN PUBLICACION ===\n", flush=True)
    sys.stdout.flush()
    
    return result
from datetime import datetime, timezone
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_article_workflow() -> StateGraph:
    """
    Crea el workflow completo de LangGraph para la generación de artículos.
    """
    
    # Crear el grafo de estado
    workflow = StateGraph(ArticleState)
    
    # Agregar nodos al workflow
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("workflow_validator", workflow_validator_node)
    workflow.add_node("article_selector", article_selector_node)
    workflow.add_node("keyword_selector", keyword_selector_node)
    workflow.add_node("content_creator", content_creator_node)
    workflow.add_node("title_creator", title_creator_node)
    workflow.add_node("meta_description_creator", meta_description_creator_node)
    workflow.add_node("categorizer", categorizer_node)
    workflow.add_node("image_creator", image_creator_node)
    workflow.add_node("internal_links", internal_links_node)
    workflow.add_node("cta_creator", cta_creator_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("quality_checker", quality_checker_node)
    workflow.add_node("article_assembler", article_assembler_node)
    workflow.add_node("wordpress_publisher", wordpress_publisher_with_logging)
    
    # Definir el punto de entrada
    workflow.set_entry_point("supervisor")
    
    # Definir las transiciones condicionales desde el supervisor
    workflow.add_conditional_edges(
        "supervisor",
        decision_router,
        {
            "article_selector": "article_selector",
            "keyword_selector": "keyword_selector", 
            "content_creator": "content_creator",
            "internal_links": "internal_links",
            "title_creator": "title_creator",
            "cta_creator": "cta_creator",
            "categorizer": "categorizer",
            "meta_description_creator": "meta_description_creator",
            "image_creator": "image_creator",
            "article_assembler": "article_assembler",
            "reviewer": "reviewer",
            "quality_checker": "quality_checker",
            "wordpress_publisher": "wordpress_publisher",
            "END": END
        }
    )
    
    # Todas las operaciones regresan al supervisor para coordinación
    nodes_to_supervisor = [
        "article_selector", "keyword_selector", "content_creator",
        "title_creator", "meta_description_creator", "categorizer",
        "image_creator", "internal_links", "cta_creator",
        "reviewer", "quality_checker", "article_assembler",
        "wordpress_publisher"
    ]
    
    for node in nodes_to_supervisor:
        workflow.add_edge(node, "supervisor")
    
    # Compilar el workflow con límite de recursión más alto
    compiled_workflow = workflow.compile()
    compiled_workflow.config = {"recursion_limit": 50}
    return compiled_workflow

def initialize_article_state() -> ArticleState:
    """
    Inicializa el estado del artículo con valores por defecto.
    """
    
    return ArticleState(
        # Selección inicial
        selected_keyword=None,
        selected_stage=None,
        
        # Contenido del artículo
        title=None,
        content=None,
        meta_description=None,
        
        # Categorización
        category=None,
        tags=None,
        
        # Imagen destacada
        featured_image_prompt=None,
        featured_image_url=None,
        featured_image_alt=None,
        
        # Enlaces internos
        internal_links=None,
        
        # CTA
        cta_title=None,
        cta_content=None,
        cta_link=None,
        
        # Estado del proceso
        errors=None,
        warnings=None,
        current_step='start',
        supervisor_decision=None,
        retry_count=0,
        skip_wordpress_publishing=False,
        is_complete=False,
        needs_revision=False,
        
        # WordPress
        wordpress_id=None,
        is_published=False,
        
        # Ideas de Telegram
        telegram_idea=None,
        telegram_idea_mode=False,
        
        # Metadatos
        created_at=datetime.now(timezone.utc),
        processing_log=["Workflow iniciado"],
        last_supervisor_check=None,
        workflow_validations=None
    )

async def run_article_generation() -> ArticleState:
    """
    Ejecuta el workflow completo de generación de artículos.
    """
    
    logger.info("Iniciando generación de artículo")
    
    # Crear workflow
    workflow = create_article_workflow()
    
    # Inicializar estado
    initial_state = initialize_article_state()
    
    try:
        # Ejecutar workflow
        final_state = workflow.invoke(initial_state)
        
        logger.info(f"Workflow completado. Estado final: {final_state.get('current_step')}")
        
        return final_state
        
    except Exception as e:
        logger.error(f"Error en workflow: {str(e)}")
        
        # Retornar estado con error
        error_state = initial_state.copy()
        error_state.update({
            'errors': [f"Error en workflow: {str(e)}"],
            'current_step': 'workflow_error',
            'is_complete': True
        })
        
        return error_state

def run_article_generation_sync() -> ArticleState:
    """
    Versión síncrona del generador de artículos.
    """
    
    logger.info("Iniciando generación de artículo (síncrono)")
    
    # Crear workflow
    workflow = create_article_workflow()
    
    # Inicializar estado
    initial_state = initialize_article_state()
    
    try:
        # Ejecutar workflow
        final_state = workflow.invoke(initial_state)
        
        logger.info(f"Workflow completado. Estado final: {final_state.get('current_step')}")
        
        return final_state
        
    except Exception as e:
        logger.error(f"Error en workflow: {str(e)}")
        
        # Retornar estado con error
        error_state = initial_state.copy()
        error_state.update({
            'errors': [f"Error en workflow: {str(e)}"],
            'current_step': 'workflow_error',
            'is_complete': True
        })
        
        return error_state

def run_article_generation_sync_with_idea(idea_text: str) -> ArticleState:
    """
    Versión síncrona del generador de artículos basado en una idea de Telegram.
    """
    
    logger.info(f"Iniciando generación de artículo con idea: {idea_text[:100]}...")
    
    # Crear workflow
    workflow = create_article_workflow()
    
    # Inicializar estado con la idea
    initial_state = initialize_article_state()
    initial_state.update({
        'telegram_idea': idea_text,
        'telegram_idea_mode': True,
        'processing_log': [f"Workflow iniciado con idea de Telegram: {idea_text[:50]}..."]
    })
    
    try:
        # Ejecutar workflow
        final_state = workflow.invoke(initial_state)
        
        logger.info(f"Workflow con idea completado. Estado final: {final_state.get('current_step')}")
        
        return final_state
        
    except Exception as e:
        logger.error(f"Error en workflow con idea: {str(e)}")
        
        # Retornar estado con error
        error_state = initial_state.copy()
        error_state.update({
            'errors': [f"Error en workflow: {str(e)}"],
            'current_step': 'workflow_error',
            'is_complete': True
        })
        
        return error_state

def continue_workflow_from_state(current_state: ArticleState) -> ArticleState:
    """
    Continúa el workflow desde un estado específico hasta completar.
    Usado principalmente para procesar aprobaciones de Telegram.
    """
    
    logger.info(f"Continuando workflow desde estado: {current_state.get('current_step')}")
    
    # Crear workflow
    workflow = create_article_workflow()
    
    try:
        # Continuar workflow desde estado actual
        final_state = workflow.invoke(current_state)
        
        logger.info(f"Workflow continuado completado. Estado final: {final_state.get('current_step')}")
        
        return final_state
        
    except Exception as e:
        logger.error(f"Error continuando workflow: {str(e)}")
        
        # Retornar estado con error
        error_state = current_state.copy()
        error_state.update({
            'errors': current_state.get('errors', []) + [f"Error continuando workflow: {str(e)}"],
            'current_step': 'workflow_continuation_error',
            'is_complete': True
        })
        
        return error_state

if __name__ == "__main__":
    # Test del workflow
    import asyncio
    
    # Inicializar base de datos
    from database import init_db
    init_db()
    
    # Ejecutar workflow de prueba
    result = run_article_generation_sync()
    
    print("=== RESULTADO DEL WORKFLOW ===")
    print(f"Estado final: {result.get('current_step')}")
    print(f"Completado: {result.get('is_complete')}")
    print(f"Errores: {result.get('errors', [])}")
    print(f"Warnings: {result.get('warnings', [])}")
    
    if result.get('title'):
        print(f"Título: {result.get('title')}")
    
    if result.get('selected_keyword'):
        print(f"Keyword: {result.get('selected_keyword')}")
    
    print(f"\nLog del proceso:")
    for log in result.get('processing_log', []):
        print(f"- {log}")