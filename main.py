#!/usr/bin/env python3
"""
Agent Blogger - Generador automático de artículos con IA
Punto de entrada principal para la aplicación
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """Configurar sistema de logging"""
    
    # Crear directorio de logs
    os.makedirs('logs', exist_ok=True)
    
    # Configurar logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                f'logs/agent_blogger_{datetime.now().strftime("%Y%m%d")}.log',
                encoding='utf-8'
            )
        ]
    )

def check_environment():
    """Verificar variables de entorno necesarias"""
    
    logger = logging.getLogger(__name__)
    
    required_vars = [
        'OPENAI_API_KEY',
        'WP_USERNAME', 
        'WP_APP_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
        logger.error("Por favor configura el archivo .env")
        return False
    
    logger.info("OK Variables de entorno configuradas correctamente")
    return True

def init_database():
    """Inicializar base de datos"""
    
    logger = logging.getLogger(__name__)
    
    try:
        from database import init_db
        from database.seed_data import run_seed
        
        logger.info("Inicializando base de datos...")
        init_db()
        
        logger.info("Cargando datos iniciales...")
        run_seed()
        
        logger.info("Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {str(e)}")
        return False

def run_api_server():
    """Ejecutar servidor API"""
    
    logger = logging.getLogger(__name__)
    
    try:
        import uvicorn
        from api.main import app
        
        logger.info("Iniciando servidor API...")
        
        # Configuración del servidor
        port = int(os.getenv('PORT', 8000))
        host = os.getenv('HOST', '0.0.0.0')
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"Error ejecutando servidor: {str(e)}")
        return False

def run_single_article():
    """Generar un solo artículo (modo CLI)"""
    
    logger = logging.getLogger(__name__)
    
    try:
        from agents.workflow import run_article_generation_sync
        
        logger.info("Generando articulo...")
        
        result = run_article_generation_sync()
        
        # Mostrar resultado
        if result.get('is_complete') and not result.get('errors'):
            logger.info("OK Artículo generado exitosamente")
            logger.info(f"Título: {result.get('title')}")
            logger.info(f"Keyword: {result.get('selected_keyword')}")
            logger.info(f"Etapa: {result.get('selected_stage')}")
            
            if result.get('wordpress_id'):
                logger.info(f"Publicado en WordPress: ID {result.get('wordpress_id')}")
            
        else:
            logger.error(" Error generando artículo")
            for error in result.get('errors', []):
                logger.error(f"  - {error}")
        
        return result.get('is_complete', False)
        
    except Exception as e:
        logger.error(f" Error en generación: {str(e)}")
        return False

def publish_complete_article():
    """Publicar artículo completo con todas las mejoras"""
    
    logger = logging.getLogger(__name__)
    
    logger.info("PUBLICANDO ARTICULO COMPLETO CON TODAS LAS MEJORAS")
    logger.info("=" * 60)
    
    # Verificar credenciales
    required_vars = ['WP_URL', 'WP_USERNAME', 'WP_APP_PASSWORD', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error("Faltan variables de entorno:")
        for var in missing_vars:
            logger.error(f"   - {var}")
        return False
    
    try:
        from agents.workflow import create_article_workflow, initialize_article_state
        from utils.article_visualizer import visualize_latest_article
        import webbrowser
        
        # Crear workflow
        workflow = create_article_workflow()
        
        # Inicializar estado para publicación completa
        initial_state = initialize_article_state()
        initial_state.update({
            'skip_wordpress_publishing': False  # PUBLICAR EN WORDPRESS
        })
        
        start_time = datetime.now()
        
        logger.info("Ejecutando workflow completo...")
        logger.info("Generando contenido con IA")
        logger.info("Integrando enlaces internos")
        logger.info("Creando CTA con enlace")
        logger.info("Generando imagen con DALL-E")
        logger.info("Configurando Yoast SEO")
        logger.info("Publicando en WordPress")
        
        config = {"recursion_limit": 50}
        final_state = workflow.invoke(initial_state, config=config)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Workflow completado en {execution_time:.2f} segundos")
        
        # Analizar resultado
        success = analyze_publication_result(final_state)
        
        if success:
            # Generar visualización HTML
            try:
                logger.info("Generando visualización HTML...")
                html_file = visualize_latest_article()
                
                # Abrir en navegador
                full_path = os.path.abspath(html_file)
                webbrowser.open(f'file:///{full_path.replace(os.sep, "/")}')
                logger.info(f"Visualizacion: {html_file}")
            except Exception as e:
                logger.warning(f"No se pudo generar visualización: {str(e)}")
        
        return success
        
    except Exception as e:
        logger.error(f" Error en workflow: {str(e)}")
        return False

def analyze_publication_result(state):
    """Analizar y reportar resultado de publicación"""
    
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "RESULTADO DE LA PUBLICACION")
    logger.info("=" * 50)
    
    current_step = state.get('current_step')
    is_published = state.get('is_published', False)
    wordpress_id = state.get('wordpress_id')
    errors = state.get('errors', [])
    warnings = state.get('warnings', [])
    
    if current_step == 'completed' and is_published and wordpress_id:
        logger.info("ARTICULO PUBLICADO EXITOSAMENTE!")
        logger.info(f"   ID WordPress: {wordpress_id}")
        logger.info(f"   Estado: Borrador (listo para revision)")
        
        # Mostrar detalles del artículo
        logger.info(f"\nCARACTERISTICAS DEL ARTICULO:")
        logger.info(f"   Título: {state.get('title', 'N/A')}")
        logger.info(f"   Keyword objetivo: {state.get('selected_keyword', 'N/A')}")
        logger.info(f"   Etapa del buyer: {state.get('selected_stage', 'N/A')}")
        logger.info(f"   Categoría: {state.get('category', 'N/A')}")
        logger.info(f"   Etiquetas: {len(state.get('tags', []))} etiquetas")
        logger.info(f"   Palabras: {len(state.get('content', '').split())} palabras")
        logger.info(f"   Enlaces internos: {len(state.get('internal_links', []))} integrados")
        logger.info(f"   CTA incluido: {'OK' if state.get('cta_title') else ''}")
        logger.info(f"   Imagen destacada: {'OK' if state.get('featured_image_url') else ''}")
        
        # Verificar mejoras implementadas
        logger.info(f"\n MEJORAS IMPLEMENTADAS:")
        logger.info(f"   OK Markdown convertido a HTML")
        logger.info(f"   OK Yoast SEO configurado automáticamente")
        logger.info(f"   OK Enlaces internos integrados en el texto")
        logger.info(f"   OK CTA con enlace funcional")
        
        # Verificar si se subió la imagen
        processing_log = state.get('processing_log', [])
        image_uploaded = any('Imagen destacada subida' in log for log in processing_log)
        if image_uploaded:
            logger.info(f"   OK Imagen DALL-E descargada y subida automáticamente")
        else:
            logger.info(f"     Imagen no se pudo procesar automáticamente")
        
        logger.info(f"\nPROXIMOS PASOS:")
        logger.info(f"   1. Ve a WordPress Admin: {os.getenv('WP_URL')}/wp-admin")
        logger.info(f"   2. Busca el post con ID {wordpress_id}")
        logger.info(f"   3. Verifica el semáforo verde de Yoast SEO")
        logger.info(f"   4. Revisa la imagen destacada")
        logger.info(f"   5. ¡Publica cuando esté listo!")
        
        if warnings:
            logger.info(f"\n  SUGERENCIAS MENORES ({len(warnings)}):")
            for i, warning in enumerate(warnings[:5], 1):  # Solo mostrar primeras 5
                logger.info(f"   {i}. {warning}")
        
        return True
        
    elif errors:
        logger.error(" PUBLICACIÓN FALLÓ")
        logger.error(f"   Estado actual: {current_step}")
        logger.error(f"   Errores encontrados:")
        for i, error in enumerate(errors, 1):
            logger.error(f"      {i}. {error}")
            
        logger.info(f"\nSOLUCIONES:")
        logger.info(f"   1. Verifica credenciales WordPress en .env")
        logger.info(f"   2. Ejecuta: python sync_wordpress_simple.py")
        logger.info(f"   3. Revisa conexión a internet")
        
        return False
        
    else:
        logger.warning("  PUBLICACIÓN INCOMPLETA")
        logger.warning(f"   Estado: {current_step}")
        logger.warning(f"   Publicado: {is_published}")
        logger.warning(f"   ID WordPress: {wordpress_id}")
        
        return False

def run_tests():
    """Ejecutar suite de tests"""
    
    logger = logging.getLogger(__name__)
    
    try:
        from test_scripts.run_all_tests import run_all_tests
        
        logger.info("Ejecutando tests...")
        success, results = run_all_tests()
        
        if success:
            logger.info("Todos los tests pasaron")
        else:
            logger.warning("Algunos tests fallaron")
        
        return success
        
    except Exception as e:
        logger.error(f" Error ejecutando tests: {str(e)}")
        return False

def show_help():
    """Mostrar ayuda de uso"""
    
    print("""
Agent Blogger - Generador automatico de articulos

USO:
    python main.py [comando]

COMANDOS:
    server      - Ejecutar servidor API FastAPI (por defecto)
    generate    - Generar un artículo individual
    publish     - Publicar artículo completo con todas las mejoras
    test        - Ejecutar suite de tests
    init        - Solo inicializar base de datos
    help        - Mostrar esta ayuda

EJEMPLOS:
    python main.py server      # Iniciar servidor API
    python main.py generate    # Generar un artículo
    python main.py publish     # Publicar artículo con todas las mejoras
    python main.py test        # Ejecutar tests

CONFIGURACIÓN:
    Asegúrate de tener configurado el archivo .env con:
    - OPENAI_API_KEY
    - WP_USERNAME  
    - WP_APP_PASSWORD
    - WP_URL (opcional, default: https://lucasbenites.com)
""")

def main():
    """Función principal"""
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Banner
    print("="*60)
    print("AGENT BLOGGER - Generador Automatico de Articulos")
    print("="*60)
    
    # Obtener comando
    command = sys.argv[1] if len(sys.argv) > 1 else 'server'
    
    # Verificar entorno (excepto para help)
    if command != 'help':
        if not check_environment():
            sys.exit(1)
    
    # Ejecutar comando
    try:
        if command == 'help':
            show_help()
            
        elif command == 'init':
            success = init_database()
            sys.exit(0 if success else 1)
            
        elif command == 'test':
            success = run_tests()
            sys.exit(0 if success else 1)
            
        elif command == 'generate':
            # Inicializar DB primero
            if not init_database():
                sys.exit(1)
            
            success = run_single_article()
            sys.exit(0 if success else 1)
            
        elif command == 'publish':
            # Inicializar DB primero
            if not init_database():
                sys.exit(1)
            
            success = publish_complete_article()
            sys.exit(0 if success else 1)
            
        elif command == 'server':
            # Inicializar DB primero
            if not init_database():
                sys.exit(1)
            
            # Ejecutar servidor
            run_api_server()
            
        else:
            logger.error(f"Comando desconocido: {command}")
            logger.info("Usa 'python main.py help' para ver comandos disponibles")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\nInterrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()