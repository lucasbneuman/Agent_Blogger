#!/usr/bin/env python3
"""
Agent Blogger v2.0 - Generador automático de artículos con IA
Sistema principal con generación automática de artículos
"""

import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('agent_blogger.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Verificar configuración del entorno"""
    
    logger.info("Verificando configuracion del entorno...")
    
    required_vars = [
        'OPENAI_API_KEY',
        'WP_URL', 
        'WP_USERNAME',
        'WP_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
        logger.error("Configura tu archivo .env con todas las variables necesarias")
        return False
    
    logger.info("Variables de entorno configuradas correctamente")
    return True

def init_database():
    """Inicializar base de datos"""

    logger.info("Inicializando base de datos...")

    try:
        from database import init_db
        from database.seed_data import run_seed

        init_db()
        run_seed()

        logger.info("Base de datos inicializada correctamente")

        # NUEVO: Sincronizar posts existentes de WordPress
        logger.info("Sincronizando posts existentes de WordPress...")
        try:
            from wordpress_sync import sync_wordpress_to_local_db
            sync_wordpress_to_local_db()
            logger.info("Sincronización de WordPress completada")
        except Exception as sync_error:
            logger.warning(f"No se pudo sincronizar WordPress: {str(sync_error)}")
            logger.warning("Continuando sin sincronización...")

        return True

    except Exception as e:
        logger.error(f"Error inicializando base de datos: {str(e)}")
        return False

def run_continuous_generation():
    """Ejecutar generación continua de artículos"""
    
    logger.info("MODO: Generacion continua de articulos")
    logger.info("Sistema Agent Blogger v2.0 iniciado")
    logger.info("Ctrl+C para detener")
    
    article_count = 0
    
    try:
        while True:
            article_count += 1
            logger.info(f"\n--- GENERANDO ARTICULO #{article_count} ---")
            
            # Generar artículo
            success = generate_single_article()
            
            if success:
                logger.info(f"Articulo #{article_count} completado exitosamente")
            else:
                logger.warning(f"Articulo #{article_count} fallo - continuando...")
            
            # Esperar antes del siguiente artículo
            wait_time = int(os.getenv('ARTICLE_INTERVAL_MINUTES', 60)) * 60
            logger.info(f"Esperando {wait_time//60} minutos hasta el proximo articulo...")
            
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        logger.info(f"\nProceso detenido por usuario. Total generados: {article_count}")
    except Exception as e:
        logger.error(f"Error en generacion continua: {str(e)}")

def generate_single_article():
    """Generar un solo artículo"""
    
    try:
        from agents.workflow import run_article_generation_sync
        
        start_time = time.time()
        result = run_article_generation_sync()
        end_time = time.time()
        
        # Mostrar resultados
        execution_time = int(end_time - start_time)
        
        if result and result.get('is_complete'):
            logger.info(f"RESULTADO: Articulo completado en {execution_time} segundos")
            logger.info(f"Titulo: {result.get('title', 'N/A')}")
            logger.info(f"WordPress ID: {result.get('wordpress_id', 'N/A')}")
            
            if result.get('telegram_idea_mode'):
                logger.info(f"Origen: Idea de Telegram")
                logger.info(f"Idea: {result.get('telegram_idea', 'N/A')[:100]}...")
            else:
                logger.info(f"Origen: Generacion automatica")
                logger.info(f"Keyword: {result.get('selected_keyword', 'N/A')}")
            
            errors = result.get('errors', [])
            if errors:
                logger.warning(f"Errores: {len(errors)}")
                for error in errors[-2:]:  # Últimos 2 errores
                    logger.warning(f"  - {error}")
            
            return True
        else:
            logger.error("Articulo no se pudo completar")
            return False
            
    except Exception as e:
        logger.error(f"Error generando articulo: {str(e)}")
        return False

def show_help():
    """Mostrar ayuda"""
    
    print("""
Agent Blogger v2.0 - Generador automatico de articulos

USO:
    python main.py [comando]

COMANDOS:
    generate    - Generar un solo articulo
    continuous  - Generacion continua (por defecto)
    help        - Mostrar esta ayuda

EJEMPLOS:
    python main.py              # Generacion continua
    python main.py generate     # Un solo articulo
    python main.py continuous   # Generacion continua explicita

CONFIGURACION (.env):
    OPENAI_API_KEY=tu_clave_openai
    WP_URL=https://tu-sitio.com
    WP_USERNAME=tu_usuario
    WP_PASSWORD=tu_app_password
    
    # Opcional para modo continuo
    ARTICLE_INTERVAL_MINUTES=60  # Intervalo entre articulos

TELEGRAM:
    Para usar ideas de audio, ejecuta en paralelo:
    python telegram_unified.py
""")

def main():
    """Función principal"""
    
    print("=" * 60)
    print("AGENT BLOGGER V2.0 - SISTEMA AUTOMATICO")
    print("=" * 60)
    print("* Generacion automatica de articulos")
    print("* Ideas de audio via Telegram")  
    print("* Publicacion directa en WordPress")
    print("* Imagenes contextuales y realistas")
    print("=" * 60)
    
    # Obtener comando
    command = sys.argv[1] if len(sys.argv) > 1 else 'continuous'
    
    if command == 'help':
        show_help()
        return
    
    # Verificar entorno
    if not check_environment():
        sys.exit(1)
    
    # Inicializar database
    if not init_database():
        sys.exit(1)
    
    # Ejecutar comando
    try:
        if command == 'generate':
            success = generate_single_article()
            if success:
                logger.info("Proceso completado exitosamente")
            else:
                logger.error("Proceso fallo")
                sys.exit(1)
                
        elif command == 'continuous':
            run_continuous_generation()
            
        else:
            logger.error(f"Comando desconocido: {command}")
            logger.info("Usa 'python main.py help' para ver comandos disponibles")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Proceso interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()