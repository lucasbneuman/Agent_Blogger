#!/usr/bin/env python3
"""
Bot simple de Telegram para probar el envío de audio
"""

import os
import asyncio
import logging
import tempfile
from dotenv import load_dotenv
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SimpleTelegramBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.openai_client = openai.OpenAI()
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN no encontrado en variables de entorno")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        await update.message.reply_text(
            "🤖 Agent Blogger Bot v2.0 - PRUEBA\n\n"
            "Envía un audio para probar la transcripción!"
        )
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar mensajes de voz"""
        await update.message.reply_text("🎤 Procesando audio...")
        
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
            
            await update.message.reply_text(
                f"✅ Audio transcrito:\n\n"
                f'"{idea_text}"\n\n'
                f"🎯 Transcripción completada!"
            )
                
        except Exception as e:
            logging.error(f"Error procesando audio: {str(e)}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
        finally:
            # Limpiar archivo temporal
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass  # Si no se puede eliminar, no importa

def main():
    """Función principal"""
    print("* Iniciando bot simple para pruebas...")
    
    try:
        bot = SimpleTelegramBot()
        
        # Crear aplicación
        app = Application.builder().token(bot.token).build()
        
        # Añadir handlers
        app.add_handler(CommandHandler("start", bot.start_command))
        app.add_handler(MessageHandler(filters.VOICE, bot.handle_voice))
        
        print("* Bot iniciado - Envía /start para comenzar")
        print("* Presiona Ctrl+C para detener")
        
        # Ejecutar
        app.run_polling(drop_pending_updates=True)
        
    except KeyboardInterrupt:
        print("\n* Bot detenido por el usuario")
    except Exception as e:
        print(f"* Error: {str(e)}")

if __name__ == "__main__":
    main()