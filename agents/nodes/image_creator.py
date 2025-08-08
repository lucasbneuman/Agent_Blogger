from typing import Dict, Any
from agents.state import ArticleState
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def image_creator_node(state: ArticleState) -> Dict[str, Any]:
    """
    Nodo para crear imagen destacada usando DALL-E.
    Genera un prompt optimizado y crea la imagen.
    """
    
    title = state.get('title')
    keyword = state.get('selected_keyword')
    stage = state.get('selected_stage')
    
    if not all([title, keyword]):
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + ['Faltan título o keyword para crear imagen'],
            'current_step': 'image_error'
        })
        return new_state
    
    try:
        # Crear prompt mejorado y contextual para la imagen
        content_preview = state.get('content', '')[:500]  # Obtener preview del contenido
        
        image_prompt_generator = f"""
        Analiza este artículo y crea un prompt ESPECÍFICO y CONTEXTUAL en inglés para DALL-E:
        
        TÍTULO: {title}
        KEYWORD: {keyword}
        ETAPA: {stage}
        CONTENIDO (preview): {content_preview}...
        
        INSTRUCCIONES PARA CREAR EL PROMPT:
        
        1. IDENTIFICA EL CONTEXTO ESPECÍFICO:
        - Si menciona consultorio médico → imagen en consultorio/clínica
        - Si habla de restaurante → imagen en restaurante/cocina
        - Si es sobre fábrica → imagen en planta industrial
        - Si es oficina → imagen en oficina moderna
        - Si es e-commerce → imagen en almacén/tienda online
        - Si es sobre educación → imagen en aula/centro educativo
        
        2. INCLUYE PROTAGONISTAS ESPECÍFICOS:
        - Profesionales del sector mencionado (médicos, chefs, ingenieros, etc.)
        - Personas reales y diversas
        - Vestimenta apropiada al contexto
        - Expresiones de confianza y profesionalismo
        
        3. AMBIENTE REALISTA Y ESPECÍFICO:
        - Ubicación específica según el tema
        - Herramientas/equipos del sector
        - Detalles que den credibilidad
        - Iluminación natural y profesional
        
        4. ESTILO FOTOGRÁFICO:
        - "Professional corporate photography"
        - "High-resolution realistic photo"
        - "Natural lighting, sharp focus"
        - "Modern [specific industry] setting"
        
        EJEMPLOS DE CONTEXTOS:
        - Artículo sobre IA en medicina → "Professional medical team using AI technology in modern hospital, doctors and nurses collaborating with computers, clinical setting"
        - Artículo sobre automatización en restaurantes → "Professional chefs and restaurant staff using digital ordering systems, modern commercial kitchen"
        - Artículo sobre pymes → "Small business owners working together in modern office, diverse team collaborating"
        
        Crea un prompt MUY ESPECÍFICO en inglés que capture el contexto exacto del artículo. Responde SOLO con el prompt.
        """
        
        prompt_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": image_prompt_generator}],
            max_tokens=200,
            temperature=0.7
        )
        
        image_prompt = prompt_response.choices[0].message.content.strip()
        
        # Generar imagen con DALL-E
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        image_url = image_response.data[0].url
        
        # Crear texto alternativo para la imagen
        alt_text_prompt = f"""
        Crea un texto alternativo (alt text) SEO para una imagen destacada de este artículo:
        
        TÍTULO: {title}
        KEYWORD: {keyword}
        
        REQUISITOS:
        - Máximo 125 caracteres
        - Descriptivo y relevante al contenido
        - Incluir la keyword si es natural
        - Accesible para lectores de pantalla
        
        Responde SOLO con el alt text.
        """
        
        alt_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": alt_text_prompt}],
            max_tokens=50,
            temperature=0.3
        )
        
        alt_text = alt_response.choices[0].message.content.strip()
        
        # Actualizar estado
        processing_log = state.get('processing_log', [])
        processing_log.append("Imagen destacada generada exitosamente")
        processing_log.append(f"Prompt de imagen: {image_prompt}")
        
        new_state = state.copy()
        new_state.update({
            'featured_image_prompt': image_prompt,
            'featured_image_url': image_url,
            'featured_image_alt': alt_text,
            'current_step': 'image_created',
            'processing_log': processing_log
        })
        
        return new_state
        
    except Exception as e:
        error_msg = f"Error creando imagen: {str(e)}"
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + [error_msg],
            'current_step': 'image_error'
        })
        return new_state