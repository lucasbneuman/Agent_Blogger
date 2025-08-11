from typing import Dict, Any
from sqlalchemy.orm import Session
from database import get_db, Keyword
from agents.state import ArticleState
import random
from datetime import datetime
import openai
import os

def generate_seo_keyword_from_idea(telegram_idea: str) -> str:
    """
    Genera una keyword SEO optimizada basada en la idea de Telegram
    """
    
    client = openai.OpenAI()
    
    prompt = f"""
Analiza esta idea de artículo y genera UNA keyword SEO específica y optimizada:

IDEA DEL USUARIO: {telegram_idea}

INSTRUCCIONES:
1. Identifica el tema principal y el público objetivo
2. Crea una keyword de 3-6 palabras que sea:
   - Específica y relevante al tema
   - Optimizada para SEO (incluir términos de búsqueda)
   - Orientada a Argentina cuando sea relevante
   - Enfocada en la intención de búsqueda del usuario

3. La keyword debe ser algo que la gente buscaría en Google

EJEMPLOS:
- Idea: "IA para restaurantes" → Keyword: "inteligencia artificial restaurantes Argentina"
- Idea: "automatizar contabilidad pymes" → Keyword: "software contabilidad automatizada pymes"
- Idea: "marketing digital consultoría" → Keyword: "servicios marketing digital empresas"

RESPONDE SOLO CON LA KEYWORD (sin comillas ni explicaciones):
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un experto en SEO que genera keywords específicas y optimizadas."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.3
        )
        
        keyword = response.choices[0].message.content.strip()
        
        # Limpiar la respuesta por si incluye comillas o texto extra
        keyword = keyword.replace('"', '').replace("'", "").strip()
        
        # Si la keyword es muy larga, truncarla
        if len(keyword) > 80:
            keyword = keyword[:80]
        
        return keyword
        
    except Exception as e:
        # Fallback: extraer términos clave de la idea original
        import re
        
        # Remover palabras comunes
        stop_words = ['el', 'la', 'de', 'que', 'y', 'a', 'un', 'una', 'para', 'con', 'por', 'como', 'sobre', 'en']
        
        # Extraer palabras importantes
        words = re.findall(r'\b\w+\b', telegram_idea.lower())
        important_words = [w for w in words if len(w) > 3 and w not in stop_words]
        
        # Tomar las primeras 4 palabras más importantes
        keyword = ' '.join(important_words[:4])
        
        return keyword if keyword else telegram_idea[:50]

def article_selector_node(state: ArticleState) -> Dict[str, Any]:
    """
    Nodo para seleccionar qué artículo escribir.
    Si hay una idea de Telegram, la usa. Si no, usa keywords y equilibrio de etapas.
    """
    
    processing_log = state.get('processing_log', [])
    
    # Verificar si hay una idea de Telegram
    if state.get('telegram_idea_mode') and state.get('telegram_idea'):
        processing_log.append("* Procesando idea de Telegram para generar keyword SEO")
        
        try:
            # Generar keyword SEO optimizada basada en la idea
            telegram_idea = state['telegram_idea']
            selected_keyword = generate_seo_keyword_from_idea(telegram_idea)
            
            # Para artículos con ideas de Telegram, usar etapa de consideración por defecto
            # ya que normalmente las ideas son sobre servicios/productos específicos
            selected_stage = 'consideracion'
            
            new_state = state.copy()
            new_state.update({
                'selected_keyword': selected_keyword,
                'selected_stage': selected_stage,
                'current_step': 'keyword_selected',
                'processing_log': processing_log + [
                    f"* Idea original: {telegram_idea[:100]}...",
                    f"* Keyword SEO generada: {selected_keyword}"
                ],
                'supervisor_decision': 'validate_keyword'
            })
            
            return new_state
            
        except Exception as e:
            # Si falla la generación de keyword, usar la idea original como fallback
            processing_log.append(f"* Error generando keyword SEO: {str(e)}")
            processing_log.append("* Usando idea original como keyword")
            
            selected_stage = 'consideracion'
            selected_keyword = state['telegram_idea']
            
            new_state = state.copy()
            new_state.update({
                'selected_keyword': selected_keyword,
                'selected_stage': selected_stage,
                'current_step': 'keyword_selected',
                'processing_log': processing_log + [f"* Keyword (fallback): {selected_keyword[:100]}..."],
                'supervisor_decision': 'validate_keyword'
            })
            
            return new_state
    
    # Flujo normal con base de datos de keywords
    processing_log.append("* Seleccionando keyword automaticamente desde base de datos")
    
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
            # Si no hay keywords disponibles, resetear todas las keywords de esta etapa
            print(f"No hay keywords disponibles para {selected_stage}, reseteando...")
            reset_keywords = db.query(Keyword).filter(Keyword.stage == selected_stage).all()
            for kw in reset_keywords:
                kw.is_used = False
            db.commit()
            
            # Volver a buscar
            available_keywords = db.query(Keyword).filter(
                Keyword.stage == selected_stage,
                Keyword.is_used == False
            ).order_by(Keyword.priority.desc()).all()
        
        if available_keywords:
            # MEJORADO: Selección más diversa en lugar de siempre la primera
            
            # Agrupar keywords por prioridad
            high_priority = [kw for kw in available_keywords if kw.priority >= 4]
            medium_priority = [kw for kw in available_keywords if kw.priority == 3]
            low_priority = [kw for kw in available_keywords if kw.priority <= 2]
            
            # Selección ponderada: 60% alta prioridad, 30% media, 10% baja
            selection_pool = []
            if high_priority:
                selection_pool.extend(high_priority * 6)  # 60% probabilidad
            if medium_priority:
                selection_pool.extend(medium_priority * 3)  # 30% probabilidad  
            if low_priority:
                selection_pool.extend(low_priority * 1)   # 10% probabilidad
            
            # Si no hay pool, usar todas las disponibles
            if not selection_pool:
                selection_pool = available_keywords
                
            # Seleccionar aleatoriamente del pool ponderado
            selected_keyword_obj = random.choice(selection_pool)
            selected_keyword = selected_keyword_obj.keyword
            
            # Marcar como usado
            selected_keyword_obj.is_used = True
            db.commit()
            
            print(f"Keyword seleccionada: '{selected_keyword}' (prioridad: {selected_keyword_obj.priority})")
        else:
            # Fallback final si algo falla
            fallback_keywords = {
                'conciencia': 'beneficios de la IA en empresas',
                'consideracion': 'servicios de consultoría IA',
                'compra': 'contratar consultor IA'
            }
            selected_keyword = fallback_keywords[selected_stage]
            print(f"Usando keyword fallback: '{selected_keyword}'")
        
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