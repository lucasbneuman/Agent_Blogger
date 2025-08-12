from typing import Dict, Any
from agents.state import ArticleState
import requests
import os
from dotenv import load_dotenv
from database import get_db
from database.models import Article, Category, Tag
from datetime import datetime
import re
from io import BytesIO
from urllib.parse import urlparse
import tempfile

load_dotenv()

def markdown_to_html(content: str) -> str:
    """Convertir markdown básico a HTML para WordPress"""
    
    # Convertir títulos (del más específico al más general)
    content = re.sub(r'^#### (.*$)', r'<h4>\1</h4>', content, flags=re.MULTILINE)
    content = re.sub(r'^### (.*$)', r'<h3>\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.*$)', r'<h2>\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^# (.*$)', r'<h1>\1</h1>', content, flags=re.MULTILINE)
    
    # Convertir negritas
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    
    # Convertir cursivas
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
    
    # Convertir separadores
    content = content.replace('\n---\n', '\n<hr>\n')
    
    # Convertir párrafos (dividir por doble salto de línea)
    paragraphs = content.split('\n\n')
    html_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if para:
            # Si ya es HTML (empieza con <), no envolver en <p>
            if para.startswith('<h') or para.startswith('<hr') or para.startswith('<ul') or para.startswith('<ol') or para.startswith('<div'):
                html_paragraphs.append(para)
            else:
                # Convertir saltos de línea simples en <br>
                para = para.replace('\n', '<br>')
                html_paragraphs.append(f'<p>{para}</p>')
    
    return '\n'.join(html_paragraphs)

def download_dalle_image(image_url: str) -> tuple:
    """
    Descarga imagen de DALL-E y retorna bytes y nombre de archivo.
    
    Returns:
        tuple: (image_bytes, filename) o (None, None) si falla
    """
    try:
        # Descargar la imagen
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Generar nombre de archivo único
        parsed_url = urlparse(image_url)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dalle_image_{timestamp}.png"
        
        return response.content, filename
        
    except Exception as e:
        print(f"Error descargando imagen de DALL-E: {str(e)}")
        return None, None

def upload_image_to_wordpress(image_bytes: bytes, filename: str, alt_text: str, wp_url: str, wp_user: str, wp_password: str) -> int:
    """
    Sube imagen a WordPress Media Library.
    
    Returns:
        int: Media ID de WordPress o None si falla
    """
    try:
        # Preparar headers
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'image/png',
        }
        
        # Subir imagen
        media_response = requests.post(
            f"{wp_url}/wp-json/wp/v2/media",
            headers=headers,
            data=image_bytes,
            auth=(wp_user, wp_password)
        )
        
        if media_response.status_code == 201:
            media_data = media_response.json()
            media_id = media_data['id']
            
            # Actualizar alt text si se proporcionó
            if alt_text:
                alt_response = requests.post(
                    f"{wp_url}/wp-json/wp/v2/media/{media_id}",
                    json={'alt_text': alt_text},
                    auth=(wp_user, wp_password)
                )
            
            print(f"Imagen subida exitosamente: ID {media_id}")
            return media_id
        else:
            print(f"Error subiendo imagen: {media_response.status_code} - {media_response.text}")
            return None
            
    except Exception as e:
        print(f"Error en subida de imagen: {str(e)}")
        return None

def wordpress_publisher_node(state: ArticleState) -> Dict[str, Any]:
    """
    Nodo para publicar el artículo en WordPress.
    Utiliza la API REST de WordPress para crear el post.
    """
    
    # Verificar si se debe evitar la publicación (para tests)
    if state.get('skip_wordpress_publishing', False):
        processing_log = state.get('processing_log', [])
        processing_log.append("Publicación en WordPress omitida (modo test)")
        
        new_state = state.copy()
        new_state.update({
            'current_step': 'published_draft',
            'is_published': False,
            'processing_log': processing_log,
            'is_complete': True
        })
        return new_state
    
    # Verificar que el artículo esté aprobado
    if state.get('needs_revision', True) or state.get('errors'):
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + ['Artículo no puede publicarse: necesita revisión o tiene errores'],
            'current_step': 'publish_blocked'
        })
        return new_state
    
    # Verificar campos requeridos
    required_fields = ['title', 'content', 'meta_description', 'category', 'tags']
    missing_fields = [field for field in required_fields if not state.get(field)]
    
    if missing_fields:
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + [f'Faltan campos para publicar: {", ".join(missing_fields)}'],
            'current_step': 'publish_error'
        })
        return new_state
    
    try:
        # Configuración de WordPress
        wp_url = os.getenv('WP_URL', 'https://lucasbenites.com')
        wp_user = os.getenv('WP_USERNAME')
        wp_password = os.getenv('WP_APP_PASSWORD')
        
        if not all([wp_url, wp_user, wp_password]):
            raise Exception("Faltan credenciales de WordPress en variables de entorno")
        
        # Preparar contenido completo del artículo (convertir markdown a HTML)
        # NOTA: El CTA ya está integrado en state['content'] por article_assembler_node
        full_content = markdown_to_html(state['content'])
        
        # Agregar enlace del CTA al final si existe (solo el enlace, no duplicar el contenido)
        if state.get('cta_link') and state.get('cta_content'):
            cta_link_html = f'<p><a href="{state["cta_link"]}" target="_blank" rel="noopener">👉 Hacer clic aquí</a></p>'
            full_content += "\n\n" + cta_link_html
        
        # Obtener ID de categoría de WordPress
        import sys
        db = next(get_db())
        category = db.query(Category).filter(Category.name == state['category']).first()
        category_id = category.wordpress_id if category and category.wordpress_id else 1
        
        # DEBUGGING CRITICO DE CATEGORIA - FORZAR VISIBILIDAD
        import sys
        print("\n" + "="*60, flush=True)
        print(f"*** WORDPRESS PUBLISHER DEBUG ***", flush=True)
        print(f"Categoria del estado: '{state['category']}'", flush=True)
        print(f"Categoria encontrada en BD: {category.name if category else 'None'}", flush=True)
        print(f"WordPress ID en BD: {category.wordpress_id if category else 'None'}", flush=True)
        print(f"Category ID final a enviar: {category_id}", flush=True)
        print("="*60 + "\n", flush=True)
        sys.stdout.flush()
        
        # Obtener IDs de etiquetas de WordPress (crear si no existen)
        tag_ids = []
        print(f"Buscando etiquetas en BD: {state['tags']}")
        for tag_name in state['tags']:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if tag and tag.wordpress_id:
                print(f"  Found tag: {tag_name} -> ID {tag.wordpress_id}")
                tag_ids.append(tag.wordpress_id)
            else:
                print(f"  Tag NOT found: {tag_name} - creando en WordPress...")
                # Crear etiqueta en WordPress
                try:
                    # Limpiar AGRESIVAMENTE para evitar errores 400
                    clean_tag_name = re.sub(r'[^a-zA-Z0-9\s-]', '', tag_name)  # Solo letras, numeros, espacios, guiones
                    clean_tag_name = clean_tag_name.strip().lower()
                    tag_slug = re.sub(r'[-\s]+', '-', clean_tag_name)
                    
                    # Validar que la tag no esté vacía
                    if not clean_tag_name or len(clean_tag_name) < 2:
                        print(f"    Skipping invalid tag: '{tag_name}' -> '{clean_tag_name}'")
                        continue
                    
                    tag_data = {
                        'name': clean_tag_name,
                        'slug': tag_slug
                    }
                    
                    tag_response = requests.post(
                        f"{wp_url}/wp-json/wp/v2/tags",
                        json=tag_data,
                        auth=(wp_user, wp_password)
                    )
                    if tag_response.status_code == 201:
                        wp_tag_data = tag_response.json()
                        new_wp_tag_id = wp_tag_data['id']
                        tag_ids.append(new_wp_tag_id)
                        print(f"    Created new tag: {clean_tag_name} -> ID {new_wp_tag_id}")
                        
                        # Guardar en BD local para futuras referencias (MEJORADO)
                        try:
                            # Verificar si ya existe antes de crear
                            existing_tag = db.query(Tag).filter(Tag.wordpress_id == new_wp_tag_id).first()
                            if not existing_tag:
                                new_tag = Tag(name=clean_tag_name, slug=tag_slug, wordpress_id=new_wp_tag_id)
                                db.add(new_tag)
                                db.commit()
                        except Exception as e:
                            print(f"    Info: Tag ya existe en BD local: {str(e)}")
                            db.rollback()
                    elif tag_response.status_code == 400:
                        # Tag ya existe en WordPress, obtener su ID
                        try:
                            error_data = tag_response.json()
                            if 'term_id' in error_data.get('data', {}) or 'additional_data' in error_data:
                                # Extraer term_id de la respuesta de error
                                existing_id = error_data.get('additional_data', [None])[0] if error_data.get('additional_data') else error_data.get('data', {}).get('term_id')
                                if existing_id:
                                    tag_ids.append(existing_id)
                                    print(f"    Tag exists in WP: {clean_tag_name} -> ID {existing_id}")
                                    
                                    # Guardar referencia en BD local si no existe
                                    try:
                                        existing_tag = db.query(Tag).filter(Tag.wordpress_id == existing_id).first()
                                        if not existing_tag:
                                            new_tag = Tag(name=clean_tag_name, slug=tag_slug, wordpress_id=existing_id)
                                            db.add(new_tag)
                                            db.commit()
                                    except Exception as e:
                                        db.rollback()
                        except:
                            print(f"    Error 400 - Tag might exist: {clean_tag_name}")
                    else:
                        print(f"    Error creating tag '{clean_tag_name}': {tag_response.status_code}")
                        print(f"    Response: {tag_response.text[:200]}")
                except Exception as e:
                    print(f"    Exception creating tag: {str(e)}")
        print(f"Final tag_ids: {tag_ids}")
        print(f"Tags procesados: {len(state['tags'])} -> Tags finales: {len(tag_ids)}")
        
        # Si tenemos muy pocas tags, mostrar advertencia
        if len(tag_ids) < 3:
            print(f"WARNING: Solo {len(tag_ids)} tags creadas, se esperaban al menos 5")
        
        # Publicar directamente (sin aprobación necesaria)
        publish_status = 'publish'
        
        # DEBUGGING CRITICO FINAL ANTES DE ENVIAR
        print("\n" + "-"*40, flush=True)
        print(f">>> ENVIANDO A WORDPRESS <<<", flush=True)
        print(f"Category ID: [{category_id}]", flush=True)
        print(f"Tag IDs: {tag_ids}", flush=True)
        print(f"Status: {publish_status}", flush=True)
        print("-"*40 + "\n", flush=True)
        sys.stdout.flush()
        
        # Comentado para reducir logs
        # print(f"Estado: {state.get('current_step')} -> {publish_status}")
        
        # Preparar datos del post para WordPress
        post_data = {
            'title': state['title'],
            'content': full_content,
            'excerpt': state['meta_description'],
            'status': publish_status,  # Publicar o borrador según aprobación
            'categories': [category_id],
            'tags': tag_ids,
            'meta': {
                # Meta descripción estándar
                'description': state['meta_description'],
                
                # Yoast SEO metadata
                '_yoast_wpseo_title': state['title'],
                '_yoast_wpseo_metadesc': state['meta_description'],
                '_yoast_wpseo_focuskw': state.get('selected_keyword', ''),
                '_yoast_wpseo_canonical': '',
                '_yoast_wpseo_opengraph-title': state['title'],
                '_yoast_wpseo_opengraph-description': state['meta_description'],
                '_yoast_wpseo_twitter-title': state['title'],
                '_yoast_wpseo_twitter-description': state['meta_description']
            }
        }
        
        # Procesar imagen destacada automáticamente
        featured_image_id = None
        if state.get('featured_image_url'):
            print("Procesando imagen destacada...")
            
            # Descargar imagen de DALL-E
            image_bytes, filename = download_dalle_image(state['featured_image_url'])
            
            if image_bytes and filename:
                # Subir a WordPress
                featured_image_id = upload_image_to_wordpress(
                    image_bytes=image_bytes,
                    filename=filename,
                    alt_text=state.get('featured_image_alt', ''),
                    wp_url=wp_url,
                    wp_user=wp_user,
                    wp_password=wp_password
                )
                
                if featured_image_id:
                    # Asignar como imagen destacada
                    post_data['featured_media'] = featured_image_id
                    print(f"Imagen destacada asignada: ID {featured_image_id}")
                else:
                    print("No se pudo subir la imagen, continuando sin imagen destacada")
            else:
                print("No se pudo descargar la imagen de DALL-E")
            
            # Guardar información en meta para referencia
            post_data['meta']['_featured_image_original_url'] = state['featured_image_url']
            post_data['meta']['_featured_image_prompt'] = state.get('featured_image_prompt', '')
        
        # Realizar petición a WordPress REST API
        wp_api_url = f"{wp_url}/wp-json/wp/v2/posts"
        
        print(f"ENVIANDO A WP: {post_data['title'][:50]}...", flush=True)
        
        response = requests.post(
            wp_api_url,
            json=post_data,
            auth=(wp_user, wp_password),
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\n*** WORDPRESS RESPONSE: {response.status_code} ***", flush=True)
        if response.status_code not in [200, 201]:
            print(f"ERROR RESPONSE: {response.text[:500]}", flush=True)
        sys.stdout.flush()
        
        if response.status_code in [200, 201]:
            # Post creado exitosamente
            wp_response = response.json()
            wordpress_id = wp_response.get('id')
            post_url = wp_response.get('link')
            
            print(f"Post creado exitosamente: ID {wordpress_id}")
            
            # Actualizar meta campos Yoast SEO por separado (el REST API tiene limitaciones)
            if wordpress_id:
                try:
                    print("Actualizando meta campos Yoast SEO...")
                    
                    # Primero actualizar el post con excerpt
                    post_update = requests.post(
                        f"{wp_url}/wp-json/wp/v2/posts/{wordpress_id}",
                        json={
                            'excerpt': state['meta_description']
                        },
                        auth=(wp_user, wp_password),
                        headers={'Content-Type': 'application/json'}
                    )
                    print(f"Post excerpt update: {post_update.status_code}")
                    
                    # Intentar diferentes métodos para actualizar metadata
                    
                    # Método 1: Campos Yoast estándar
                    yoast_meta_data = {
                        '_yoast_wpseo_title': state['title'],
                        '_yoast_wpseo_metadesc': state['meta_description'], 
                        '_yoast_wpseo_focuskw': state.get('selected_keyword', ''),
                        '_yoast_wpseo_opengraph-title': state['title'],
                        '_yoast_wpseo_opengraph-description': state['meta_description'],
                        '_yoast_wpseo_twitter-title': state['title'],
                        '_yoast_wpseo_twitter-description': state['meta_description']
                    }
                    
                    # Método 2: También intentar campos WordPress nativos
                    wp_meta_data = {
                        'description': state['meta_description'],
                        'keywords': state.get('selected_keyword', ''),
                        '_wp_meta_description': state['meta_description'],
                        '_wp_meta_keywords': state.get('selected_keyword', '')
                    }
                    
                    # Combinar ambos
                    meta_data = {**yoast_meta_data, **wp_meta_data}
                    
                    print(f"Meta data to send: {meta_data}")
                    
                    # Método 1: Usar el campo yoast_meta personalizado (si functions.php fue actualizado)
                    yoast_custom_data = {
                        'yoast_meta': {
                            'title': state['title'],
                            'metadesc': state['meta_description'],
                            'focuskw': state.get('selected_keyword', '')
                        }
                    }
                    
                    print("Intentando actualizar via yoast_meta custom field...")
                    yoast_update = requests.post(
                        f"{wp_url}/wp-json/wp/v2/posts/{wordpress_id}",
                        json=yoast_custom_data,
                        auth=(wp_user, wp_password),
                        headers={'Content-Type': 'application/json'}
                    )
                    print(f"Yoast custom update response: {yoast_update.status_code}")
                    
                    # Método 2: Intentar meta fields registrados individualmente
                    print("Intentando actualizar via meta fields individuales...")
                    meta_update = requests.post(
                        f"{wp_url}/wp-json/wp/v2/posts/{wordpress_id}",
                        json={'meta': meta_data},
                        auth=(wp_user, wp_password),
                        headers={'Content-Type': 'application/json'}
                    )
                    print(f"Meta update response: {meta_update.status_code}")
                    
                    if meta_update.status_code not in [200, 201]:
                        print(f"Meta update error: {meta_update.text}")
                        
                        # Intentar método alternativo usando PUT
                        print("Intentando con PUT...")
                        put_update = requests.put(
                            f"{wp_url}/wp-json/wp/v2/posts/{wordpress_id}",
                            json={'meta': meta_data},
                            auth=(wp_user, wp_password)
                        )
                        print(f"PUT update response: {put_update.status_code}")
                        if put_update.status_code not in [200, 201]:
                            print(f"PUT error: {put_update.text}")
                    
                    # Verificar qué meta campos se guardaron realmente
                    print("Verificando meta campos guardados...")
                    verify_response = requests.get(
                        f"{wp_url}/wp-json/wp/v2/posts/{wordpress_id}",
                        auth=(wp_user, wp_password)
                    )
                    if verify_response.status_code == 200:
                        post_data_check = verify_response.json()
                        meta_fields = post_data_check.get('meta', {})
                        print(f"Meta fields actually saved:")
                        for key, value in meta_data.items():
                            saved_value = meta_fields.get(key, 'NOT FOUND')
                            print(f"  {key}: {saved_value}")
                    else:
                        print(f"Error verificando post: {verify_response.status_code}")
                    
                    # Método alternativo: Intentar usando el endpoint personalizado si existe
                    print("\nIntentando método alternativo...")
                    try:
                        # Algunos plugins de WordPress permiten actualizar meta a través de endpoints personalizados
                        custom_meta = requests.post(
                            f"{wp_url}/wp-json/wp/v2/posts/{wordpress_id}/meta",
                            json=meta_data,
                            auth=(wp_user, wp_password)
                        )
                        print(f"Custom meta endpoint response: {custom_meta.status_code}")
                    except:
                        print("Custom meta endpoint not available")
                        
                    # Método final: Usar PHP directo si es necesario
                    print("Si la metadata sigue sin aparecer, puede ser necesario:")
                    print("1. Verificar permisos de Application Password para meta campos")
                    print("2. Instalar plugin que exponga meta fields via REST API")
                    print("3. Usar approach diferente con wp-admin/admin-ajax.php")
                    
                except Exception as e:
                    print(f"Error actualizando meta: {str(e)}")
            
            # Guardar artículo en base de datos local
            try:
                # Generar slug único con timestamp si es necesario
                base_slug = wp_response.get('slug', '')
                slug = base_slug
                counter = 1
                while db.query(Article).filter(Article.slug == slug).first():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                new_article = Article(
                    title=state['title'],
                    slug=slug,
                    content=state['content'],
                    meta_description=state['meta_description'],
                    featured_image_url=state.get('featured_image_url'),
                    featured_image_alt=state.get('featured_image_alt'),
                    main_keyword=state['selected_keyword'],
                    stage=state['selected_stage'],
                    category_id=category.id if category else 1,
                    wordpress_id=wordpress_id,
                    is_published=True,
                    created_at=datetime.utcnow()
                )
                
                db.add(new_article)
            except Exception as e:
                print(f"Error guardando en BD local: {str(e)} - continuando...")
            
            # Agregar etiquetas
            for tag_name in state['tags']:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if tag:
                    new_article.tags.append(tag)
            
            db.commit()
            
            # Actualizar estado
            processing_log = state.get('processing_log', [])
            processing_log.append(f"Artículo publicado en WordPress: ID {wordpress_id}")
            processing_log.append(f"URL: {post_url}")
            
            if featured_image_id:
                processing_log.append(f"Imagen destacada subida: Media ID {featured_image_id}")
            else:
                processing_log.append("Sin imagen destacada")
            
            new_state = state.copy()
            new_state.update({
                'wordpress_id': wordpress_id,
                'is_published': True,
                'current_step': 'published',
                'is_complete': True,
                'processing_log': processing_log
            })
            
            return new_state
            
        else:
            # Error en la publicación
            error_msg = f"Error publicando en WordPress: {response.status_code} - {response.text}"
            raise Exception(error_msg)
            
    except Exception as e:
        error_msg = f"Error en publicación: {str(e)}"
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + [error_msg],
            'current_step': 'publish_error',
            'is_published': False
        })
        return new_state
        
    finally:
        if 'db' in locals():
            db.close()

def article_assembler_node(state: ArticleState) -> Dict[str, Any]:
    """
    Nodo para ensamblar el artículo completo antes de la publicación.
    Combina todos los elementos en un formato final.
    """
    
    try:
        # Verificar que todos los componentes estén listos
        required_components = {
            'title': state.get('title'),
            'content': state.get('content'),
            'meta_description': state.get('meta_description'),
            'category': state.get('category'),
            'tags': state.get('tags'),
            'selected_keyword': state.get('selected_keyword'),
            'selected_stage': state.get('selected_stage')
        }
        
        missing = [k for k, v in required_components.items() if not v]
        
        if missing:
            new_state = state.copy()
            new_state.update({
                'errors': state.get('errors', []) + [f'Componentes faltantes: {", ".join(missing)}'],
                'current_step': 'assembly_error'
            })
            return new_state
        
        # Ensamblar contenido completo integrando el CTA
        assembled_content = state['content']
        
        # Agregar CTA al final del contenido si existe
        if state.get('cta_title') and state.get('cta_content'):
            cta_section = f"\n\n---\n\n## {state['cta_title']}\n\n{state['cta_content']}"
            assembled_content += cta_section
            processing_log = state.get('processing_log', [])
            processing_log.append("CTA integrado al final del contenido")
        
        # Crear resumen del artículo
        article_summary = {
            'title': state['title'],
            'keyword': state['selected_keyword'],
            'stage': state['selected_stage'],
            'category': state['category'],
            'tags': state.get('tags', []),
            'word_count': len(assembled_content.split()),
            'original_word_count': len(state['content'].split()),
            'has_featured_image': bool(state.get('featured_image_url')),
            'has_cta': bool(state.get('cta_title')),
            'internal_links_count': len(state.get('internal_links', [])),
            'meta_description_length': len(state.get('meta_description', '')),
            'title_length': len(state.get('title', ''))
        }
        
        # Log de ensamblaje
        processing_log = state.get('processing_log', []) if not processing_log else processing_log
        processing_log.append("Artículo ensamblado exitosamente")
        processing_log.append(f"Contenido final: {len(assembled_content.split())} palabras (incluye CTA)")
        
        new_state = state.copy()
        new_state.update({
            'content': assembled_content,  # Actualizar con contenido que incluye CTA
            'current_step': 'assembled',
            'processing_log': processing_log,
            'article_summary': article_summary
        })
        
        return new_state
        
    except Exception as e:
        error_msg = f"Error en ensamblaje: {str(e)}"
        new_state = state.copy()
        new_state.update({
            'errors': state.get('errors', []) + [error_msg],
            'current_step': 'assembly_error'
        })
        return new_state