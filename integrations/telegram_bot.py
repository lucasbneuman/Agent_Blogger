#!/usr/bin/env python3
"""
Bot de Telegram para recibir ideas de audio y generar artículos.
"""

import os
import asyncio
import logging
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

class TelegramBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.openai_client = openai.OpenAI()
        self.application = None
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN no encontrado en variables de entorno")
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID no encontrado en variables de entorno")
    
    def init_bot(self):
        """Inicializar el bot de Telegram"""
        self.application = Application.builder().token(self.token).build()
        
        # Comandos
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("generate", self.generate_command))
        
        # Manejo de mensajes de audio/voz
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        self.application.add_handler(MessageHandler(filters.AUDIO, self.handle_audio))
        
        # Manejo de mensajes de texto para ideas
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_idea))
        
        return self.application
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        await update.message.reply_text(
            "🤖 **Agent Blogger Bot v2.0**\n\n"
            "¡Ahora puedo crear artículos basados en tus ideas!\n\n"
            "**¿Cómo funciona?**\n"
            "• 🎤 Envía un audio con tu idea\n"
            "• 💬 O escribe tu idea por texto\n"
            "• ✨ Yo genero un artículo completo\n\n"
            "**Comandos:**\n"
            "• /help - Ayuda detallada\n"
            "• /generate - Generar artículo automático\n\n"
            "✅ Bot activo y listo!"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        await update.message.reply_text(
            "📖 **Ayuda - Agent Blogger Bot**\n\n"
            "**Generar artículos con ideas:**\n"
            "• 🎤 Envía un mensaje de voz con tu idea\n"
            "• 🎵 O un archivo de audio\n"
            "• 💬 O escribe tu idea por texto\n\n"
            "**Ejemplo de idea:**\n"
            "💡 'Quiero un artículo sobre cómo las pymes argentinas pueden usar IA para automatizar su contabilidad'\n\n"
            "**Generar artículo automático:**\n"
            "• /generate - El sistema elige el tema automáticamente\n\n"
            "**Tips para mejores resultados:**\n"
            "• Sé específico con tu idea\n"
            "• Menciona el público objetivo\n"
            "• Incluye contexto argentino si es relevante\n\n"
            "¡El artículo se publicará automáticamente en WordPress!"
        )
    
    async def generate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generar artículo automático sin idea específica"""
        await update.message.reply_text(
            "🚀 **Generando artículo automático...**\n\n"
            "⏳ El sistema está creando un artículo completo basado en palabras clave disponibles.\n\n"
            "Te notificaré cuando esté publicado en WordPress."
        )
        
        # Ejecutar workflow automático
        try:
            from agents.workflow import run_article_generation_sync
            result = await asyncio.get_event_loop().run_in_executor(None, run_article_generation_sync)
            
            if result and result.get('is_complete'):
                await update.message.reply_text(
                    f"✅ **Artículo generado exitosamente!**\n\n"
                    f"📰 **Título:** {result.get('title', 'N/A')}\n"
                    f"🆔 **WordPress ID:** {result.get('wordpress_id', 'N/A')}\n"
                    f"🔗 **Estado:** Publicado\n\n"
                    f"¡Ya está disponible en tu sitio web!"
                )
            else:
                await update.message.reply_text(
                    "❌ **Error generando artículo**\n\n"
                    "Hubo un problema en el proceso. Revisa los logs del sistema."
                )
        except Exception as e:
            logging.error(f"Error ejecutando workflow automático: {str(e)}")
            await update.message.reply_text(
                "❌ **Error del sistema**\n\n"
                f"No se pudo generar el artículo: {str(e)}"
            )
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar mensajes de voz"""
        await update.message.reply_text("🎤 **Procesando tu audio...**\n⏳ Transcribiendo...")
        
        temp_file_path = None
        try:
            # Descargar el archivo de audio
            voice = update.message.voice
            file = await context.bot.get_file(voice.file_id)
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                temp_file_path = temp_file.name
                await file.download_to_drive(temp_file_path)
            
            # Transcribir usando OpenAI Whisper
            with open(temp_file_path, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="es"
                )
            
            idea_text = transcript.text
            await self.process_idea(update, idea_text, "audio")
                
        except Exception as e:
            logging.error(f"Error procesando audio: {str(e)}")
            await update.message.reply_text(
                "❌ **Error procesando audio**\n\n"
                f"No se pudo transcribir el audio: {str(e)}"
            )
        finally:
            # Limpiar archivo temporal
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
    
    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar archivos de audio"""
        await update.message.reply_text("🎵 **Procesando archivo de audio...**\n⏳ Transcribiendo...")
        
        temp_file_path = None
        try:
            # Descargar el archivo de audio
            audio = update.message.audio
            file = await context.bot.get_file(audio.file_id)
            
            # Determinar extensión basada en mime_type
            mime_type = audio.mime_type or 'audio/mpeg'
            if 'mp3' in mime_type:
                suffix = '.mp3'
            elif 'mp4' in mime_type or 'm4a' in mime_type:
                suffix = '.m4a'
            elif 'wav' in mime_type:
                suffix = '.wav'
            else:
                suffix = '.mp3'  # default
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_file_path = temp_file.name
                await file.download_to_drive(temp_file_path)
            
            # Transcribir usando OpenAI Whisper
            with open(temp_file_path, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="es"
                )
            
            idea_text = transcript.text
            await self.process_idea(update, idea_text, "archivo de audio")
                
        except Exception as e:
            logging.error(f"Error procesando archivo de audio: {str(e)}")
            await update.message.reply_text(
                "❌ **Error procesando archivo**\n\n"
                f"No se pudo transcribir el archivo: {str(e)}"
            )
        finally:
            # Limpiar archivo temporal
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
    
    async def handle_text_idea(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar ideas enviadas por texto"""
        idea_text = update.message.text
        await self.process_idea(update, idea_text, "texto")
    
    async def process_idea(self, update: Update, idea_text: str, input_type: str):
        """Procesar una idea y generar artículo"""
        try:
            # Mostrar la idea transcrita/recibida
            await update.message.reply_text(
                f"💡 **Idea recibida ({input_type}):**\n\n"
                f'"{idea_text}"\n\n'
                f"🚀 **Generando artículo completo...**\n"
                f"⏳ Esto puede tomar 1-2 minutos..."
            )
            
            # Ejecutar workflow con la idea
            from agents.workflow import run_article_generation_sync_with_idea
            result = await asyncio.get_event_loop().run_in_executor(
                None, run_article_generation_sync_with_idea, idea_text
            )
            
            if result and result.get('is_complete'):
                await update.message.reply_text(
                    f"✅ **¡Artículo creado y publicado!**\n\n"
                    f"📰 **Título:** {result.get('title', 'N/A')}\n"
                    f"🆔 **WordPress ID:** {result.get('wordpress_id', 'N/A')}\n"
                    f"🔗 **Estado:** Publicado\n"
                    f"⏱️ **Tiempo:** {result.get('generation_time', 'N/A')} segundos\n\n"
                    f"💡 **Tu idea original:** {idea_text[:100]}{'...' if len(idea_text) > 100 else ''}\n\n"
                    f"¡Ya está disponible en tu sitio web!"
                )
            else:
                await update.message.reply_text(
                    f"❌ **Error generando artículo**\n\n"
                    f"💡 **Tu idea:** {idea_text[:100]}{'...' if len(idea_text) > 100 else ''}\n\n"
                    f"Hubo un problema procesando tu idea. Revisa los logs del sistema."
                )
                
        except Exception as e:
            logging.error(f"Error procesando idea: {str(e)}")
            await update.message.reply_text(
                f"❌ **Error del sistema**\n\n"
                f"💡 **Tu idea:** {idea_text[:100]}{'...' if len(idea_text) > 100 else ''}\n\n"
                f"No se pudo generar el artículo: {str(e)}"
            )

# Instancia global del bot
telegram_bot = None

def init_telegram_bot():
    """Inicializar el bot de Telegram"""
    global telegram_bot
    
    try:
        telegram_bot = TelegramBot()
        return telegram_bot.init_bot()
    except Exception as e:
        logging.error(f"Error inicializando bot de Telegram: {str(e)}")
        return None

# Mantener compatibilidad con funciones existentes
def send_article_for_review(article_data: Dict[str, Any]) -> Optional[str]:
    """Función de compatibilidad - ya no se usa para aprobación"""
    logging.info("send_article_for_review llamado pero ya no se usa para aprobación")
    return None