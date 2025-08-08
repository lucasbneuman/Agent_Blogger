#!/usr/bin/env python3
"""
API REST para Render - Maneja generación programada y bot Telegram
"""

import os
import sys
import asyncio
import threading
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import json

load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear app Flask
app = Flask(__name__)

# Variable global para el bot
telegram_bot_thread = None
telegram_app = None

def init_telegram_bot():
    """Inicializar bot de Telegram en hilo separado"""
    global telegram_app
    
    try:
        from integrations.telegram_final import FinalTelegramBot
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
        
        bot = FinalTelegramBot()
        telegram_app = Application.builder().token(bot.token).build()
        
        # Handlers
        telegram_app.add_handler(CommandHandler("start", bot.start))
        telegram_app.add_handler(MessageHandler(filters.VOICE, bot.handle_voice_message))
        telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text_message))
        
        logger.info("Bot de Telegram configurado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"Error inicializando bot Telegram: {e}")
        return False

def run_telegram_bot():
    """Ejecutar bot de Telegram"""
    global telegram_app
    
    if not telegram_app:
        logger.error("Bot de Telegram no inicializado")
        return
    
    try:
        # Crear nuevo event loop para este hilo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info("Iniciando bot de Telegram...")
        telegram_app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Error ejecutando bot Telegram: {e}")

@app.route('/', methods=['GET'])
def health_check():
    """Health check para Render"""
    return jsonify({
        'status': 'active',
        'service': 'Agent Blogger API',
        'version': '2.0',
        'timestamp': datetime.utcnow().isoformat(),
        'telegram_bot': 'active' if telegram_app else 'inactive'
    })

@app.route('/generate-article', methods=['POST'])
def generate_article_endpoint():
    """Endpoint para generar artículo automático (llamado por cron)"""
    try:
        logger.info("Solicitud de generación de artículo recibida")
        
        # Verificar token de seguridad (opcional)
        auth_token = request.headers.get('Authorization')
        expected_token = os.getenv('API_SECRET_TOKEN', 'default-secret')
        
        if auth_token != f"Bearer {expected_token}":
            return jsonify({'error': 'No autorizado'}), 401
        
        # Generar artículo
        from agents.workflow import run_article_generation_sync
        
        start_time = datetime.utcnow()
        result = run_article_generation_sync()
        end_time = datetime.utcnow()
        
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
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/generate-with-idea', methods=['POST'])
def generate_with_idea_endpoint():
    """Endpoint para generar artículo con idea específica"""
    try:
        data = request.get_json()
        
        if not data or 'idea' not in data:
            return jsonify({'error': 'Campo "idea" requerido'}), 400
        
        idea = data['idea']
        logger.info(f"Generando artículo con idea: {idea[:100]}...")
        
        # Generar artículo con idea
        from agents.workflow import run_article_generation_sync_with_idea
        
        start_time = datetime.utcnow()
        result = run_article_generation_sync_with_idea(idea)
        end_time = datetime.utcnow()
        
        generation_time = (end_time - start_time).total_seconds()
        
        if result and result.get('is_complete'):
            response = {
                'success': True,
                'article_id': result.get('wordpress_id'),
                'title': result.get('title'),
                'keyword': result.get('selected_keyword'),
                'idea': idea,
                'generation_time': generation_time,
                'timestamp': end_time.isoformat()
            }
            
            logger.info(f"Artículo con idea generado: {result.get('title')}")
            return jsonify(response)
        else:
            return jsonify({
                'success': False,
                'error': 'Error en la generación del artículo',
                'timestamp': end_time.isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Error en endpoint generate-with-idea: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
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
            'telegram_bot': 'active' if telegram_app else 'inactive',
            'database': 'connected',
            'total_articles': total_articles,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

def start_telegram_in_background():
    """Iniciar bot de Telegram en hilo separado"""
    global telegram_bot_thread
    
    if init_telegram_bot():
        telegram_bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        telegram_bot_thread.start()
        logger.info("Bot de Telegram iniciado en hilo separado")
    else:
        logger.warning("No se pudo inicializar el bot de Telegram")

if __name__ == "__main__":
    # Inicializar sistema
    logger.info("Iniciando Agent Blogger API para Render...")
    
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
    
    # Iniciar bot de Telegram en background si está configurado
    if os.getenv('TELEGRAM_BOT_TOKEN'):
        start_telegram_in_background()
    else:
        logger.warning("TELEGRAM_BOT_TOKEN no configurado - Bot de Telegram deshabilitado")
    
    # Iniciar servidor Flask
    port = int(os.getenv('PORT', 5000))
    
    logger.info(f"Servidor iniciado en puerto {port}")
    logger.info("Endpoints disponibles:")
    logger.info("  GET  / - Health check")
    logger.info("  POST /generate-article - Generar artículo automático")
    logger.info("  POST /generate-with-idea - Generar con idea específica")
    logger.info("  GET  /status - Estado del sistema")
    
    app.run(host='0.0.0.0', port=port, debug=False)