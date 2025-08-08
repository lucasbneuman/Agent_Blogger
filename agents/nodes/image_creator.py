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
        Crea un prompt ESPECÍFICO para DALL-E que genere una imagen REALISTA para PYMES (pequeñas y medianas empresas):
        
        TÍTULO: {title}
        KEYWORD: {keyword}
        ETAPA: {stage}
        CONTENIDO: {content_preview}...
        
        REQUISITOS OBLIGATORIOS PARA PYMES:
        
        1. CONTEXTO ESPECÍFICO DE PYME (NO corporativo):
        - Si es transporte → pequeña empresa de logística, camiones medianos
        - Si es restaurante → restaurante familiar, cocina casera profesional
        - Si es consultoría → oficina pequeña, emprendedores, ambiente acogedor
        - Si es médico → consultorio privado pequeño, clínica familiar
        - Si es comercio → tienda local, negocio familiar
        
        2. PERSONAS REALES DE PYME:
        - Propietarios/emprendedores (30-50 años)
        - Equipos pequeños (2-4 personas máximo)
        - Vestimenta profesional pero casual
        - Diversidad étnica (latinos, argentinos)
        - Expresiones amigables y cercanas
        
        3. AMBIENTE PYME REALISTA:
        - Espacios más pequeños e íntimos
        - Decoración moderna pero accesible
        - Tecnología práctica (laptops, tablets)
        - Colores cálidos y variados (NO solo azul corporativo)
        - Iluminación natural y acogedora
        
        4. COLORES Y ESTILO:
        - Paleta variada: naranjas, verdes, amarillos, rojos
        - Evitar azul corporativo dominante
        - Atmósfera cálida y humana
        - Estilo "documentary photography"
        
        EJEMPLOS ESPECÍFICOS:
        - IA en transporte → "Friendly logistics small business owners planning routes with tablets in warehouse, warm lighting, diverse Latin American entrepreneurs, orange and green color scheme"
        - Automatización restaurante → "Family restaurant owners using digital ordering system, cozy dining space, warm colors, authentic small business atmosphere"
        
        Crea un prompt MUY ESPECÍFICO en inglés que capture un negocio PYME real y auténtico. Responde SOLO con el prompt.
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