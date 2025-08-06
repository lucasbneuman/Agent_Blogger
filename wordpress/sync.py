from typing import Dict, Any
from sqlalchemy.orm import Session
from database import get_db
from database.models import Article, Category, Tag
from wordpress.client import wp_client
import logging

logger = logging.getLogger(__name__)

def sync_categories_from_wordpress():
    """
    Sincronizar categorías desde WordPress a la base de datos local.
    """
    db = next(get_db())
    
    try:
        wp_categories = wp_client.get_categories()
        synced_count = 0
        
        for wp_cat in wp_categories:
            # Buscar categoría existente
            existing = db.query(Category).filter(
                Category.wordpress_id == wp_cat['id']
            ).first()
            
            if not existing:
                # Crear nueva categoría
                new_category = Category(
                    name=wp_cat['name'],
                    slug=wp_cat['slug'],
                    wordpress_id=wp_cat['id']
                )
                db.add(new_category)
                synced_count += 1
            else:
                # Actualizar existente si es necesario
                if existing.name != wp_cat['name'] or existing.slug != wp_cat['slug']:
                    existing.name = wp_cat['name']
                    existing.slug = wp_cat['slug']
                    synced_count += 1
        
        db.commit()
        logger.info(f"Sincronizadas {synced_count} categorías desde WordPress")
        return synced_count
        
    except Exception as e:
        logger.error(f"Error sincronizando categorías: {str(e)}")
        db.rollback()
        return 0
    finally:
        db.close()

def sync_tags_from_wordpress():
    """
    Sincronizar etiquetas desde WordPress a la base de datos local.
    """
    db = next(get_db())
    
    try:
        wp_tags = wp_client.get_tags()
        synced_count = 0
        
        for wp_tag in wp_tags:
            # Buscar etiqueta existente
            existing = db.query(Tag).filter(
                Tag.wordpress_id == wp_tag['id']
            ).first()
            
            if not existing:
                # Crear nueva etiqueta
                new_tag = Tag(
                    name=wp_tag['name'],
                    slug=wp_tag['slug'],
                    wordpress_id=wp_tag['id']
                )
                db.add(new_tag)
                synced_count += 1
            else:
                # Actualizar existente si es necesario
                if existing.name != wp_tag['name'] or existing.slug != wp_tag['slug']:
                    existing.name = wp_tag['name']
                    existing.slug = wp_tag['slug']
                    synced_count += 1
        
        db.commit()
        logger.info(f"Sincronizadas {synced_count} etiquetas desde WordPress")
        return synced_count
        
    except Exception as e:
        logger.error(f"Error sincronizando etiquetas: {str(e)}")
        db.rollback()
        return 0
    finally:
        db.close()

def sync_articles_from_wordpress():
    """
    Sincronizar artículos existentes desde WordPress.
    Útil para importar artículos ya publicados.
    """
    db = next(get_db())
    
    try:
        wp_posts = wp_client.get_posts(per_page=50)  # Obtener más posts
        synced_count = 0
        
        for wp_post in wp_posts:
            # Buscar artículo existente
            existing = db.query(Article).filter(
                Article.wordpress_id == wp_post['id']
            ).first()
            
            if not existing:
                # Determinar categoría local
                category_id = 1  # Default
                if wp_post.get('categories'):
                    wp_cat_id = wp_post['categories'][0]
                    local_cat = db.query(Category).filter(
                        Category.wordpress_id == wp_cat_id
                    ).first()
                    if local_cat:
                        category_id = local_cat.id
                
                # Crear nuevo artículo
                new_article = Article(
                    title=wp_post['title']['rendered'],
                    slug=wp_post['slug'],
                    content=wp_post['content']['rendered'],
                    meta_description=wp_post.get('excerpt', {}).get('rendered', ''),
                    main_keyword='importado',  # Placeholder
                    stage='conciencia',  # Default
                    category_id=category_id,
                    wordpress_id=wp_post['id'],
                    is_published=wp_post['status'] == 'publish'
                )
                db.add(new_article)
                synced_count += 1
        
        db.commit()
        logger.info(f"Sincronizados {synced_count} artículos desde WordPress")
        return synced_count
        
    except Exception as e:
        logger.error(f"Error sincronizando artículos: {str(e)}")
        db.rollback()
        return 0
    finally:
        db.close()

def publish_article_to_wordpress(article_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publicar artículo específico en WordPress.
    Maneja la sincronización de categorías y etiquetas.
    """
    
    try:
        # Sincronizar categorías y etiquetas
        categories = [article_data.get('category', 'Sin categoría')]
        tags = article_data.get('tags', [])
        
        sync_result = wp_client.sync_categories_and_tags(categories, tags)
        category_ids = sync_result['category_ids']
        tag_ids = sync_result['tag_ids']
        
        # Subir imagen destacada si existe
        featured_media_id = None
        if article_data.get('featured_image_url'):
            media_data = wp_client.upload_media(
                article_data['featured_image_url'],
                f"featured-{article_data.get('slug', 'image')}.jpg",
                article_data.get('featured_image_alt', '')
            )
            if media_data:
                featured_media_id = media_data['id']
        
        # Crear el post
        post_data = wp_client.create_post(
            title=article_data['title'],
            content=article_data['content'],
            excerpt=article_data.get('meta_description', ''),
            categories=category_ids,
            tags=tag_ids,
            featured_media=featured_media_id,
            status='draft',  # Crear como borrador inicialmente
            meta={
                'description': article_data.get('meta_description', ''),
                '_yoast_wpseo_metadesc': article_data.get('meta_description', ''),
                '_yoast_wpseo_focuskw': article_data.get('main_keyword', '')
            }
        )
        
        if post_data:
            return {
                'success': True,
                'wordpress_id': post_data['id'],
                'url': post_data['link'],
                'status': post_data['status']
            }
        else:
            return {
                'success': False,
                'error': 'Error creando post en WordPress'
            }
            
    except Exception as e:
        logger.error(f"Error publicando en WordPress: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def update_wordpress_ids_in_db():
    """
    Actualizar IDs de WordPress en la base de datos local.
    Útil después de sincronizaciones.
    """
    db = next(get_db())
    
    try:
        # Actualizar categorías
        categories = db.query(Category).filter(Category.wordpress_id == None).all()
        for category in categories:
            wp_cat = wp_client.find_category_by_name(category.name)
            if wp_cat:
                category.wordpress_id = wp_cat['id']
        
        # Actualizar etiquetas
        tags = db.query(Tag).filter(Tag.wordpress_id == None).all()
        for tag in tags:
            wp_tag = wp_client.find_tag_by_name(tag.name)
            if wp_tag:
                tag.wordpress_id = wp_tag['id']
        
        db.commit()
        logger.info("IDs de WordPress actualizados en base de datos")
        
    except Exception as e:
        logger.error(f"Error actualizando IDs: {str(e)}")
        db.rollback()
    finally:
        db.close()

def full_sync():
    """
    Sincronización completa: categorías, etiquetas y artículos.
    """
    logger.info("Iniciando sincronización completa con WordPress")
    
    results = {
        'categories': sync_categories_from_wordpress(),
        'tags': sync_tags_from_wordpress(),
        'articles': sync_articles_from_wordpress()
    }
    
    # Actualizar IDs faltantes
    update_wordpress_ids_in_db()
    
    logger.info(f"Sincronización completa finalizada: {results}")
    return results

if __name__ == "__main__":
    # Test de sincronización
    if wp_client.test_connection():
        print("Conexión con WordPress exitosa")
        results = full_sync()
        print(f"Resultados: {results}")
    else:
        print("Error conectando con WordPress")