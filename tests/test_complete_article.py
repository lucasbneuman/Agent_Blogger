import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
from datetime import datetime, timezone
from database import init_db
from database.seed_data import run_seed
from agents.workflow import create_article_workflow, initialize_article_state
import logging

# Configurar logging para tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_test_environment():
    """Configurar entorno de prueba"""
    logger.info("Configurando entorno de prueba...")
    
    # Inicializar base de datos
    init_db()
    
    # Poblar con datos de prueba
    run_seed()
    
    logger.info("Entorno de prueba configurado")

def run_complete_article_workflow():
    """
    Ejecuta el workflow completo hasta obtener un artículo terminado, 
    pero SIN publicar en WordPress.
    """
    
    logger.info("=== INICIANDO TEST DE ARTÍCULO COMPLETO ===")
    
    # Configurar entorno
    setup_test_environment()
    
    # Crear workflow
    workflow = create_article_workflow()
    
    # Inicializar estado
    initial_state = initialize_article_state()
    
    try:
        start_time = datetime.now(timezone.utc)
        
        # Ejecutar workflow con configuración para evitar publicación
        config = {"recursion_limit": 50}
        
        # Modificar el estado inicial para evitar publicación
        initial_state.update({
            'skip_wordpress_publishing': True  # Flag para evitar publicación
        })
        
        logger.info("Ejecutando workflow de generación de artículo...")
        final_state = workflow.invoke(initial_state, config=config)
        
        end_time = datetime.now(timezone.utc)
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Workflow completado en {execution_time:.2f} segundos")
        logger.info(f"Estado final: {final_state.get('current_step')}")
        
        # Guardar resultado para análisis
        save_article_output(final_state, "complete_article_test")
        
        # Analizar el resultado
        analyze_article_result(final_state)
        
        return final_state
        
    except Exception as e:
        logger.error(f"Error en workflow: {str(e)}")
        
        # Retornar estado con error
        error_state = initial_state.copy()
        error_state.update({
            'errors': [f"Error en workflow: {str(e)}"],
            'current_step': 'workflow_error',
            'is_complete': True
        })
        
        return error_state

def analyze_article_result(state):
    """Analiza el resultado del artículo generado"""
    
    logger.info("\n" + "="*60)
    logger.info("📊 ANÁLISIS DEL ARTÍCULO GENERADO")
    logger.info("="*60)
    
    # Verificar componentes principales
    components = {
        'Keyword seleccionada': state.get('selected_keyword'),
        'Etapa seleccionada': state.get('selected_stage'),
        'Título del artículo': state.get('title'),
        'Contenido del artículo': state.get('content'),
        'Meta descripción': state.get('meta_description'),
        'Categoría': state.get('category'),
        'Etiquetas': state.get('tags'),
        'CTA título': state.get('cta_title'),
        'CTA contenido': state.get('cta_content'),
        'Enlaces internos': state.get('internal_links'),
        'Imagen destacada URL': state.get('featured_image_url'),
        'Imagen destacada Alt': state.get('featured_image_alt')
    }
    
    # Mostrar estado de cada componente
    complete_components = []
    missing_components = []
    
    for component, value in components.items():
        if value and (not isinstance(value, list) or len(value) > 0):
            complete_components.append(component)
            status = "✅"
            if isinstance(value, str):
                preview = value[:50] + "..." if len(value) > 50 else value
            elif isinstance(value, list):
                preview = f"{len(value)} elementos"
            else:
                preview = str(value)
            logger.info(f"{status} {component}: {preview}")
        else:
            missing_components.append(component)
            logger.info(f"❌ {component}: FALTANTE")
    
    # Estadísticas del contenido
    if state.get('content'):
        content = state.get('content')
        word_count = len(content.split())
        char_count = len(content)
        logger.info(f"\n📝 ESTADÍSTICAS DEL CONTENIDO:")
        logger.info(f"   - Palabras: {word_count}")
        logger.info(f"   - Caracteres: {char_count}")
    
    # Estadísticas del título
    if state.get('title'):
        title = state.get('title')
        logger.info(f"\n📰 ESTADÍSTICAS DEL TÍTULO:")
        logger.info(f"   - Longitud: {len(title)} caracteres")
        logger.info(f"   - Título: '{title}'")
    
    # Estadísticas de meta descripción
    if state.get('meta_description'):
        meta = state.get('meta_description')
        logger.info(f"\n🏷️  ESTADÍSTICAS DE META DESCRIPCIÓN:")
        logger.info(f"   - Longitud: {len(meta)} caracteres")
        logger.info(f"   - Meta: '{meta}'")
    
    # Estado del workflow
    logger.info(f"\n🔄 ESTADO DEL WORKFLOW:")
    logger.info(f"   - Paso actual: {state.get('current_step')}")
    logger.info(f"   - Completado: {state.get('is_complete', False)}")
    logger.info(f"   - Necesita revisión: {state.get('needs_revision', False)}")
    logger.info(f"   - Errores: {len(state.get('errors') or [])}")
    logger.info(f"   - Advertencias: {len(state.get('warnings') or [])}")
    logger.info(f"   - Reintentos: {state.get('retry_count', 0)}")
    
    # Mostrar errores si los hay
    if state.get('errors'):
        logger.info(f"\n❌ ERRORES ENCONTRADOS:")
        for i, error in enumerate(state.get('errors', []), 1):
            logger.info(f"   {i}. {error}")
    
    # Mostrar advertencias si las hay
    if state.get('warnings'):
        logger.info(f"\n⚠️  ADVERTENCIAS:")
        for i, warning in enumerate(state.get('warnings', []), 1):
            logger.info(f"   {i}. {warning}")
    
    # Resumen final
    logger.info(f"\n" + "="*60)
    logger.info(f"📈 RESUMEN:")
    logger.info(f"   - Componentes completos: {len(complete_components)}/{len(components)}")
    logger.info(f"   - Componentes faltantes: {len(missing_components)}")
    
    if len(complete_components) >= 8:  # Mínimo 8 componentes para considerar éxito
        logger.info(f"   - Estado: ✅ ARTÍCULO COMPLETO")
    elif len(complete_components) >= 5:
        logger.info(f"   - Estado: ⚠️  ARTÍCULO PARCIAL")
    else:
        logger.info(f"   - Estado: ❌ ARTÍCULO INCOMPLETO")
    
    logger.info("="*60)
    
    return {
        'complete_components': complete_components,
        'missing_components': missing_components,
        'total_components': len(components),
        'completion_percentage': (len(complete_components) / len(components)) * 100
    }

def save_article_output(result, test_name):
    """Guarda el resultado del test en un archivo JSON"""
    
    # Crear directorio de salida
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Crear archivo con timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/{test_name}_{timestamp}.json"
    
    # Preparar datos para JSON (convertir datetime y otros objetos no serializables)
    json_result = prepare_for_json(result)
    
    # Guardar archivo
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Resultado guardado en: {filename}")

def prepare_for_json(obj):
    """Prepara un objeto para serialización JSON"""
    if isinstance(obj, dict):
        return {k: prepare_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [prepare_for_json(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return prepare_for_json(obj.__dict__)
    else:
        return obj

def test_article_components():
    """Test específico para verificar todos los componentes del artículo"""
    
    logger.info("🧪 Ejecutando test de componentes de artículo...")
    
    result = run_complete_article_workflow()
    analysis = analyze_article_result(result)
    
    # Verificar que se generen los componentes mínimos
    required_components = [
        'Keyword seleccionada',
        'Etapa seleccionada', 
        'Título del artículo',
        'Contenido del artículo',
        'Meta descripción',
        'Categoría'
    ]
    
    missing_required = [comp for comp in required_components 
                       if comp in analysis['missing_components']]
    
    if missing_required:
        logger.error(f"❌ FALTAN COMPONENTES CRÍTICOS: {', '.join(missing_required)}")
        return False
    else:
        logger.info(f"✅ TODOS LOS COMPONENTES CRÍTICOS PRESENTES")
        return True

if __name__ == "__main__":
    logger.info("🚀 INICIANDO TEST DE ARTÍCULO COMPLETO")
    
    # Ejecutar test principal
    success = test_article_components()
    
    if success:
        logger.info("\n🎉 TEST COMPLETADO EXITOSAMENTE")
        logger.info("📁 Revisa los archivos en test_output/ para ver el artículo generado")
        
        # Generar visualización HTML automáticamente
        try:
            from utils.article_visualizer import visualize_latest_article
            import webbrowser
            import os
            
            logger.info("🎨 Generando visualización HTML...")
            html_file = visualize_latest_article()
            
            # Abrir en navegador
            full_path = os.path.abspath(html_file)
            try:
                webbrowser.open(f'file:///{full_path.replace(os.sep, "/")}')
                logger.info(f"🌐 Visualización abierta en navegador: {html_file}")
            except Exception:
                logger.info(f"📋 Visualización generada: {html_file}")
                
        except Exception as e:
            logger.warning(f"⚠️ No se pudo generar visualización HTML: {str(e)}")
            
    else:
        logger.error("\n❌ TEST FALLÓ - Revisa los logs para más detalles")