from typing import Dict, Any
from agents.state import ArticleState
from openai import OpenAI
import os
from dotenv import load_dotenv
from wordpress_sync import check_title_exists_in_wordpress

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
        # SISTEMA MEJORADO: Múltiples estilos creativos para evitar repetitividad
        import random
        
        # Estilos de escritura variados
        writing_styles = [
            {
                "name": "conversacional_directo",
                "instructions": "Estilo directo y conversacional. Usa preguntas retóricas, ejemplos cotidianos y un tono de 'te cuento como amigo'."
            },
            {
                "name": "narrativo_casos",
                "instructions": "Estilo narrativo con mini historias y casos reales. Cuenta ejemplos específicos como si fueran historias."
            },
            {
                "name": "practico_accionable", 
                "instructions": "Estilo súper práctico con pasos concretos, listas numeradas y acciones específicas que puede tomar YA."
            },
            {
                "name": "exploratorio_curioso",
                "instructions": "Estilo exploratorio que hace pensar. Usa analogías, comparaciones inesperadas y conceptos que abren la mente."
            },
            {
                "name": "profesional_experto",
                "instructions": "Estilo más profesional pero accesible. Combina experiencia técnica con explicaciones claras."
            }
        ]
        
        # Seleccionar estilo aleatorio
        selected_style = random.choice(writing_styles)
        
        # Estructuras variadas
        article_structures = [
            {
                "type": "problema_solucion",
                "template": "1. Introduce un problema común, 2. Explora las consecuencias, 3. Presenta soluciones paso a paso, 4. Muestra resultados esperados"
            },
            {
                "type": "comparativo",
                "template": "1. Situación actual vs ideal, 2. Diferentes enfoques/opciones, 3. Pros y contras, 4. Recomendación final"
            },
            {
                "type": "guia_paso_a_paso", 
                "template": "1. Por qué es importante, 2. Preparación necesaria, 3. Pasos detallados, 4. Qué esperar después"
            },
            {
                "type": "mitos_realidades",
                "template": "1. Mitos comunes sobre el tema, 2. La realidad detrás, 3. Qué significa para tu negocio, 4. Cómo aprovechar la verdad"
            },
            {
                "type": "evolucion_futuro",
                "template": "1. Cómo era antes, 2. Situación actual, 3. Tendencias emergentes, 4. Prepararse para el futuro"
            }
        ]
        
        # Seleccionar estructura aleatoria
        selected_structure = random.choice(article_structures)
        
        # Contextos de etapa mejorados y más específicos
        stage_contexts = {
            'conciencia': f"""
            OBJETIVO: Educar y crear awareness. El lector NO conoce mucho del tema.
            ENFOQUE: Explicar conceptos básicos, beneficios evidentes, desmitificar.
            ESTILO: {selected_style['instructions']}
            ESTRUCTURA: {selected_structure['template']}
            EJEMPLOS: Usa casos específicos de pymes argentinas (restaurante, taller, consultorio, etc.)
            """,
            'consideracion': f"""
            OBJETIVO: Ayudar a evaluar opciones. El lector YA conoce el tema básico.
            ENFOQUE: Comparaciones, criterios de decisión, casos de éxito, implementación.
            ESTILO: {selected_style['instructions']}
            ESTRUCTURA: {selected_structure['template']}
            EJEMPLOS: Historias reales de empresas que lo implementaron con resultados concretos.
            """,
            'compra': f"""
            OBJETIVO: Convencer y guiar a la acción. El lector está LISTO para decidir.
            ENFOQUE: Evidencia social, ROI claro, proceso de implementación, siguientes pasos.
            ESTILO: {selected_style['instructions']}
            ESTRUCTURA: {selected_structure['template']}
            EJEMPLOS: Casos de éxito con números específicos, testimonios, garantías.
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
        
        # PROMPT SÚPER MEJORADO Y CREATIVO
        prompt = f"""
        Eres Lucas Benites, consultor en IA para pymes argentinas. Pero HOY vas a escribir de manera DIFERENTE.
        
        TEMA DEL ARTÍCULO: "{keyword}"{telegram_context}
        
        🎯 CONTEXTO ESPECÍFICO: {stage_contexts[stage]}
        
        🎨 CREATIVIDAD OBLIGATORIA:
        - EVITA frases típicas como "en la era digital", "la transformación digital llegó para quedarse", "la inteligencia artificial está revolucionando"  
        - NO uses introducciones genéricas tipo "¿Te has preguntado alguna vez...?" o "En el mundo actual..."
        - EMPIEZA con algo inesperado: una estadística sorprendente, una pregunta provocativa, un dato contraintuitivo
        - USA analogías originales y específicas de Argentina (no futbol - ya es muy usado)
        
        📝 VARIEDAD OBLIGATORIA EN CONTENIDO:
        - Alternar párrafos largos con párrafos cortos
        - Incluir al menos una lista numerada Y una con bullets
        - Usar ejemplos específicos de tipos de pymes: panadería, ferretería, estudio contable, peluquería, consultorio médico, taller mecánico
        - EVITAR siempre los mismos ejemplos (restaurante ya se usó mucho)
        
        🏢 CASOS REALES ESPECÍFICOS:
        - Menciona situaciones específicas pero sin inventar nombres de empresas
        - Ejemplo: "un taller mecánico que implementó esto" en lugar de "Taller Mecánico López"
        - Usa datos aproximados: "redujo X% el tiempo" pero sin inventar cifras exactas
        
        🗣️ TONO Y ESTILO:
        - Usa "vos" argentino natural
        - Incluye expresiones argentinas ocasionales pero SIN exagerar
        - Sé directo y práctico - menos filosofía, más acción
        - Incluye al menos 2-3 preguntas directas al lector a lo largo del artículo
        
        📚 ESTRUCTURA DINÁMICA:
        - NO sigas siempre el mismo patrón de subtítulos
        - Varía entre títulos descriptivos ("Cómo implementar...") y títulos curiosos ("El problema que nadie ve")
        - Usa ## para títulos principales, ### para subtítulos
        - Incluye una sección que sorprenda al lector con información no obvia
        
        ⚠️ PROHIBIDO ABSOLUTAMENTE:
        - Frases hechas y clichés de marketing digital
        - Introducciones largas y genéricas  
        - Siempre los mismos ejemplos de pymes
        - Estructura rígida idéntica a artículos anteriores
        - Finales tipo "En conclusión..." o "Para concluir..."
        
        🎯 LONGITUD: Mínimo 1500 palabras, máximo 2200.
        
        Escribe ÚNICAMENTE el contenido del artículo (sin título ni meta descripción).
        SÉ CREATIVO, SORPRENDENTE Y DIFERENTE.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.85  # Más creatividad y variabilidad
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

        # NUEVO: Verificar que el título no exista en WordPress
        max_attempts = 3
        attempt = 1

        while attempt <= max_attempts and check_title_exists_in_wordpress(title):
            processing_log = state.get('processing_log', [])
            processing_log.append(f"Título '{title}' ya existe en WordPress. Generando alternativa (intento {attempt}/{max_attempts})...")

            # Generar un título alternativo
            retry_prompt = f"""
            El título "{title}" ya existe en WordPress. Genera un título DIFERENTE pero igualmente optimizado.

            REQUISITOS:
            - Máximo 60 caracteres
            - Debe incluir la keyword "{keyword}"
            - Debe ser completamente diferente al título anterior
            - Mantener optimización SEO
            - Tono conversacional y atractivo

            Responde SOLO con el nuevo título, sin comillas ni explicaciones.
            """

            retry_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": retry_prompt}],
                max_tokens=100,
                temperature=0.9  # Más creatividad para generar algo diferente
            )

            title = retry_response.choices[0].message.content.strip().strip('"').strip("'").strip()
            attempt += 1

        # Si después de los intentos sigue existiendo, agregar sufijo único
        if check_title_exists_in_wordpress(title):
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y")
            title = f"{title} {timestamp}"
            processing_log = state.get('processing_log', [])
            processing_log.append(f"⚠️ Título sigue duplicado. Agregando año: {title}")

        # Actualizar estado
        processing_log = state.get('processing_log', [])
        processing_log.append(f"Título creado y validado: {title}")

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