#!/usr/bin/env python3
"""
API REST para Render - Con webhooks de Telegram (NO polling)
"""

import os
import sys
import logging
import tempfile
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import openai

load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear app Flask
app = Flask(__name__)

# Cliente OpenAI global
openai_client = openai.OpenAI()

# Cache para prevenir procesamiento de mensajes duplicados
processed_messages = set()
from threading import Lock
message_lock = Lock()

@app.route('/', methods=['GET'])
def health_check():
    """Health check para Render"""
    return jsonify({
        'status': 'active',
        'service': 'Agent Blogger API v2.0',
        'telegram_mode': 'webhooks',
        'version': 'webhook-fixed',
        'timestamp': datetime.now().isoformat(),
    })

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    """Webhook para recibir mensajes de Telegram - CON PROTECCIÓN ANTI-BUCLE"""
    try:
        update = request.get_json()
        
        if not update or 'message' not in update:
            return jsonify({'status': 'ignored'}), 200
        
        message = update['message']
        chat_id = message['chat']['id']
        message_id = message.get('message_id')
        message_date = message.get('date', 0)
        
        # PROTECCIÓN ANTI-BUCLE MEJORADA
        
        # 1. Ignorar mensajes del bot
        if 'from' in message and message['from'].get('is_bot', False):
            return jsonify({'status': 'ignored_bot_message'}), 200
        
        # 2. Ignorar mensajes que no son chats privados
        if message.get('chat', {}).get('type') != 'private':
            return jsonify({'status': 'ignored_not_private'}), 200
        
        # 3. CRÍTICO: Ignorar mensajes antiguos (más de 60 segundos)
        import time
        current_timestamp = int(time.time())
        message_age = current_timestamp - message_date
        
        if message_age > 60:  # Mensaje más viejo de 1 minuto
            logger.info(f"IGNORANDO mensaje antiguo - Age: {message_age}s, Chat: {chat_id}")
            return jsonify({'status': 'ignored_old_message', 'age_seconds': message_age}), 200
        
        # 4. CRÍTICO: Prevenir procesamiento de mensajes duplicados
        with message_lock:
            message_key = f"{chat_id}:{message_id}"
            if message_key in processed_messages:
                logger.info(f"IGNORANDO mensaje duplicado - Key: {message_key}")
                return jsonify({'status': 'ignored_duplicate_message'}), 200
            
            # Marcar mensaje como procesado
            processed_messages.add(message_key)
            
            # Limpiar cache viejo (mantener solo últimos 100 mensajes)
            if len(processed_messages) > 100:
                processed_messages.clear()
        
        # Log del mensaje recibido para debug
        logger.info(f"PROCESANDO mensaje - Chat: {chat_id}, ID: {message_id}, Age: {message_age}s")
        
        # Manejar comando /start
        if 'text' in message and message['text'] == '/start':
            send_telegram_message(chat_id, 
                "Agent Blogger Bot v2.0\n\n"
                "¡Ahora puedo crear articulos basados en tus ideas!\n\n"
                "Como funciona:\n"
                "• Envia un audio con tu idea\n"
                "• O escribe tu idea por texto\n"
                "• Yo genero un articulo completo\n\n"
                "Bot activo y listo!"
            )
            return jsonify({'status': 'start_sent'}), 200
        
        # Manejar mensajes de voz
        if 'voice' in message:
            logger.info(f"Procesando mensaje de voz - Chat: {chat_id}")
            return handle_voice_message(chat_id, message['voice'])
        
        # Manejar texto (ideas) - SOLO si no es comando
        if 'text' in message and not message['text'].startswith('/'):
            text = message['text']
            logger.info(f"Procesando texto - Chat: {chat_id}, Texto: {text[:50]}...")
            return handle_text_idea(chat_id, text)
        
        # Ignorar otros tipos de mensajes
        return jsonify({'status': 'ignored_unsupported'}), 200
        
    except Exception as e:
        logger.error(f"Error en webhook Telegram: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

def handle_voice_message(chat_id, voice):
    """Procesar mensaje de voz"""
    try:
        send_telegram_message(chat_id, "Procesando tu audio...")
        
        # Obtener archivo de audio
        file_url = get_telegram_file_url(voice['file_id'])
        
        # Descargar y transcribir
        audio_content = download_telegram_file(file_url)
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            temp_file.write(audio_content)
            temp_file.flush()
            
            # Transcribir con Whisper
            with open(temp_file.name, 'rb') as audio_file:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="es"
                )
            
            os.unlink(temp_file.name)
        
        idea_text = transcript.text
        
        send_telegram_message(chat_id,
            f"Transcripcion:\n\n\"{idea_text}\"\n\n"
            f"Generando articulo completo..."
        )
        
        # Generar artículo
        return generate_article_from_idea(chat_id, idea_text)
        
    except Exception as e:
        logger.error(f"Error procesando audio: {e}")
        send_telegram_message(chat_id, f"Error procesando audio: {str(e)}")
        return jsonify({'error': str(e)}), 500

def handle_text_idea(chat_id, text):
    """Procesar idea de texto"""
    try:
        send_telegram_message(chat_id,
            f"Idea recibida:\n\n\"{text}\"\n\n"
            f"Generando articulo completo..."
        )
        
        return generate_article_from_idea(chat_id, text)
        
    except Exception as e:
        logger.error(f"Error procesando texto: {e}")
        send_telegram_message(chat_id, f"Error procesando idea: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_article_from_idea(chat_id, idea):
    """Generar artículo usando la idea - CON CONTROL DE ERRORES MEJORADO"""
    try:
        logger.info(f"INICIANDO generación de artículo - Chat: {chat_id}")
        
        from agents.workflow import run_article_generation_sync_with_idea
        
        # Enviar mensaje de inicio
        send_telegram_message(chat_id, "Iniciando generacion completa del articulo...")
        
        result = run_article_generation_sync_with_idea(idea)
        
        if result and result.get('is_complete'):
            # Éxito total
            title = result.get('title', 'Sin título')
            wp_id = result.get('wordpress_id', 'N/A')
            keyword = result.get('selected_keyword', 'N/A')
            category = result.get('category', 'Sin categoría')
            tags = result.get('tags', [])
            
            # Log detallado para debug
            logger.info(f"RESULTADO WORKFLOW - Title: {title}, Category: {category}, Tags: {len(tags)}, WP_ID: {wp_id}")
            
            send_telegram_message(chat_id,
                f"Articulo completado exitosamente!\n\n"
                f"Titulo: {title}\n"
                f"Keyword SEO: {keyword}\n"
                f"Categoria: {category}\n"
                f"Tags: {len(tags)} etiquetas\n"
                f"WordPress ID: {wp_id}\n"
                f"Estado: Publicado\n\n"
                f"Disponible en tu sitio web!"
            )
            
            logger.info(f"ÉXITO - Artículo generado: {title} (ID: {wp_id})")
            return jsonify({'success': True, 'article_id': wp_id}), 200
            
        else:
            # Error en el workflow
            errors = result.get('errors', []) if result else ['Workflow falló sin resultado']
            error_msg = '; '.join(errors[-3:])  # Últimos 3 errores
            
            send_telegram_message(chat_id, 
                f"Error generando articulo\n\n"
                f"Tu idea: {idea[:100]}...\n\n"
                f"Detalles: {error_msg}\n\n"
                f"Intenta con una idea mas especifica."
            )
            
            logger.error(f"FALLO workflow - Chat: {chat_id}, Errores: {error_msg}")
            return jsonify({'success': False, 'errors': errors}), 500
            
    except Exception as e:
        error_str = str(e)
        logger.error(f"EXCEPCIÓN generando artículo - Chat: {chat_id}, Error: {error_str}")
        
        send_telegram_message(chat_id, 
            f"Error del sistema\n\n"
            f"Tu idea: {idea[:100]}...\n\n"
            f"Error tecnico: {error_str}\n\n"
            f"Por favor intenta de nuevo en unos minutos."
        )
        
        return jsonify({'success': False, 'error': error_str}), 500

def get_telegram_file_url(file_id):
    """Obtener URL de archivo de Telegram"""
    import requests
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    response = requests.get(f'https://api.telegram.org/bot{token}/getFile?file_id={file_id}')
    
    if response.status_code == 200:
        file_path = response.json()['result']['file_path']
        return f'https://api.telegram.org/file/bot{token}/{file_path}'
    else:
        raise Exception(f"Error obteniendo archivo: {response.text}")

def download_telegram_file(file_url):
    """Descargar archivo de Telegram"""
    import requests
    
    response = requests.get(file_url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Error descargando archivo: {response.status_code}")

def send_telegram_message(chat_id, text):
    """Enviar mensaje a Telegram"""
    import requests
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    
    data = {
        'chat_id': chat_id,
        'text': text
    }
    
    response = requests.post(url, json=data)
    if response.status_code != 200:
        logger.warning(f"Error enviando mensaje Telegram: {response.text}")

@app.route('/generate-article', methods=['POST'])
def generate_article_endpoint():
    """Endpoint para generar artículo automático (llamado por cron)"""
    try:
        logger.info("Solicitud de generación de artículo recibida")
        
        # Verificar token de seguridad
        auth_token = request.headers.get('Authorization')
        expected_token = os.getenv('API_SECRET_TOKEN', 'default-secret')
        
        if auth_token != f"Bearer {expected_token}":
            return jsonify({'error': 'No autorizado'}), 401
        
        # Generar artículo
        from agents.workflow import run_article_generation_sync
        
        start_time = datetime.now()
        result = run_article_generation_sync()
        end_time = datetime.now()
        
        generation_time = (end_time - start_time).total_seconds()
        
        if result and result.get('is_complete'):
            response = {
                'success': True,
                'article_id': result.get('wordpress_id'),
                'title': result.get('title'),
                'keyword': result.get('selected_keyword'),
                'generation_time': generation_time,
                'timestamp': end_time.isoformat()
            }
            
            logger.info(f"Artículo generado exitosamente: {result.get('title')}")
            return jsonify(response)
        else:
            logger.error("Error generando artículo")
            return jsonify({
                'success': False,
                'error': 'Error en la generación del artículo',
                'timestamp': end_time.isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Error en endpoint generate-article: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/status', methods=['GET'])
def status():
    """Estado del sistema"""
    try:
        # Verificar base de datos
        from database import get_db
        db = next(get_db())
        
        # Contar artículos
        from database.models import Article
        total_articles = db.query(Article).count()
        
        db.close()
        
        return jsonify({
            'status': 'operational',
            'telegram_mode': 'webhooks',
            'database': 'connected',
            'total_articles': total_articles,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/setup-webhook', methods=['POST'])
def setup_webhook():
    """Configurar webhook de Telegram"""
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        webhook_url = request.json.get('webhook_url')
        
        if not webhook_url:
            return jsonify({'error': 'webhook_url requerido'}), 400
        
        import requests
        response = requests.post(
            f'https://api.telegram.org/bot{token}/setWebhook',
            json={'url': f'{webhook_url}/telegram-webhook'}
        )
        
        if response.status_code == 200:
            return jsonify({'success': True, 'result': response.json()})
        else:
            return jsonify({'error': response.text}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    # Inicializar sistema
    logger.info("Iniciando Agent Blogger API v2.0 para Render (Webhooks)...")
    
    # Verificar variables de entorno
    required_vars = ['OPENAI_API_KEY', 'WP_URL', 'WP_USERNAME', 'WP_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Variables de entorno faltantes: {missing_vars}")
        sys.exit(1)
    
    # Inicializar base de datos
    try:
        from database import init_db
        from database.seed_data import run_seed
        init_db()
        run_seed()
        logger.info("Base de datos inicializada")
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        sys.exit(1)
    
    # Iniciar servidor Flask
    port = int(os.getenv('PORT', 5000))
    
    logger.info(f"Servidor iniciado en puerto {port}")
    logger.info("Telegram funcionando con WEBHOOKS (no polling)")
    logger.info("Endpoints disponibles:")
    logger.info("  GET  / - Health check")
    logger.info("  POST /telegram-webhook - Webhook de Telegram")
    logger.info("  POST /generate-article - Generar artículo automático")
    logger.info("  GET  /status - Estado del sistema")
    logger.info("  POST /setup-webhook - Configurar webhook Telegram")
    
    app.run(host='0.0.0.0', port=port, debug=False)