#!/usr/bin/env python3
"""
Bot unificado de Telegram para recibir ideas de audio y generar artículos.
"""

import logging
import asyncio
from integrations.telegram_bot import init_telegram_bot

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    """Función principal del bot"""
    
    print("* Iniciando Agent Blogger Bot v2.0...")
    print("* Ahora con soporte para ideas de audio!")
    
    app = None
    try:
        # Inicializar bot
        app = init_telegram_bot()
        
        if not app:
            print("* Error inicializando bot de Telegram")
            return
        
        print("* Bot de Telegram iniciado correctamente")
        print("* Listo para recibir ideas de audio, texto y generar articulos automaticos")
        print("* Envia /start al bot para comenzar")
        print("")
        print("Funcionalidades disponibles:")
        print("* Envia un audio con tu idea")
        print("* Escribe una idea por texto") 
        print("* /generate - Generar articulo automatico")
        print("* /help - Ver ayuda completa")
        print("")
        print("Presiona Ctrl+C para detener")
        
        # Ejecutar bot
        await app.run_polling(drop_pending_updates=True)
        
    except KeyboardInterrupt:
        print("\\nBot detenido por el usuario")
    except Exception as e:
        logging.error(f"Error en el bot: {str(e)}")
        print(f"* Error: {str(e)}")
    finally:
        # Limpiar recursos
        if app:
            try:
                await app.stop()
                await app.shutdown()
            except:
                pass

if __name__ == "__main__":
    asyncio.run(main())