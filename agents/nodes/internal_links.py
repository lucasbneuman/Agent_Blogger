from typing import Dict, Any, List
from agents.state import ArticleState
from openai import OpenAI
from database import get_db
from database.models import Article
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def internal_links_node(state: ArticleState) -> Dict[str, Any]:
    """
    Nodo para crear vínculos internos hacia otros artículos.
    Modifica el contenido agregando enlaces contextuales.
    """
    
    content = state.get('content')
    keyword = state.get('selected_keyword')
    stage = state.get('selected_stage')
    
    if not content:
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + ['Falta contenido para crear vínculos internos'],
            'current_step': 'internal_links_error'
        })
        return new_state
    
    # Obtener artículos existentes de la base de datos
    db = next(get_db())
    
    try:
        existing_articles = db.query(Article).filter(
            Article.is_published == True
        ).all()
        
        if not existing_articles:
            # Si no hay artículos existentes, continuar sin enlaces internos
            processing_log = state.get('processing_log', [])
            processing_log.append("No hay artículos existentes para enlaces internos")
            
            new_state = state.copy()
            new_state.update({
                'internal_links': [],
                'current_step': 'internal_links_skipped',
                'processing_log': processing_log
            })
            return new_state
        
        # Preparar información de artículos para el prompt
        articles_info = []
        for article in existing_articles[:10]:  # Limitar a 10 artículos más relevantes
            # Construir URL completa basada en categoría y slug
            category_slug = article.category.slug if article.category else 'blog'
            full_url = f"https://lucasbenites.com/{category_slug}/{article.slug}/"
            
            articles_info.append({
                'title': article.title,
                'keyword': article.main_keyword,
                'stage': article.stage,
                'slug': article.slug,
                'url': full_url
            })
        
        articles_text = "\n".join([
            f"- Título: {art['title']}\n  Keyword: {art['keyword']}\n  Etapa: {art['stage']}\n  URL: {art['url']}"
            for art in articles_info
        ])
        
        prompt = f"""
        Eres un experto en SEO y marketing de contenidos. Tu tarea es integrar enlaces internos de manera natural y orgánica en el contenido.
        
        CONTENIDO ACTUAL:
        {content}
        
        ARTÍCULOS EXISTENTES:
        {articles_text}
        
        INSTRUCCIONES:
        1. Lee todo el contenido completo
        2. Identifica 2-3 frases específicas que puedan ser reemplazadas con enlaces internos
        3. Los enlaces deben fluir naturalmente en el contexto
        4. Usa anchor text descriptivo que mejore la experiencia del usuario
        5. Los enlaces deben ser relevantes al tema que se está discutiendo en esa sección
        
        IMPORTANTE: Devuelve el contenido COMPLETO modificado con los enlaces integrados.
        
        FORMATO DE RESPUESTA:
        Primero lista los enlaces que vas a agregar:
        
        ENLACES AGREGADOS:
        1. Texto original: "[texto a reemplazar]"
           Nuevo texto: "[texto con enlace HTML usando las URLs proporcionadas]"
           URL: [url completa del artículo de la lista]
           Justificación: [por qué es relevante]
        
        Luego el contenido completo modificado:
        
        CONTENIDO MODIFICADO:
        [contenido completo con enlaces integrados usando HTML <a href="url">texto</a>]
        
        IMPORTANTE: 
        - Usa EXACTAMENTE las URLs proporcionadas en la lista de artículos
        - Integra los enlaces de forma natural en el flujo del texto
        - No agregues enlaces al final, sino distribuidos en el contenido
        - Máximo 3 enlaces para mantener calidad
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content
        
        # Parsear la respuesta para extraer enlaces y contenido modificado
        internal_links = []
        modified_content = content
        
        try:
            # Buscar la sección de enlaces agregados
            if "ENLACES AGREGADOS:" in ai_response:
                enlaces_section = ai_response.split("ENLACES AGREGADOS:")[1]
                if "CONTENIDO MODIFICADO:" in enlaces_section:
                    enlaces_text = enlaces_section.split("CONTENIDO MODIFICADO:")[0]
                    modified_content = enlaces_section.split("CONTENIDO MODIFICADO:")[1].strip()
                    
                    # Parsear los enlaces para el registro
                    enlace_items = enlaces_text.split('\n')
                    current_link = {}
                    
                    for line in enlace_items:
                        line = line.strip()
                        if line.startswith('URL:'):
                            url = line.replace('URL:', '').strip()
                            if current_link.get('original') and current_link.get('nuevo'):
                                current_link['url'] = url
                                internal_links.append({
                                    'url': url,
                                    'anchor': current_link.get('anchor', ''),
                                    'context': current_link.get('original', '')
                                })
                                current_link = {}
                        elif 'Texto original:' in line:
                            original = line.split('Texto original:')[1].strip().strip('"')
                            current_link['original'] = original
                        elif 'Nuevo texto:' in line:
                            nuevo = line.split('Nuevo texto:')[1].strip().strip('"')
                            current_link['nuevo'] = nuevo
                            # Extraer el anchor text del HTML
                            if '<a href=' in nuevo and '>' in nuevo and '</a>' in nuevo:
                                start = nuevo.find('>') + 1
                                end = nuevo.find('</a>')
                                if start > 0 and end > start:
                                    current_link['anchor'] = nuevo[start:end]
            
            # Si no se pudo parsear correctamente, usar el contenido original
            if not modified_content or modified_content == content:
                modified_content = content
                internal_links = []
                
        except Exception as parse_error:
            # Si hay error en el parseo, usar contenido original
            modified_content = content
            internal_links = []
        
        # Verificar que el contenido fue realmente modificado
        content_changed = modified_content != content
        links_found = len(internal_links) > 0
        
        # Actualizar estado
        processing_log = state.get('processing_log', [])
        if content_changed and links_found:
            processing_log.append(f"Se integraron {len(internal_links)} vínculos internos en el contenido")
            for i, link in enumerate(internal_links, 1):
                processing_log.append(f"  {i}. {link.get('anchor', 'N/A')} -> {link.get('url', 'N/A')}")
        elif not existing_articles:
            processing_log.append("No hay artículos existentes para enlaces internos")
        else:
            processing_log.append("No se pudieron integrar enlaces internos en el contenido")
        
        new_state = state.copy()
        new_state.update({
            'content': modified_content,
            'internal_links': internal_links,
            'current_step': 'internal_links_created',
            'processing_log': processing_log
        })
        
        return new_state
        
    except Exception as e:
        error_msg = f"Error creando vínculos internos: {str(e)}"
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + [error_msg],
            'current_step': 'internal_links_error'
        })
        return new_state
        
    finally:
        db.close()