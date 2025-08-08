#!/usr/bin/env python3
"""
Bot de Telegram FINAL - Sin emojis para evitar problemas de encoding en Windows
"""

import os
import tempfile
import logging
from dotenv import load_dotenv
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

load_dotenv()

# Configurar logging simple
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinalTelegramBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.openai_client = openai.OpenAI()
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN requerido")
    
    async def start(self, update: Update, context: CallbackContext):
        """Comando start"""
        await update.message.reply_text(
            "Agent Blogger Bot v2.0\n\n"
            "Envia un audio con tu idea y generare un articulo completo!\n\n"
            "Bot activo y funcional"
        )
    
    async def handle_voice_message(self, update: Update, context: CallbackContext):
        """Manejar audio"""
        await update.message.reply_text("Procesando audio...")
        
        temp_path = None
        try:
            # Descargar audio
            voice = update.message.voice
            file = await context.bot.get_file(voice.file_id)
            
            # Archivo temporal
            temp_file = tempfile.NamedTemporaryFile(suffix='.ogg', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # Descargar
            await file.download_to_drive(temp_path)
            
            # Transcribir
            with open(temp_path, 'rb') as f:
                result = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="es"
                )
            
            texto = result.text
            
            await update.message.reply_text(
                f"Transcripcion:\n\n\"{texto}\"\n\n"
                f"Ahora generando articulo completo..."
            )
            
            # Generar artículo
            await self.generate_article_from_idea(update, texto)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text(f"Error: {str(e)}")
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    async def handle_text_message(self, update: Update, context: CallbackContext):
        """Manejar texto"""
        texto = update.message.text
        
        await update.message.reply_text(
            f"Idea recibida:\n\n\"{texto}\"\n\n"
            f"Generando articulo completo..."
        )
        
        await self.generate_article_from_idea(update, texto)
    
    async def generate_article_from_idea(self, update: Update, idea: str):
        """Generar artículo usando la idea"""
        try:
            # Importar función de workflow
            from agents.workflow import run_article_generation_sync_with_idea
            
            # Ejecutar en hilo separado para no bloquear
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, run_article_generation_sync_with_idea, idea)
            
            if result and result.get('is_complete'):
                await update.message.reply_text(
                    f"Articulo publicado!\n\n"
                    f"Titulo: {result.get('title', 'N/A')}\n"
                    f"WordPress ID: {result.get('wordpress_id', 'N/A')}\n"
                    f"Estado: Publicado\n\n"
                    f"Disponible en tu sitio web!"
                )
            else:
                await update.message.reply_text("Error generando articulo")
                
        except Exception as e:
            logger.error(f"Error generando articulo: {e}")
            await update.message.reply_text(f"Error: {str(e)}")

def main():
    """Main function"""
    print("Iniciando Agent Blogger Bot v2.0...")
    
    try:
        bot = FinalTelegramBot()
        
        # Crear app
        app = Application.builder().token(bot.token).build()
        
        # Handlers
        app.add_handler(CommandHandler("start", bot.start))
        app.add_handler(MessageHandler(filters.VOICE, bot.handle_voice_message))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text_message))
        
        print("Bot configurado correctamente")
        print("Envia /start para comenzar")
        print("Envia un audio con tu idea")
        print("O escribe tu idea por texto")
        print("Ctrl+C para detener")
        
        # Run
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()