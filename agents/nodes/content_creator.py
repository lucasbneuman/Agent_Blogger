from typing import Dict, Any
from agents.state import ArticleState
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def content_creator_node(state: ArticleState) -> Dict[str, Any]:
    """
    Nodo para crear el cuerpo del artículo usando OpenAI.
    Genera contenido extenso y conversacional optimizado para SEO.
    """
    
    keyword = state.get('selected_keyword')
    stage = state.get('selected_stage')
    
    if not keyword or not stage:
        new_state = state.copy()
        new_state.update({
            'errors': ['Faltan keyword o stage para crear contenido'],
            'current_step': 'content_error'
        })
        return new_state
    
    try:
        # Definir el prompt según la etapa
        stage_contexts = {
            'conciencia': """
            El artículo debe educar y crear conciencia sobre el tema.
            Enfócate en explicar conceptos, beneficios y posibilidades.
            El lector está empezando a conocer sobre el tema.
            """,
            'consideracion': """
            El artículo debe ayudar al lector a evaluar opciones y soluciones.
            Incluye comparaciones, pros y contras, y casos de uso específicos.
            El lector ya conoce el tema y está evaluando opciones.
            """,
            'compra': """
            El artículo debe convencer y guiar hacia la toma de decisión.
            Incluye evidencia social, casos de uso reales y beneficios tangibles.
            El lector está listo para tomar una decisión.
            """
        }
        
        # Preparar contexto especial para ideas de Telegram
        telegram_context = ""
        if state.get('telegram_idea_mode') and state.get('telegram_idea'):
            telegram_context = f"""
        
        IMPORTANTE - IDEA ORIGINAL DEL USUARIO:
        "{state['telegram_idea']}"
        
        INSTRUCCIONES ESPECIALES:
        - Basa el artículo específicamente en esta idea del usuario
        - La keyword "{keyword}" debe estar integrada naturalmente 
        - Responde directamente a lo que el usuario pidió en su idea
        - Mantén el enfoque específico de su solicitud
        """
        
        prompt = f"""
        Eres Lucas Benites, un consultor en Inteligencia Artificial especializado en pymes argentinas.
        
        Escribe un artículo extenso (mínimo 1500 palabras) sobre: "{keyword}"{telegram_context}
        
        CONTEXTO DE ETAPA: {stage_contexts[stage]}
        
        CARACTERÍSTICAS DEL ARTÍCULO:
        - Lenguaje conversacional y cercano
        - Dirigido a dueños y gerentes de pymes (poco técnicos)
        - Marca personal: Lucas Benites 
        - Público principalmente argentino
        - Incluir ejemplos prácticos y casos de uso reales
        - Estructura clara con subtítulos usando ## y ###
        - Optimizado para SEO con la keyword principal
        
        ESTRUCTURA REQUERIDA:
        1. Introducción enganchadora (problema/beneficio)
        2. 3-4 secciones principales con subtítulos ##
        3. Cada sección con 2-3 subsecciones ### si es necesario
        4. Casos de uso específicos y ejemplos prácticos en cada sección
        5. Conclusión que resuma los puntos clave
        
        IMPORTANTE: 
        - Usa formato markdown (## para títulos, ### para subtítulos)
        - NO escribas "H2:" o "H3:" - usa directamente ## y ###
        - Enfócate en casos de uso REALES, no inventes casos de éxito específicos
        
        TONO:
        - Conversacional ("vos" en lugar de "tú")
        - Experto pero accesible
        - Empático con los desafíos de las pymes
        - Optimista sobre las posibilidades de la IA
        
        Escribe SOLO el contenido del artículo, sin título ni meta descripción.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        
        # Actualizar estado
        processing_log = state.get('processing_log', [])
        processing_log.append("Contenido del artículo generado exitosamente")
        
        new_state = state.copy()
        new_state.update({
            'content': content,
            'current_step': 'content_created',
            'processing_log': processing_log,
            'needs_revision': False,  # Limpiar flag cuando el contenido se crea exitosamente
            'errors': []  # Limpiar errores previos cuando se corrige el contenido
        })
        
        return new_state
        
    except Exception as e:
        error_msg = f"Error creando contenido: {str(e)}"
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + [error_msg],
            'current_step': 'content_error'
        })
        return new_state

def title_creator_node(state: ArticleState) -> Dict[str, Any]:
    """
    Nodo para crear un título SEO optimizado para el artículo.
    """
    
    keyword = state.get('selected_keyword')
    content = state.get('content')
    stage = state.get('selected_stage')
    
    if not keyword or not content:
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + ['Faltan keyword o contenido para crear título'],
            'current_step': 'title_error'
        })
        return new_state
    
    try:
        prompt = f"""
        Crea un título SEO optimizado para un artículo sobre "{keyword}".
        
        CONTEXTO:
        - Etapa del buyer journey: {stage}
        - Sitio web: lucasbenites.com (consultor IA para pymes)
        - Público: dueños y gerentes de pymes argentinas
        
        REQUISITOS DEL TÍTULO:
        - Máximo 60 caracteres (importante para SEO)
        - Incluir la keyword principal de forma natural
        - Atractivo y clickeable
        - Que refleje el contenido del artículo
        - Tono conversacional y directo
        
        EJEMPLOS DE ESTILO:
        - Cómo [hacer algo] en 5 pasos simples
        - [Número] formas de [beneficio] para tu pyme
        - Qué es [concepto] y cómo puede [beneficio]
        - Guía completa de [tema] para pymes argentinas
        
        IMPORTANTE: Responde SOLO con el título limpio, SIN comillas, SIN explicaciones.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )
        
        title = response.choices[0].message.content.strip()
        
        # Limpiar comillas que puedan haber quedado
        title = title.strip('"').strip("'").strip()
        
        # Actualizar estado
        processing_log = state.get('processing_log', [])
        processing_log.append(f"Título creado: {title}")
        
        new_state = state.copy()
        new_state.update({
            'title': title,
            'current_step': 'title_created',
            'processing_log': processing_log
        })
        
        return new_state
        
    except Exception as e:
        error_msg = f"Error creando título: {str(e)}"
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + [error_msg],
            'current_step': 'title_error'
        })
        return new_state

def meta_description_creator_node(state: ArticleState) -> Dict[str, Any]:
    """
    Nodo para crear la meta descripción del artículo.
    """
    
    title = state.get('title')
    keyword = state.get('selected_keyword')
    content = state.get('content')
    
    if not all([title, keyword, content]):
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + ['Faltan título, keyword o contenido para meta descripción'],
            'current_step': 'meta_error'
        })
        return new_state
    
    try:
        prompt = f"""
        Crea una meta descripción SEO para este artículo:
        
        TÍTULO: {title}
        KEYWORD: {keyword}
        
        REQUISITOS:
        - Máximo 155 caracteres (crucial para SEO)  
        - Incluir la keyword principal
        - Resumir el valor del artículo
        - Call-to-action sutil
        - Tono conversacional
        
        Responde SOLO con la meta descripción, sin comillas ni explicaciones.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        
        meta_description = response.choices[0].message.content.strip()
        
        # Verificar longitud
        if len(meta_description) > 155:
            meta_description = meta_description[:152] + "..."
        
        # Actualizar estado
        processing_log = state.get('processing_log', [])
        processing_log.append("Meta descripción creada")
        
        new_state = state.copy()
        new_state.update({
            'meta_description': meta_description,
            'current_step': 'meta_created',
            'processing_log': processing_log
        })
        
        return new_state
        
    except Exception as e:
        error_msg = f"Error creando meta descripción: {str(e)}"
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + [error_msg],
            'current_step': 'meta_error'
        })
        return new_state