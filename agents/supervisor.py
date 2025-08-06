from typing import Dict, Any, List
from agents.state import ArticleState
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

def supervisor_node(state: ArticleState) -> Dict[str, Any]:
    """
    Nodo supervisor que coordina el flujo de trabajo y toma decisiones.
    Determina el próximo paso basado en el estado actual.
    """
    
    errors_list = state.get('errors') or []
    logger.info(f"Supervisor node iniciando - current_step: {state.get('current_step', 'start')}, needs_revision: {state.get('needs_revision', False)}, errors: {len(errors_list)}, retry_count: {state.get('retry_count', 0)}")
    
    current_step = state.get('current_step', 'start')
    errors = state.get('errors', [])
    needs_revision = state.get('needs_revision', False)
    retry_count = state.get('retry_count', 0)
    
    # Log del estado actual
    processing_log = state.get('processing_log', [])
    processing_log.append(f"Supervisor evaluando paso: {current_step}")
    
    # Mapa de flujo de trabajo
    workflow_map = {
        'start': 'select_article',
        'keyword_selected': 'validate_keyword',
        'keyword_validated': 'create_content',
        'content_created': 'create_internal_links',
        'internal_links_created': 'create_title',
        'title_created': 'create_cta',
        'cta_created': 'categorize',
        'categorized': 'create_meta_description',
        'meta_created': 'create_image',
        'image_created': 'assemble_article',
        'assembled': 'review_article',
        'review_approved': 'quality_check',
        'quality_checked': 'publish_article',
        'published': 'complete',
        'published_draft': 'complete'
    }
    
    # Manejo especial para quality_checked loop infinito
    if needs_revision and current_step == 'quality_checked':
        # Limitar reintentos para evitar loops infinitos en quality check
        if retry_count >= 2:
            next_step = 'publish_article'  # Continuar con publicación a pesar de warnings menores
            processing_log.append(f"Quality check con warnings menores ({retry_count} reintentos), continuando con publicación")
        else:
            next_step = 'quality_check'
            processing_log.append("Re-verificando calidad")
    
    # Manejo de revisión necesaria (prioridad sobre errores generales)
    elif needs_revision and current_step == 'review_failed':
        # Limitar reintentos para evitar loops infinitos
        if retry_count >= 2:
            next_step = 'abort'
            processing_log.append(f"Demasiados reintentos de revisión ({retry_count}), abortando")
        else:
            next_step = 'fix_content'
            processing_log.append("Artículo necesita correcciones")
    
    # Manejo de errores
    elif errors:
        if current_step.endswith('_error'):
            # Ya estamos en un estado de error, determinar si es recuperable
            if len(errors) > 3:
                next_step = 'abort'
                processing_log.append("Demasiados errores, abortando proceso")
            else:
                # Intentar recuperar basado en el tipo de error
                next_step = determine_recovery_step(current_step, errors)
                processing_log.append(f"Intentando recuperar del error: {next_step}")
        else:
            # Primer error en este paso
            next_step = f"{current_step}_retry"
            processing_log.append(f"Error detectado, programando reintento: {next_step}")
    
    # Manejo de otros casos de revisión necesaria
    elif needs_revision:
        next_step = 'review_article'
        processing_log.append("Enviando a revisión")
    
    # Flujo normal
    else:
        next_step = workflow_map.get(current_step, 'unknown')
        if next_step == 'unknown':
            processing_log.append(f"Paso desconocido: {current_step}")
            next_step = 'error'
    
    # Actualizar retry_count si es un retry
    updated_retry_count = retry_count
    if next_step.endswith('_retry') or (current_step == 'review_failed' and next_step == 'fix_content'):
        updated_retry_count = retry_count + 1
        processing_log.append(f"Incrementando contador de reintentos: {updated_retry_count}")
    
    # Lógica especial: después de fix_content, ir directo a ensamblar y revisar
    if current_step == 'content_created' and retry_count > 0:
        next_step = 'assemble_article'
        processing_log.append("Contenido corregido, saltando a ensamblado para re-revisión")
    
    # Actualizar estado con decisión del supervisor
    new_state = state.copy()
    new_state.update({
        'supervisor_decision': next_step,
        'processing_log': processing_log,
        'last_supervisor_check': datetime.now(timezone.utc),
        'retry_count': updated_retry_count
    })
    
    # Casos especiales
    if next_step == 'complete':
        new_state.update({
            'is_complete': True,
            'current_step': 'completed'
        })
    elif next_step == 'abort':
        new_state.update({
            'is_complete': True,
            'current_step': 'aborted',
            'errors': errors + ['Proceso abortado por supervisor']
        })
    
    return new_state

def determine_recovery_step(error_step: str, errors: List[str]) -> str:
    """
    Determina el paso de recuperación basado en el tipo de error.
    """
    
    recovery_map = {
        'selector_error': 'select_article',
        'keyword_error': 'select_article',
        'content_error': 'create_content',
        'title_error': 'create_title',
        'categorizer_error': 'categorize',
        'image_error': 'skip_image',  # La imagen no es crítica
        'internal_links_error': 'create_title',  # Continuar sin enlaces internos
        'cta_error': 'create_meta_description',  # CTA no es crítico
        'meta_error': 'create_image',  # Continuar sin meta descripción
        'review_error': 'assemble_article',  # Re-ensamblar y revisar
        'assembly_error': 'review_article',
        'publish_error': 'save_draft'  # Guardar como borrador si no se puede publicar
    }
    
    return recovery_map.get(error_step, 'restart')

def workflow_validator_node(state: ArticleState) -> Dict[str, Any]:
    """
    Nodo para validar que el flujo de trabajo esté progresando correctamente.
    """
    
    processing_log = state.get('processing_log', [])
    current_step = state.get('current_step', 'start')
    
    # Validaciones básicas
    validations = []
    
    # Validar que el estado tenga timestamp
    if not state.get('created_at'):
        validations.append("Falta timestamp de creación")
    
    # Validar progreso del workflow
    if current_step == 'start' and not state.get('selected_keyword'):
        validations.append("Proceso iniciado correctamente")
    
    # Validar dependencias por paso
    step_requirements = {
        'keyword_validated': ['selected_keyword', 'selected_stage'],
        'content_created': ['selected_keyword', 'content'],
        'title_created': ['content', 'title'],
        'categorized': ['title', 'category', 'tags'],
        'meta_created': ['title', 'meta_description'],
        'review_approved': ['title', 'content', 'meta_description', 'category'],
        'assembled': ['title', 'content', 'meta_description', 'category', 'tags']
    }
    
    requirements = step_requirements.get(current_step, [])
    missing_requirements = [req for req in requirements if not state.get(req)]
    
    if missing_requirements:
        validations.append(f"Faltan requisitos para {current_step}: {', '.join(missing_requirements)}")
    
    # Actualizar log
    processing_log.append("Validación de workflow completada")
    if validations:
        processing_log.extend(validations)
    
    new_state = state.copy()
    new_state.update({
        'processing_log': processing_log,
        'workflow_validations': validations,
        'current_step': f"{current_step}_validated" if not missing_requirements else f"{current_step}_validation_failed"
    })
    
    return new_state

def decision_router(state: ArticleState) -> str:
    """
    Router que determina el siguiente nodo basado en el estado actual.
    Utilizado por LangGraph para routing condicional.
    """
    
    current_step = state.get('current_step', 'start')
    supervisor_decision = state.get('supervisor_decision')
    
    logger.info(f"Decision router - current_step: {current_step}, supervisor_decision: {supervisor_decision}")
    
    # Si el supervisor ha tomado una decisión, usarla
    if supervisor_decision:
        routing_map = {
            'select_article': 'article_selector',
            'validate_keyword': 'keyword_selector',
            'create_content': 'content_creator',
            'create_internal_links': 'internal_links',
            'create_title': 'title_creator',
            'create_cta': 'cta_creator',
            'categorize': 'categorizer',
            'create_meta_description': 'meta_description_creator',
            'create_image': 'image_creator',
            'assemble_article': 'article_assembler',
            'review_article': 'reviewer',
            'quality_check': 'quality_checker',
            'publish_article': 'wordpress_publisher',
            'complete': 'END',
            'abort': 'END',
            'published_draft': 'END',
            'save_draft': 'END',
            
            # Casos de retry
            'start_retry': 'article_selector',
            'keyword_selected_retry': 'keyword_selector',
            'keyword_validated_retry': 'content_creator',
            'content_created_retry': 'content_creator',
            'internal_links_created_retry': 'internal_links',
            'title_created_retry': 'title_creator',
            'cta_created_retry': 'cta_creator',
            'categorized_retry': 'categorizer',
            'meta_created_retry': 'meta_description_creator',
            'image_created_retry': 'image_creator',
            'assembled_retry': 'article_assembler',
            'review_approved_retry': 'reviewer',
            'review_failed_retry': 'reviewer',
            'quality_checked_retry': 'quality_checker',
            
            # Casos especiales
            'fix_content': 'content_creator'
        }
        
        return routing_map.get(supervisor_decision, 'supervisor')
    
    # Routing por defecto basado en current_step
    if current_step in ['completed', 'aborted', 'published_draft']:
        logger.info(f"Decision router - Terminando workflow en {current_step}")
        return 'END'
    elif 'error' in current_step:
        logger.info(f"Decision router - Error detectado en {current_step}, volviendo a supervisor")
        return 'supervisor'
    else:
        logger.info(f"Decision router - Estado no reconocido: {current_step}, volviendo a supervisor")
        return 'supervisor'