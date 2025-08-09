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
        
        1. CONTEXTO ESPECÍFICO DE PYME (NO corporativo) - ANALIZAR EL TEMA PARA ELEGIR:
        - Si es IA/tecnología → oficina pequeña moderna, emprendedores con laptops
        - Si es automatización → taller, fábrica pequeña, o negocio usando tablets
        - Si es atención al cliente → oficina de servicios, recepción acogedora
        - Si es marketing → agencia pequeña, equipo creativo, pantallas
        - Si es consultoría → sala de reuniones pequeña, ambiente profesional
        - Si es transporte/logística → depósito, camiones, planificación
        - Si es salud → consultorio, clínica familiar
        - Si es comercio → tienda, punto de venta, atención personalizada
        - Si es general → oficina PYME diversa, equipo trabajando
        
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
        
        EJEMPLOS ESPECÍFICOS POR TEMA:
        - IA para PYMES → "Small business team working with AI tools on laptops in modern cozy office, diverse entrepreneurs, warm lighting, orange and blue accents"
        - Automatización procesos → "Small manufacturing business owners reviewing automated systems on tablets, workshop setting, friendly atmosphere"
        - Atención al cliente → "PYME customer service team using modern tools in welcoming office, personal touch, warm colors"
        - Marketing digital → "Small creative agency team planning campaigns, collaborative workspace, energetic but intimate setting"
        - Consultoría empresarial → "Business consultants meeting with PYME owners in comfortable conference room, professional yet approachable"
        
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