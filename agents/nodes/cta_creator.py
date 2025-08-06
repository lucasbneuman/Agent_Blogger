from typing import Dict, Any
from agents.state import ArticleState
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def cta_creator_node(state: ArticleState) -> Dict[str, Any]:
    """
    Nodo para crear CTA (Call-to-Action) al final del artículo.
    Usa el archivo ctas.txt para seleccionar el enlace apropiado según la etapa.
    """
    
    stage = state.get('selected_stage')
    title = state.get('title')
    keyword = state.get('selected_keyword')
    
    if not all([stage, title]):
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + ['Faltan stage o título para crear CTA'],
            'current_step': 'cta_error'
        })
        return new_state
    
    try:
        # Leer archivo ctas.txt para obtener enlaces por etapa
        cta_links = {
            'conciencia': {
                'url': 'https://032cf721.sibforms.com/serve/MUIFAE47zttqxtfbDRc3ItIdRx3jI2XDzO5OLTijGhWzk0VnJxbYG97Q1OrgM17TZXOSEKyhy-RVK9N6MQf2nmkkAPBXeRuNM1KiAvsMf5xrdH1lBWiypothxpeUCSLwFkWWUTvFB211Gu0b8NKpEk_SlyucOKg4weycY3zSId5SERj5yKJjUHM7rVaTqJY7Z3XZ7p5H9bIKK0mY',
                'description': 'Formulario para descargar un Checklist y validar si un negocio está listo para implementar IA'
            },
            'consideracion': {
                'url': 'https://lucasbenites.com/5-automatizaciones-inteligentes-con-ia/',
                'description': 'Recurso gratuito sobre formas y herramientas para implementar IA en negocios'
            },
            'compra': {
                'url': 'https://meet.brevo.com/lucas-benites',
                'description': 'Agendar una reunión gratuita para aprender a implementar IA en el negocio'
            }
        }
        
        # Obtener enlace para la etapa actual
        cta_info = cta_links.get(stage, cta_links['consideracion'])  # Fallback a consideración
        
        # Crear prompt para generar CTA
        prompt = f"""
        Crea un CTA (Call-to-Action) sutil y efectivo para el final de este artículo:
        
        TÍTULO DEL ARTÍCULO: {title}
        KEYWORD: {keyword}
        ETAPA: {stage}
        
        ENLACE A USAR: {cta_info['url']}
        DESCRIPCIÓN DEL ENLACE: {cta_info['description']}
        
        REQUISITOS DEL CTA:
        - Subtítulo atractivo (H3)
        - Párrafo de 2-3 oraciones que conecte naturalmente con el artículo
        - Llamada a la acción clara pero no agresiva
        - Tono conversacional y empático
        - Enfoque en el beneficio para el lector
        
        EJEMPLOS DE TONO SEGÚN ETAPA:
        - Conciencia: "Si querés evaluar..." / "Para conocer más..."
        - Consideración: "Si estás listo para..." / "Para profundizar..."
        - Compra: "Si necesitás ayuda..." / "Para comenzar hoy..."
        
        FORMATO:
        ### [Subtítulo del CTA]
        
        [Párrafo conectando con el artículo y presentando la oferta]
        
        [Oración con call-to-action específico]
        
        No incluyas el enlace HTML, solo el texto. El enlace se agregará después.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        
        cta_content = response.choices[0].message.content.strip()
        
        # Extraer título del CTA (línea que empieza con ###)
        lines = cta_content.split('\n')
        cta_title = ""
        cta_body = ""
        
        for i, line in enumerate(lines):
            if line.startswith('###'):
                cta_title = line.replace('###', '').strip()
                # El resto es el cuerpo
                cta_body = '\n'.join(lines[i+1:]).strip()
                break
        
        if not cta_title:
            cta_title = "¿Te gustaría saber más?"
            cta_body = cta_content
        
        # Actualizar estado
        processing_log = state.get('processing_log', [])
        processing_log.append(f"CTA creado para etapa: {stage}")
        
        new_state = state.copy()
        new_state.update({
            'cta_title': cta_title,
            'cta_content': cta_body,
            'cta_link': cta_info['url'],
            'current_step': 'cta_created',
            'processing_log': processing_log
        })
        
        return new_state
        
    except Exception as e:
        error_msg = f"Error creando CTA: {str(e)}"
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + [error_msg],
            'current_step': 'cta_error'
        })
        return new_state