import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime, timezone
from test_database import run_database_tests
from test_wordpress_connection import run_wordpress_tests
from test_full_workflow import run_test_suite

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/test_execution.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def create_logs_directory():
    """Crear directorio de logs si no existe"""
    os.makedirs('logs', exist_ok=True)
    os.makedirs('test_output', exist_ok=True)

def run_all_tests():
    """
    Ejecutar toda la suite de tests en orden.
    """
    
    create_logs_directory()
    
    logger.info("🚀 INICIANDO SUITE COMPLETA DE TESTS")
    logger.info(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    test_results = {}
    
    # 1. Tests de Base de Datos
    logger.info("\n" + "="*60)
    logger.info("🗃️  FASE 1: TESTS DE BASE DE DATOS")
    logger.info("="*60)
    
    try:
        test_results['database'] = run_database_tests()
    except Exception as e:
        logger.error(f"Error en tests de base de datos: {str(e)}")
        test_results['database'] = False
    
    # 2. Tests de WordPress (si la DB está OK)
    if test_results['database']:
        logger.info("\n" + "="*60)
        logger.info("🌐 FASE 2: TESTS DE WORDPRESS")
        logger.info("="*60)
        
        try:
            test_results['wordpress'] = run_wordpress_tests()
        except Exception as e:
            logger.error(f"Error en tests de WordPress: {str(e)}")
            test_results['wordpress'] = False
    else:
        logger.warning("⚠️  Saltando tests de WordPress (DB falló)")
        test_results['wordpress'] = False
    
    # 3. Tests de Workflow Completo (si todo está OK)
    if test_results['database']:
        logger.info("\n" + "="*60)
        logger.info("🤖 FASE 3: TESTS DE WORKFLOW COMPLETO")
        logger.info("="*60)
        
        try:
            test_results['workflow'] = run_test_suite()
        except Exception as e:
            logger.error(f"Error en tests de workflow: {str(e)}")
            test_results['workflow'] = False
    else:
        logger.warning("⚠️  Saltando tests de workflow (dependencias fallaron)")
        test_results['workflow'] = False
    
    # Generar reporte final
    generate_final_report(test_results)
    
    # Determinar éxito general
    critical_tests = ['database', 'workflow']  # WordPress no es crítico
    critical_passed = all(test_results.get(test, False) for test in critical_tests)
    
    return critical_passed, test_results

def generate_final_report(test_results):
    """Generar reporte final de todos los tests"""
    
    logger.info("\n" + "="*60)
    logger.info("📊 REPORTE FINAL DE TESTS")
    logger.info("="*60)
    
    # Resultados por categoría
    for category, success in test_results.items():
        icon = "✅" if success else "❌"
        name = category.upper()
        logger.info(f"{icon} {name}: {'PASS' if success else 'FAIL'}")
    
    # Resumen general
    total_tests = len(test_results)
    passed_tests = sum(1 for success in test_results.values() if success)
    
    logger.info(f"\nRESUMEN: {passed_tests}/{total_tests} categorías pasaron")
    
    # Estado general
    critical_tests = ['database', 'workflow']
    critical_passed = all(test_results.get(test, False) for test in critical_tests)
    
    if critical_passed:
        logger.info("🎉 SISTEMA LISTO PARA PRODUCCIÓN")
        status = "READY"
    else:
        logger.info("⚠️  SISTEMA NECESITA CORRECCIONES")
        status = "NEEDS_FIXES"
    
    # Guardar reporte en archivo
    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "test_results": test_results,
        "summary": {
            "total_categories": total_tests,
            "passed_categories": passed_tests,
            "critical_systems_ok": critical_passed
        },
        "recommendations": generate_recommendations(test_results)
    }
    
    # Guardar JSON
    import json
    with open('test_output/final_test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    logger.info("📁 Reporte completo guardado en: test_output/final_test_report.json")
    logger.info("="*60)

def generate_recommendations(test_results):
    """Generar recomendaciones basadas en los resultados"""
    
    recommendations = []
    
    if not test_results.get('database', False):
        recommendations.append("CRÍTICO: Corregir problemas de base de datos antes de continuar")
    
    if not test_results.get('wordpress', False):
        recommendations.append("IMPORTANTE: Verificar configuración de WordPress en .env")
        recommendations.append("- Revisar WP_URL, WP_USERNAME, WP_APP_PASSWORD")
        recommendations.append("- Verificar que el usuario tenga permisos de API")
    
    if not test_results.get('workflow', False):
        recommendations.append("CRÍTICO: Corregir workflow de generación de artículos")
        recommendations.append("- Verificar claves de OpenAI en .env")
        recommendations.append("- Revisar configuración de modelos de IA")
    
    if all(test_results.values()):
        recommendations.append("✅ Sistema completamente funcional")
        recommendations.append("- Listo para deployment en producción")
        recommendations.append("- Ejecutar tests periódicamente")
    
    return recommendations

def main():
    """Función principal"""
    
    print("🧪 SUITE COMPLETA DE TESTS - AGENT BLOGGER")
    print("="*60)
    
    try:
        success, results = run_all_tests()
        
        if success:
            print("\n🎉 TESTS COMPLETADOS EXITOSAMENTE")
            exit_code = 0
        else:
            print("\n⚠️  ALGUNOS TESTS FALLARON - REVISAR LOGS")
            exit_code = 1
        
        print("📁 Revisa los archivos en test_output/ para más detalles")
        return exit_code
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Tests interrumpidos por el usuario")
        return 130
    except Exception as e:
        logger.error(f"\n💥 ERROR FATAL EN TESTS: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)