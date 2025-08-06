import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wordpress.client import WordPressClient
from wordpress.sync import full_sync
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_wordpress_connection():
    """Test de conexión básica con WordPress"""
    
    logger.info("=== TEST DE CONEXIÓN WORDPRESS ===")
    
    try:
        wp_client = WordPressClient()
        
        # Test conexión
        connection_ok = wp_client.test_connection()
        logger.info(f"Conexión: {'✅ OK' if connection_ok else '❌ FALLO'}")
        
        if not connection_ok:
            logger.error("No se pudo conectar con WordPress")
            return False
        
        # Test obtener categorías
        categories = wp_client.get_categories()
        logger.info(f"Categorías obtenidas: {len(categories)}")
        
        for cat in categories[:5]:  # Mostrar primeras 5
            logger.info(f"  - {cat['name']} (id: {cat['id']})")
        
        # Test obtener etiquetas
        tags = wp_client.get_tags()
        logger.info(f"Etiquetas obtenidas: {len(tags)}")
        
        # Test obtener posts
        posts = wp_client.get_posts(per_page=5)
        logger.info(f"Posts obtenidos: {len(posts)}")
        
        for post in posts:
            logger.info(f"  - {post['title']['rendered']} (id: {post['id']})")
        
        logger.info("✅ Test de conexión WordPress completado")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test WordPress: {str(e)}")
        return False

def test_wordpress_sync():
    """Test de sincronización con WordPress"""
    
    logger.info("=== TEST DE SINCRONIZACIÓN ===")
    
    try:
        # Realizar sincronización completa
        results = full_sync()
        
        logger.info("Resultados de sincronización:")
        logger.info(f"  - Categorías: {results['categories']}")
        logger.info(f"  - Etiquetas: {results['tags']}")
        logger.info(f"  - Artículos: {results['articles']}")
        
        logger.info("✅ Test de sincronización completado")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en sincronización: {str(e)}")
        return False

def test_create_test_post():
    """Test de creación de post de prueba (NO se publica)"""
    
    logger.info("=== TEST DE CREACIÓN DE POST ===")
    
    try:
        wp_client = WordPressClient()
        
        # Datos de prueba
        test_post_data = {
            'title': f'Test Post - {os.environ.get("USER", "Bot")} - No publicar',
            'content': '''
            <p>Este es un post de prueba creado por el sistema de testing.</p>
            <p>NO debe ser publicado en el sitio real.</p>
            <p>Por favor eliminar si aparece publicado.</p>
            ''',
            'excerpt': 'Post de prueba del sistema de generación automática',
            'status': 'draft'  # IMPORTANTE: Solo borrador
        }
        
        # Crear post
        result = wp_client.create_post(**test_post_data)
        
        if result:
            logger.info(f"✅ Post de prueba creado exitosamente")
            logger.info(f"  - ID: {result['id']}")
            logger.info(f"  - URL: {result['link']}")
            logger.info(f"  - Estado: {result['status']}")
            
            # Eliminar el post de prueba inmediatamente
            delete_success = wp_client.delete_post(result['id'], force=True)
            logger.info(f"Post de prueba eliminado: {'✅' if delete_success else '❌'}")
            
            return True
        else:
            logger.error("❌ No se pudo crear post de prueba")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error creando post de prueba: {str(e)}")
        return False

def run_wordpress_tests():
    """Ejecutar todos los tests de WordPress"""
    
    logger.info("🚀 INICIANDO TESTS DE WORDPRESS")
    
    tests = [
        ("Conexión", test_wordpress_connection),
        ("Sincronización", test_wordpress_sync),
        ("Creación de post", test_create_test_post)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Ejecutando: {test_name} ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Error en {test_name}: {str(e)}")
            results[test_name] = False
    
    # Reporte final
    print("\n" + "="*50)
    print("📊 REPORTE DE TESTS WORDPRESS")
    print("="*50)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nResultado general: {'✅ TODOS PASARON' if all_passed else '❌ ALGUNOS FALLARON'}")
    print("="*50)
    
    return all_passed

if __name__ == "__main__":
    success = run_wordpress_tests()
    sys.exit(0 if success else 1)