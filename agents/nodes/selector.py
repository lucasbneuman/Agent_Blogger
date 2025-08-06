from typing import Dict, Any
from sqlalchemy.orm import Session
from database import get_db, Keyword
from agents.state import ArticleState
import random
from datetime import datetime

def article_selector_node(state: ArticleState) -> Dict[str, Any]:
    """
    Nodo para seleccionar qué artículo escribir basado en keywords y equilibrio de etapas.
    Mantiene equilibrio entre conciencia, consideración y compra.
    """
    
    # Obtener base de datos
    db = next(get_db())
    
    try:
        # Contar artículos por etapa para mantener equilibrio
        from database.models import Article
        stage_counts = {}
        for stage in ['conciencia', 'consideracion', 'compra']:
            count = db.query(Article).filter(Article.stage == stage).count()
            stage_counts[stage] = count
        
        # Determinar qué etapa necesita más artículos
        min_count = min(stage_counts.values())
        stages_needed = [stage for stage, count in stage_counts.items() if count == min_count]
        
        # Si hay empate, seleccionar aleatoriamente
        selected_stage = random.choice(stages_needed)
        
        # Obtener keywords disponibles para la etapa seleccionada
        available_keywords = db.query(Keyword).filter(
            Keyword.stage == selected_stage,
            Keyword.is_used == False
        ).order_by(Keyword.priority.desc()).all()
        
        if not available_keywords:
            # Si no hay keywords disponibles, crear una de ejemplo
            fallback_keywords = {
                'conciencia': 'beneficios de la IA en empresas',
                'consideracion': 'servicios de consultoría IA',
                'compra': 'contratar consultor IA'
            }
            selected_keyword = fallback_keywords[selected_stage]
        else:
            # Seleccionar keyword con mayor prioridad
            selected_keyword = available_keywords[0].keyword
            # Marcar como usado
            available_keywords[0].is_used = True
            db.commit()
        
        # Actualizar estado
        new_state = state.copy()
        new_state.update({
            'selected_keyword': selected_keyword,
            'selected_stage': selected_stage,
            'current_step': 'keyword_selected',
            'created_at': datetime.utcnow(),
            'processing_log': [f"Keyword seleccionada: {selected_keyword} (etapa: {selected_stage})"],
            'errors': [],
            'warnings': []
        })
        
        return new_state
        
    except Exception as e:
        error_msg = f"Error en selector de artículo: {str(e)}"
        new_state = state.copy()
        new_state.update({
            'errors': [error_msg],
            'current_step': 'selector_error'
        })
        return new_state
        
    finally:
        db.close()

def keyword_selector_node(state: ArticleState) -> Dict[str, Any]:
    """
    Nodo para refinar y validar la selección de palabra clave principal.
    Este nodo se ejecuta después del selector de artículo.
    """
    
    if not state.get('selected_keyword'):
        new_state = state.copy()
        new_state.update({
            'errors': ['No se ha seleccionado keyword'],
            'current_step': 'keyword_error'
        })
        return new_state
    
    # Validar y refinar la keyword
    keyword = state['selected_keyword']
    stage = state['selected_stage']
    
    # Log del proceso
    processing_log = state.get('processing_log', [])
    processing_log.append(f"Keyword validada: {keyword}")
    
    new_state = state.copy()
    new_state.update({
        'selected_keyword': keyword,
        'current_step': 'keyword_validated',
        'processing_log': processing_log
    })
    
    return new_state