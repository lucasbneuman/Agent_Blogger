#!/usr/bin/env python3
"""
Script simple para sincronizar con WordPress (sin emojis).
"""

import os
import sys
import requests
from dotenv import load_dotenv
from database import get_db
from database.models import Category, Tag

load_dotenv()

def get_wp_credentials():
    """Obtener credenciales de WordPress"""
    wp_url = os.getenv('WP_URL')
    wp_user = os.getenv('WP_USERNAME')
    wp_password = os.getenv('WP_APP_PASSWORD')
    
    if not all([wp_url, wp_user, wp_password]):
        raise Exception("Faltan credenciales de WordPress en .env")
    
    return wp_url, wp_user, wp_password

def test_wp_connection():
    """Probar conexión con WordPress"""
    wp_url, wp_user, wp_password = get_wp_credentials()
    
    try:
        response = requests.get(
            f"{wp_url}/wp-json/wp/v2/users/me",
            auth=(wp_user, wp_password),
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"Conexion exitosa con WordPress")
            print(f"   Usuario: {user_data.get('name', 'N/A')}")
            print(f"   Roles: {', '.join(user_data.get('roles', []))}")
            return True
        else:
            print(f"Error de autenticacion: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error de conexion: {str(e)}")
        return False

def sync_categories():
    """Sincronizar categorías con WordPress"""
    wp_url, wp_user, wp_password = get_wp_credentials()
    db = next(get_db())
    
    try:
        local_categories = db.query(Category).all()
        print(f"\nSincronizando {len(local_categories)} categorias...")
        
        for category in local_categories:
            # Verificar si existe en WordPress
            wp_response = requests.get(
                f"{wp_url}/wp-json/wp/v2/categories",
                params={'search': category.name},
                auth=(wp_user, wp_password)
            )
            
            if wp_response.status_code == 200:
                wp_categories = wp_response.json()
                
                if wp_categories:
                    # Existe - actualizar ID
                    wp_cat = wp_categories[0]
                    category.wordpress_id = wp_cat['id']
                    print(f"   OK: {category.name} -> ID: {wp_cat['id']}")
                else:
                    # No existe - crear nueva
                    create_response = requests.post(
                        f"{wp_url}/wp-json/wp/v2/categories",
                        json={
                            'name': category.name,
                            'slug': category.slug,
                            'description': category.description or ''
                        },
                        auth=(wp_user, wp_password)
                    )
                    
                    if create_response.status_code == 201:
                        wp_cat = create_response.json()
                        category.wordpress_id = wp_cat['id']
                        print(f"   NUEVA: {category.name} -> ID: {wp_cat['id']}")
                    else:
                        print(f"   ERROR: {category.name} - {create_response.text}")
        
        db.commit()
        print("Categorias sincronizadas OK")
        
    except Exception as e:
        print(f"Error sincronizando categorias: {str(e)}")
    finally:
        db.close()

def sync_tags():
    """Sincronizar etiquetas con WordPress"""
    wp_url, wp_user, wp_password = get_wp_credentials()
    db = next(get_db())
    
    try:
        local_tags = db.query(Tag).all()
        print(f"\nSincronizando {len(local_tags)} etiquetas...")
        
        for tag in local_tags:
            # Verificar si existe en WordPress
            wp_response = requests.get(
                f"{wp_url}/wp-json/wp/v2/tags",
                params={'search': tag.name},
                auth=(wp_user, wp_password)
            )
            
            if wp_response.status_code == 200:
                wp_tags = wp_response.json()
                
                if wp_tags:
                    # Existe - actualizar ID
                    wp_tag = wp_tags[0]
                    tag.wordpress_id = wp_tag['id']
                    print(f"   OK: {tag.name} -> ID: {wp_tag['id']}")
                else:
                    # No existe - crear nueva
                    create_response = requests.post(
                        f"{wp_url}/wp-json/wp/v2/tags",
                        json={
                            'name': tag.name,
                            'slug': tag.slug,
                            'description': getattr(tag, 'description', '') or ''
                        },
                        auth=(wp_user, wp_password)
                    )
                    
                    if create_response.status_code == 201:
                        wp_tag = create_response.json()
                        tag.wordpress_id = wp_tag['id']
                        print(f"   NUEVA: {tag.name} -> ID: {wp_tag['id']}")
                    else:
                        print(f"   ERROR: {tag.name} - {create_response.text}")
        
        db.commit()
        print("Etiquetas sincronizadas OK")
        
    except Exception as e:
        print(f"Error sincronizando etiquetas: {str(e)}")
    finally:
        db.close()

def test_post():
    """Crear post de prueba"""
    wp_url, wp_user, wp_password = get_wp_credentials()
    
    test_post = {
        'title': '[TEST] Agent Blogger - Post de Prueba',
        'content': '''
        <p>Este es un post de prueba generado por Agent Blogger.</p>
        <p>Si puedes ver esto, la conexion funciona correctamente.</p>
        <p><strong>Puedes eliminar este post.</strong></p>
        ''',
        'status': 'draft',
        'excerpt': 'Post de prueba para verificar conexion'
    }
    
    try:
        response = requests.post(
            f"{wp_url}/wp-json/wp/v2/posts",
            json=test_post,
            auth=(wp_user, wp_password)
        )
        
        if response.status_code == 201:
            post_data = response.json()
            print(f"\nPost de prueba creado exitosamente")
            print(f"   ID: {post_data['id']}")
            print(f"   URL: {post_data['link']}")
            print(f"   Estado: {post_data['status']}")
            return True
        else:
            print(f"\nError creando post: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"\nError en test de post: {str(e)}")
        return False

def main():
    """Función principal"""
    print("CONFIGURACION DE WORDPRESS")
    print("=" * 30)
    
    # 1. Probar conexión
    print("\n1. Probando conexion...")
    if not test_wp_connection():
        print("\nNo se pudo conectar. Verifica:")
        print("   - WP_URL en .env")
        print("   - WP_USERNAME en .env")
        print("   - WP_APP_PASSWORD en .env")
        return
    
    # 2. Sincronizar categorías
    print("\n2. Sincronizando categorias...")
    sync_categories()
    
    # 3. Sincronizar etiquetas
    print("\n3. Sincronizando etiquetas...")
    sync_tags()
    
    # 4. Test de post
    print("\n4. Probando creacion de post...")
    if test_post():
        print("\nCONFIGURACION COMPLETADA!")
        print("\nTu sistema esta listo para publicar articulos.")
        print("\nPara publicar un articulo real:")
        print("   python publish_article.py")
    else:
        print("\nLa conexion funciona pero hay problemas con publicacion.")
        print("Revisa permisos de usuario en WordPress.")

if __name__ == "__main__":
    main()