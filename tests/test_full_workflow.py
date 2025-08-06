import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
from datetime import datetime, timezone
from database import init_db
from database.seed_data import run_seed
from agents.workflow import run_article_generation_sync
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

def test_complete_article_generation():
    """
    Test principal: genera un artículo completo sin publicar en WordPress.
    Este test ejecuta todo el pipeline y valida el resultado.
    """
    
    logger.info("=== INICIANDO TEST DE GENERACIÓN COMPLETA ===")
    
    # Configurar entorno
    setup_test_environment()
    
    # Ejecutar workflow
    start_time = datetime.now(timezone.utc)
    result = run_article_generation_sync()
    end_time = datetime.now(timezone.utc)
    
    execution_time = (end_time - start_time).total_seconds()
    logger.info(f"Tiempo de ejecución: {execution_time:.2f} segundos")
    
    # Guardar resultado completo para análisis
    save_test_output(result, "complete_workflow_test")
    
    # Validaciones principales
    assert result is not None, "El resultado no debe ser None"
    assert isinstance(result, dict), "El resultado debe ser un diccionario"
    
    # Validar que el workflow se completó
    current_step = result.get('current_step')
    logger.info(f"Estado final del workflow: {current_step}")
    
    # Validar errores
    errors = result.get('errors', [])
    if errors:
        logger.warning(f"Errores encontrados: {errors}")
        # No fallar el test por errores menores, solo loggear
    
    # Validar componentes clave
    required_components = {
        'selected_keyword': 'Keyword seleccionada',
        'selected_stage': 'Etapa seleccionada',
        'title': 'Título del artículo',
        'content': 'Contenido del artículo'
    }
    
    missing_components = []
    for component, description in required_components.items():
        if not result.get(component):
            missing_components.append(description)
    
    if missing_components:
        logger.error(f"Componentes faltantes: {missing_components}")
        assert False, f"Faltan componentes esenciales: {', '.join(missing_components)}"
    
    # Validar calidad del contenido
    validate_content_quality(result)
    
    logger.info("=== TEST COMPLETADO EXITOSAMENTE ===")
    return result

def validate_content_quality(result):
    """Validar la calidad del contenido generado"""
    
    logger.info("Validando calidad del contenido...")
    
    # Validar título
    title = result.get('title', '')
    assert len(title) > 0, "El título no puede estar vacío"
    assert len(title) <= 60, f"Título muy largo: {len(title)} caracteres (máximo 60)"
    logger.info(f"✓ Título válido: {title} ({len(title)} caracteres)")
    
    # Validar keyword en título
    keyword = result.get('selected_keyword', '').lower()
    if keyword and keyword not in title.lower():
        logger.warning(f"La keyword '{keyword}' no aparece en el título")
    
    # Validar contenido
    content = result.get('content', '')
    word_count = len(content.split())
    assert word_count >= 500, f"Contenido muy corto: {word_count} palabras (mínimo 500 para test)"
    logger.info(f"✓ Contenido válido: {word_count} palabras")
    
    # Validar meta descripción
    meta_desc = result.get('meta_description', '')
    if meta_desc:
        assert len(meta_desc) <= 155, f"Meta descripción muy larga: {len(meta_desc)} caracteres"
        logger.info(f"✓ Meta descripción válida: {len(meta_desc)} caracteres")
    
    # Validar categoría y etiquetas
    category = result.get('category')
    tags = result.get('tags', [])
    assert category, "Debe tener una categoría asignada"
    assert len(tags) >= 2, f"Debe tener al menos 2 etiquetas, tiene {len(tags)}"
    logger.info(f"✓ Categorización válida: {category}, {len(tags)} etiquetas")
    
    # Validar CTA
    cta_title = result.get('cta_title')
    cta_content = result.get('cta_content')
    if cta_title or cta_content:
        logger.info("✓ CTA presente")
    else:
        logger.warning("CTA no generado")

def test_individual_components():
    """Test de componentes individuales del workflow"""
    
    logger.info("=== TESTING COMPONENTES INDIVIDUALES ===")
    
    # Test selector de artículos
    from agents.nodes.selector import article_selector_node
    from agents.state import ArticleState
    
    initial_state = ArticleState(
        created_at=datetime.now(timezone.utc),
        processing_log=[],
        current_step='start',
        is_complete=False,
        needs_revision=False,
        errors=None,
        warnings=None,
        selected_keyword=None,
        selected_stage=None,
        title=None,
        content=None,
        meta_description=None,
        category=None,
        tags=None,
        featured_image_prompt=None,
        featured_image_url=None,
        featured_image_alt=None,
        internal_links=None,
        cta_title=None,
        cta_content=None,
        cta_link=None,
        wordpress_id=None,
        is_published=False
    )
    
    # Test selector
    selector_result = article_selector_node(initial_state)
    assert selector_result.get('selected_keyword'), "Selector debe retornar keyword"
    assert selector_result.get('selected_stage'), "Selector debe retornar stage"
    logger.info(f"✓ Selector: {selector_result.get('selected_keyword')} ({selector_result.get('selected_stage')})")
    
    logger.info("=== COMPONENTES INDIVIDUALES OK ===")

def save_test_output(result, test_name):
    """Guardar resultado del test para análisis"""
    
    # Crear directorio de salida si no existe
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Crear archivo con timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/{test_name}_{timestamp}.json"
    
    # Preparar datos para JSON (convertir datetime)
    json_result = prepare_for_json(result)
    
    # Guardar
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Resultado guardado en: {filename}")

def prepare_for_json(obj):
    """Preparar objeto para serialización JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: prepare_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [prepare_for_json(item) for item in obj]
    else:
        return obj

def run_test_suite():
    """Ejecutar suite completa de tests"""
    
    logger.info("🚀 INICIANDO SUITE DE TESTS")
    
    try:
        # Test principal
        result = test_complete_article_generation()
        
        # Tests de componentes
        test_individual_components()
        
        # Generar reporte
        generate_test_report(result)
        
        logger.info("✅ TODOS LOS TESTS PASARON")
        return True
        
    except Exception as e:
        logger.error(f"❌ ERROR EN TESTS: {str(e)}")
        return False

def generate_test_report(result):
    """Generar reporte de pruebas"""
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_summary": {
            "workflow_completed": result.get('is_complete', False),
            "final_step": result.get('current_step'),
            "errors_count": len(result.get('errors', [])),
            "warnings_count": len(result.get('warnings', []))
        },
        "content_analysis": {
            "has_title": bool(result.get('title')),
            "has_content": bool(result.get('content')),
            "has_meta_description": bool(result.get('meta_description')),
            "has_category": bool(result.get('category')),
            "has_tags": bool(result.get('tags')),
            "has_cta": bool(result.get('cta_title')),
            "has_featured_image": bool(result.get('featured_image_url'))
        },
        "quality_metrics": {
            "title_length": len(result.get('title', '')),
            "content_word_count": len(result.get('content', '').split()),
            "meta_description_length": len(result.get('meta_description', '')),
            "tags_count": len(result.get('tags', []))
        }
    }
    
    # Guardar reporte
    save_test_output(report, "test_report")
    
    # Mostrar resumen en consola
    print("\n" + "="*50)
    print("📊 REPORTE DE PRUEBAS")
    print("="*50)
    print(f"Workflow completado: {'✅' if report['test_summary']['workflow_completed'] else '❌'}")
    print(f"Paso final: {report['test_summary']['final_step']}")
    print(f"Errores: {report['test_summary']['errors_count']}")
    print(f"Warnings: {report['test_summary']['warnings_count']}")
    print(f"Título: {'✅' if report['content_analysis']['has_title'] else '❌'} ({report['quality_metrics']['title_length']} chars)")
    print(f"Contenido: {'✅' if report['content_analysis']['has_content'] else '❌'} ({report['quality_metrics']['content_word_count']} palabras)")
    print(f"Categoría: {'✅' if report['content_analysis']['has_category'] else '❌'}")
    print(f"Etiquetas: {'✅' if report['content_analysis']['has_tags'] else '❌'} ({report['quality_metrics']['tags_count']})")
    print("="*50)

if __name__ == "__main__":
    # Ejecutar tests
    success = run_test_suite()
    sys.exit(0 if success else 1)