import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, get_db
from database.models import Article, Category, Tag, Keyword
from database.seed_data import run_seed
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_creation():
    """Test de creación de base de datos"""
    
    logger.info("=== TEST CREACIÓN DE BASE DE DATOS ===")
    
    try:
        # Inicializar base de datos
        init_db()
        logger.info("✅ Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {str(e)}")
        return False

def test_database_seeding():
    """Test de poblado de datos iniciales"""
    
    logger.info("=== TEST POBLADO DE DATOS ===")
    
    try:
        # Ejecutar seed
        run_seed()
        logger.info("✅ Datos iniciales cargados correctamente")
        
        # Verificar datos
        db = next(get_db())
        
        # Contar registros
        categories_count = db.query(Category).count()
        keywords_count = db.query(Keyword).count()
        articles_count = db.query(Article).count()
        
        logger.info(f"Categorías creadas: {categories_count}")
        logger.info(f"Keywords creadas: {keywords_count}")
        logger.info(f"Artículos creados: {articles_count}")
        
        # Validar que hay datos
        assert categories_count > 0, "Debe haber al menos una categoría"
        assert keywords_count > 0, "Debe haber al menos una keyword"
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en poblado de datos: {str(e)}")
        return False

def test_database_operations():
    """Test de operaciones CRUD en base de datos"""
    
    logger.info("=== TEST OPERACIONES CRUD ===")
    
    try:
        db = next(get_db())
        
        # Test CREATE - Crear nueva keyword
        test_keyword = Keyword(
            keyword="test keyword",
            stage="conciencia",
            priority=3
        )
        db.add(test_keyword)
        db.commit()
        db.refresh(test_keyword)
        
        assert test_keyword.id is not None, "Keyword debe tener ID después de crear"
        logger.info(f"✅ CREATE: Keyword creada con ID {test_keyword.id}")
        
        # Test READ - Leer keyword
        found_keyword = db.query(Keyword).filter(Keyword.id == test_keyword.id).first()
        assert found_keyword is not None, "Debe encontrar la keyword creada"
        assert found_keyword.keyword == "test keyword", "Keyword debe coincidir"
        logger.info("✅ READ: Keyword leída correctamente")
        
        # Test UPDATE - Actualizar keyword
        found_keyword.priority = 5
        db.commit()
        
        updated_keyword = db.query(Keyword).filter(Keyword.id == test_keyword.id).first()
        assert updated_keyword.priority == 5, "Priority debe estar actualizada"
        logger.info("✅ UPDATE: Keyword actualizada correctamente")
        
        # Test DELETE - Eliminar keyword
        db.delete(found_keyword)
        db.commit()
        
        deleted_keyword = db.query(Keyword).filter(Keyword.id == test_keyword.id).first()
        assert deleted_keyword is None, "Keyword debe estar eliminada"
        logger.info("✅ DELETE: Keyword eliminada correctamente")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en operaciones CRUD: {str(e)}")
        return False

def test_database_relationships():
    """Test de relaciones entre tablas"""
    
    logger.info("=== TEST RELACIONES DE TABLAS ===")
    
    try:
        db = next(get_db())
        
        # Obtener una categoría y sus artículos
        category = db.query(Category).first()
        if category:
            articles_count = len(category.articles)
            logger.info(f"Categoría '{category.name}' tiene {articles_count} artículos")
        
        # Obtener un artículo y sus etiquetas
        article = db.query(Article).first()
        if article:
            tags_count = len(article.tags)
            logger.info(f"Artículo '{article.title[:50]}...' tiene {tags_count} etiquetas")
        
        # Test de consulta con join
        articles_with_category = db.query(Article).join(Category).all()
        logger.info(f"Artículos con categoría: {len(articles_with_category)}")
        
        db.close()
        logger.info("✅ Relaciones funcionando correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en relaciones: {str(e)}")
        return False

def test_database_queries():
    """Test de consultas específicas del dominio"""
    
    logger.info("=== TEST CONSULTAS ESPECÍFICAS ===")
    
    try:
        db = next(get_db())
        
        # Consulta por etapa
        for stage in ['conciencia', 'consideracion', 'compra']:
            stage_keywords = db.query(Keyword).filter(Keyword.stage == stage).count()
            stage_articles = db.query(Article).filter(Article.stage == stage).count()
            logger.info(f"Etapa '{stage}': {stage_keywords} keywords, {stage_articles} artículos")
        
        # Keywords no usadas
        unused_keywords = db.query(Keyword).filter(Keyword.is_used == False).count()
        logger.info(f"Keywords no usadas: {unused_keywords}")
        
        # Artículos publicados
        published_articles = db.query(Article).filter(Article.is_published == True).count()
        logger.info(f"Artículos publicados: {published_articles}")
        
        # Keywords por prioridad
        high_priority = db.query(Keyword).filter(Keyword.priority >= 4).count()
        logger.info(f"Keywords alta prioridad (4-5): {high_priority}")
        
        db.close()
        logger.info("✅ Consultas específicas funcionando")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en consultas específicas: {str(e)}")
        return False

def run_database_tests():
    """Ejecutar todos los tests de base de datos"""
    
    logger.info("🚀 INICIANDO TESTS DE BASE DE DATOS")
    
    tests = [
        ("Creación de DB", test_database_creation),
        ("Poblado de datos", test_database_seeding),
        ("Operaciones CRUD", test_database_operations),
        ("Relaciones", test_database_relationships),
        ("Consultas específicas", test_database_queries)
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
    print("📊 REPORTE DE TESTS BASE DE DATOS")
    print("="*50)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nResultado general: {'✅ TODOS PASARON' if all_passed else '❌ ALGUNOS FALLARON'}")
    print("="*50)
    
    return all_passed

if __name__ == "__main__":
    success = run_database_tests()
    sys.exit(0 if success else 1)