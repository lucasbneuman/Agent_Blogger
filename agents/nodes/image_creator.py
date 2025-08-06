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
        # Crear prompt para la imagen basado en el contenido
        image_prompt_generator = f"""
        Crea un prompt en inglés para DALL-E que genere una imagen destacada profesional para este artículo:
        
        TÍTULO: {title}
        KEYWORD: {keyword}
        ETAPA: {stage}
        
        REQUISITOS DE LA IMAGEN:
        - Personas reales trabajando en oficina/empresa
        - Ambiente profesional pero cálido
        - Tecnología/computadoras visible pero no dominante
        - Estilo fotográfico realista
        - Colores profesionales (azules, grises, blancos)
        - Aspectos de colaboración y éxito empresarial
        
        ESTILO:
        - "Professional business photography"
        - "High quality"
        - "Modern office environment"
        - "Real people"
        - "Natural lighting"
        
        Crea un prompt detallado en inglés para DALL-E. Responde SOLO con el prompt.
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