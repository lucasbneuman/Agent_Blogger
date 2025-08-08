from typing import Dict, Any, List
from agents.state import ArticleState
from openai import OpenAI
from database import get_db
from database.models import Category, Tag
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def categorizer_node(state: ArticleState) -> Dict[str, Any]:
    """
    Nodo para seleccionar categoría y crear etiquetas para el artículo.
    """
    
    title = state.get('title')
    content = state.get('content')
    keyword = state.get('selected_keyword')
    
    if not all([title, content, keyword]):
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + ['Faltan título, contenido o keyword para categorización'],
            'current_step': 'categorizer_error'
        })
        return new_state
    
    # Obtener categorías disponibles de la base de datos - CON DEBUGGING FORZADO
    import sys
    print(f"*** CATEGORIZER: INICIANDO ***", flush=True)
    sys.stdout.flush()
    
    db = next(get_db())
    
    try:
        categories = db.query(Category).all()
        category_list = [cat.name for cat in categories]
        
        print(f"*** CATEGORIZER DEBUG ***", flush=True)
        print(f"  Total categories in DB: {len(categories)}", flush=True)
        print(f"  Categories found: {category_list}", flush=True)
        for cat in categories:
            print(f"    - {cat.name} -> WP ID: {cat.wordpress_id}", flush=True)
        sys.stdout.flush()
        
        prompt = f"""
        Analiza este artículo y selecciona la categoría más apropiada y crea etiquetas relevantes.
        
        TÍTULO: {title}
        KEYWORD: {keyword}
        
        CATEGORÍAS DISPONIBLES:
        {chr(10).join([f"- {cat}" for cat in category_list])}
        
        TAREAS:
        1. Selecciona LA categoría más apropiada de la lista
        2. Crea 3-5 etiquetas relevantes (en minúsculas, separadas por comas)
        
        CRITERIOS PARA ETIQUETAS:
        - Relacionadas con el contenido específico
        - Términos que los usuarios podrían buscar
        - Incluir variaciones de la keyword principal
        - Máximo 2-3 palabras por etiqueta
        - Todo en minúsculas
        
        FORMATO DE RESPUESTA:
        Categoría: [nombre exacto de la categoría]
        Etiquetas: etiqueta1, etiqueta2, etiqueta3, etiqueta4
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parsear respuesta
        lines = result.split('\n')
        category = None
        tags = []
        
        for line in lines:
            if line.startswith('Categoría:'):
                category = line.replace('Categoría:', '').strip()
            elif line.startswith('Etiquetas:'):
                tags_str = line.replace('Etiquetas:', '').strip()
                tags = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]
        
        # Validar categoría
        if category not in category_list:
            category = category_list[0]  # Fallback a primera categoría
        
        # Crear etiquetas en la base de datos si no existen
        for tag_name in tags:
            existing_tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not existing_tag:
                tag_slug = tag_name.replace(' ', '-').lower()
                new_tag = Tag(name=tag_name, slug=tag_slug)
                db.add(new_tag)
        
        db.commit()
        
        # Actualizar estado
        processing_log = state.get('processing_log', [])
        processing_log.append(f"Categoría seleccionada: {category}")
        processing_log.append(f"Etiquetas creadas: {', '.join(tags)}")
        
        new_state = state.copy()
        new_state.update({
            'category': category,
            'tags': tags,
            'current_step': 'categorized',
            'processing_log': processing_log
        })
        
        return new_state
        
    except Exception as e:
        error_msg = f"Error en categorización: {str(e)}"
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + [error_msg],
            'current_step': 'categorizer_error'
        })
        return new_state
        
    finally:
        db.close()