"""
Script de prueba para validar la sincronización con WordPress
y la prevención de duplicados.
"""

import sys
from wordpress_sync import (
    fetch_all_wordpress_posts,
    sync_wordpress_to_local_db,
    check_title_exists_in_wordpress,
    get_existing_titles_from_wordpress
)
from database import get_db
from database.models import Article


def test_fetch_posts():
    """Probar obtención de posts desde WordPress"""
    print("\n" + "="*60)
    print("TEST 1: Obtener posts de WordPress")
    print("="*60)

    try:
        posts = fetch_all_wordpress_posts()
        print(f"✓ Posts obtenidos: {len(posts)}")

        if posts:
            print("\nPrimeros 5 títulos:")
            for i, post in enumerate(posts[:5], 1):
                title = post['title']['rendered']
                print(f"  {i}. {title}")

        return True

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_sync_to_db():
    """Probar sincronización a base de datos local"""
    print("\n" + "="*60)
    print("TEST 2: Sincronizar posts a BD local")
    print("="*60)

    try:
        synced = sync_wordpress_to_local_db()
        print(f"✓ Posts sincronizados: {synced}")

        # Verificar en BD local
        db = next(get_db())
        total_articles = db.query(Article).count()
        published_articles = db.query(Article).filter(Article.is_published == True).count()

        print(f"✓ Total artículos en BD local: {total_articles}")
        print(f"✓ Artículos publicados: {published_articles}")

        db.close()
        return True

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_check_duplicate_title():
    """Probar detección de títulos duplicados"""
    print("\n" + "="*60)
    print("TEST 3: Verificar detección de títulos duplicados")
    print("="*60)

    try:
        # Obtener un título que sabemos que existe
        posts = fetch_all_wordpress_posts()

        if not posts:
            print("⚠️ No hay posts en WordPress para probar")
            return True

        existing_title = posts[0]['title']['rendered']
        fake_title = f"Este título no existe {sys.maxsize}"

        # Probar título existente
        exists = check_title_exists_in_wordpress(existing_title)
        print(f"Título existente: '{existing_title[:50]}...'")
        print(f"  ✓ Detectado como existente: {exists}")

        # Probar título inexistente
        not_exists = check_title_exists_in_wordpress(fake_title)
        print(f"\nTítulo falso: '{fake_title[:50]}...'")
        print(f"  ✓ Detectado como NO existente: {not not_exists}")

        return exists and not not_exists

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_get_all_titles():
    """Probar obtención de todos los títulos"""
    print("\n" + "="*60)
    print("TEST 4: Obtener todos los títulos de WordPress")
    print("="*60)

    try:
        titles = get_existing_titles_from_wordpress()
        print(f"✓ Títulos únicos obtenidos: {len(titles)}")

        if titles:
            print("\nPrimeros 5 títulos:")
            for i, title in enumerate(list(titles)[:5], 1):
                print(f"  {i}. {title[:60]}...")

        return True

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_category_assignment():
    """Probar que todos los artículos tengan categorías"""
    print("\n" + "="*60)
    print("TEST 5: Verificar asignación de categorías")
    print("="*60)

    try:
        db = next(get_db())

        # Contar artículos sin categoría
        no_category = db.query(Article).filter(Article.category_id == None).count()
        total = db.query(Article).count()

        print(f"✓ Total artículos: {total}")
        print(f"✓ Artículos SIN categoría: {no_category}")
        print(f"✓ Artículos CON categoría: {total - no_category}")

        # Mostrar distribución por categorías
        from database.models import Category
        categories = db.query(Category).all()

        print("\nDistribución por categorías:")
        for cat in categories:
            count = db.query(Article).filter(Article.category_id == cat.id).count()
            print(f"  {cat.name}: {count} artículos")

        db.close()

        if no_category > 0:
            print(f"\n⚠️ ADVERTENCIA: Hay {no_category} artículos sin categoría")
            return False

        return True

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def main():
    """Ejecutar todos los tests"""
    print("\n" + "#"*60)
    print("# SUITE DE PRUEBAS - INTEGRACIÓN WORDPRESS")
    print("#"*60)

    tests = [
        ("Obtener posts de WordPress", test_fetch_posts),
        ("Sincronizar a BD local", test_sync_to_db),
        ("Detectar títulos duplicados", test_check_duplicate_title),
        ("Obtener todos los títulos", test_get_all_titles),
        ("Verificar categorías", test_category_assignment)
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ ERROR EN TEST '{name}': {str(e)}")
            results.append((name, False))

    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)

    passed = 0
    failed = 0

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "-"*60)
    print(f"Total: {len(results)} | Exitosas: {passed} | Fallidas: {failed}")
    print("-"*60)

    if failed == 0:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        return 0
    else:
        print(f"\n⚠️ {failed} prueba(s) fallaron. Revisar logs arriba.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
