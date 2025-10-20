"""
Módulo para sincronizar artículos existentes de WordPress con la base de datos local.
Esto permite evitar duplicados y asegurar que no se repitan títulos.
"""

import requests
import os
from dotenv import load_dotenv
from database import get_db
from database.models import Article, Category
from datetime import datetime

load_dotenv()


def fetch_all_wordpress_posts():
    """
    Obtiene todos los posts publicados desde WordPress usando la API REST.

    Returns:
        list: Lista de diccionarios con la información de cada post
    """

    wp_url = os.getenv('WP_URL', 'https://lucasbenites.com')
    wp_user = os.getenv('WP_USERNAME')
    wp_password = os.getenv('WP_APP_PASSWORD')

    if not all([wp_url, wp_user, wp_password]):
        raise Exception("Faltan credenciales de WordPress en variables de entorno")

    all_posts = []
    page = 1
    per_page = 100  # WordPress permite máximo 100 por página

    print(f"Obteniendo posts de WordPress desde {wp_url}...")

    while True:
        try:
            # Parámetros para obtener posts
            params = {
                'per_page': per_page,
                'page': page,
                'status': 'publish',  # Solo posts publicados
                '_fields': 'id,title,slug,categories,excerpt,date'  # Solo campos necesarios
            }

            response = requests.get(
                f"{wp_url}/wp-json/wp/v2/posts",
                params=params,
                auth=(wp_user, wp_password),
                timeout=30
            )

            if response.status_code == 200:
                posts = response.json()

                if not posts:  # No hay más posts
                    break

                all_posts.extend(posts)
                print(f"  Página {page}: {len(posts)} posts obtenidos")

                # Si se obtuvieron menos posts que el límite, es la última página
                if len(posts) < per_page:
                    break

                page += 1

            elif response.status_code == 400:
                # Página fuera de rango, hemos terminado
                break
            else:
                print(f"Error obteniendo posts: {response.status_code}")
                break

        except Exception as e:
            print(f"Error en petición a WordPress: {str(e)}")
            break

    print(f"Total de posts obtenidos: {len(all_posts)}")
    return all_posts


def sync_wordpress_to_local_db():
    """
    Sincroniza todos los posts de WordPress a la base de datos local.
    Esto crea registros para posts que ya existen en WordPress pero no en la BD local.
    """

    db = next(get_db())

    try:
        # Obtener todos los posts de WordPress
        wp_posts = fetch_all_wordpress_posts()

        synced_count = 0
        skipped_count = 0

        for wp_post in wp_posts:
            wordpress_id = wp_post['id']

            # Verificar si ya existe en la BD local
            existing = db.query(Article).filter(Article.wordpress_id == wordpress_id).first()

            if existing:
                skipped_count += 1
                continue

            # Obtener título y slug
            title = wp_post['title']['rendered']
            slug = wp_post['slug']

            # Asegurar que el slug sea único en BD local
            counter = 1
            original_slug = slug
            while db.query(Article).filter(Article.slug == slug).first():
                slug = f"{original_slug}-{counter}"
                counter += 1

            # Obtener categoría (usar la primera si hay múltiples)
            category_id = 1  # Default
            if wp_post.get('categories') and len(wp_post['categories']) > 0:
                wp_category_id = wp_post['categories'][0]
                category = db.query(Category).filter(Category.wordpress_id == wp_category_id).first()
                if category:
                    category_id = category.id

            # Crear registro en BD local
            new_article = Article(
                title=title,
                slug=slug,
                content="[Contenido existente en WordPress]",
                meta_description=wp_post.get('excerpt', {}).get('rendered', '')[:160],
                wordpress_id=wordpress_id,
                main_keyword="",  # No tenemos la keyword original
                stage="consideracion",  # Asumimos etapa de consideración
                category_id=category_id,
                is_published=True,
                created_at=datetime.fromisoformat(wp_post['date'].replace('Z', '+00:00')) if 'date' in wp_post else datetime.utcnow()
            )

            db.add(new_article)
            synced_count += 1

            if synced_count % 10 == 0:
                print(f"  Sincronizados: {synced_count}")

        db.commit()

        print(f"\n=== SINCRONIZACIÓN COMPLETADA ===")
        print(f"Posts sincronizados: {synced_count}")
        print(f"Posts ya existentes: {skipped_count}")
        print(f"Total procesados: {len(wp_posts)}")

        return synced_count

    except Exception as e:
        db.rollback()
        print(f"Error sincronizando WordPress: {str(e)}")
        raise

    finally:
        db.close()


def get_existing_titles_from_wordpress():
    """
    Obtiene todos los títulos de posts existentes en WordPress.
    Útil para validar que no se repitan títulos al crear nuevos artículos.

    Returns:
        set: Conjunto de títulos normalizados (lowercase, sin espacios extra)
    """

    wp_posts = fetch_all_wordpress_posts()
    titles = set()

    for post in wp_posts:
        title = post['title']['rendered'].strip().lower()
        titles.add(title)

    return titles


def check_title_exists_in_wordpress(title: str) -> bool:
    """
    Verifica si un título ya existe en WordPress.

    Args:
        title: Título a verificar

    Returns:
        bool: True si el título ya existe, False si no
    """

    wp_url = os.getenv('WP_URL', 'https://lucasbenites.com')
    wp_user = os.getenv('WP_USERNAME')
    wp_password = os.getenv('WP_APP_PASSWORD')

    try:
        # Buscar posts con el mismo título
        params = {
            'search': title,
            'per_page': 5,
            '_fields': 'id,title'
        }

        response = requests.get(
            f"{wp_url}/wp-json/wp/v2/posts",
            params=params,
            auth=(wp_user, wp_password),
            timeout=10
        )

        if response.status_code == 200:
            posts = response.json()

            # Verificar si algún título coincide exactamente (normalizado)
            normalized_title = title.strip().lower()

            for post in posts:
                post_title = post['title']['rendered'].strip().lower()
                if post_title == normalized_title:
                    return True

        return False

    except Exception as e:
        print(f"Error verificando título en WordPress: {str(e)}")
        # En caso de error, asumir que no existe para no bloquear la creación
        return False


if __name__ == "__main__":
    print("=== SINCRONIZACIÓN DE WORDPRESS ===\n")

    # Sincronizar todos los posts
    sync_wordpress_to_local_db()
