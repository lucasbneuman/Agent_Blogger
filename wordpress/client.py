import requests
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class WordPressClient:
    """Cliente para interactuar con la API REST de WordPress"""
    
    def __init__(self):
        self.base_url = os.getenv('WP_URL', 'https://lucasbenites.com')
        self.username = os.getenv('WP_USERNAME')
        self.password = os.getenv('WP_APP_PASSWORD')
        
        if not all([self.base_url, self.username, self.password]):
            raise ValueError("Faltan credenciales de WordPress en variables de entorno")
        
        self.api_url = f"{self.base_url}/wp-json/wp/v2"
        self.auth = (self.username, self.password)
        
        # Headers por defecto
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def test_connection(self) -> bool:
        """Probar conexión con WordPress"""
        try:
            response = requests.get(f"{self.api_url}/users/me", auth=self.auth)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error probando conexión: {str(e)}")
            return False
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Obtener categorías de WordPress"""
        try:
            response = requests.get(f"{self.api_url}/categories", auth=self.auth)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo categorías: {str(e)}")
            return []
    
    def get_tags(self) -> List[Dict[str, Any]]:
        """Obtener etiquetas de WordPress"""
        try:
            response = requests.get(f"{self.api_url}/tags", auth=self.auth)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo etiquetas: {str(e)}")
            return []
    
    def create_category(self, name: str, slug: str = None, description: str = "") -> Optional[Dict[str, Any]]:
        """Crear nueva categoría en WordPress"""
        try:
            data = {
                'name': name,
                'slug': slug or name.lower().replace(' ', '-'),
                'description': description
            }
            
            response = requests.post(
                f"{self.api_url}/categories",
                json=data,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error creando categoría: {str(e)}")
            return None
    
    def create_tag(self, name: str, slug: str = None, description: str = "") -> Optional[Dict[str, Any]]:
        """Crear nueva etiqueta en WordPress"""
        try:
            data = {
                'name': name,
                'slug': slug or name.lower().replace(' ', '-'),
                'description': description
            }
            
            response = requests.post(
                f"{self.api_url}/tags",
                json=data,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error creando etiqueta: {str(e)}")
            return None
    
    def upload_media(self, image_url: str, filename: str, alt_text: str = "") -> Optional[Dict[str, Any]]:
        """Subir imagen desde URL a WordPress"""
        try:
            # Descargar imagen
            img_response = requests.get(image_url)
            img_response.raise_for_status()
            
            # Preparar datos para subir
            files = {
                'file': (filename, img_response.content, 'image/jpeg')
            }
            
            headers = {
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
            
            if alt_text:
                headers['alt_text'] = alt_text
            
            # Subir a WordPress
            response = requests.post(
                f"{self.api_url}/media",
                files=files,
                auth=self.auth,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error subiendo imagen: {str(e)}")
            return None
    
    def create_post(self, 
                   title: str, 
                   content: str, 
                   excerpt: str = "",
                   categories: List[int] = None,
                   tags: List[int] = None,
                   featured_media: int = None,
                   status: str = "draft",
                   meta: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Crear nuevo post en WordPress"""
        try:
            data = {
                'title': title,
                'content': content,
                'excerpt': excerpt,
                'status': status
            }
            
            if categories:
                data['categories'] = categories
            
            if tags:
                data['tags'] = tags
            
            if featured_media:
                data['featured_media'] = featured_media
            
            if meta:
                data['meta'] = meta
            
            response = requests.post(
                f"{self.api_url}/posts",
                json=data,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error creando post: {str(e)}")
            return None
    
    def update_post(self, post_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """Actualizar post existente"""
        try:
            response = requests.post(
                f"{self.api_url}/posts/{post_id}",
                json=kwargs,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error actualizando post: {str(e)}")
            return None
    
    def get_post(self, post_id: int) -> Optional[Dict[str, Any]]:
        """Obtener post específico"""
        try:
            response = requests.get(f"{self.api_url}/posts/{post_id}", auth=self.auth)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo post: {str(e)}")
            return None
    
    def get_posts(self, per_page: int = 10, page: int = 1, **filters) -> List[Dict[str, Any]]:
        """Obtener lista de posts"""
        try:
            params = {
                'per_page': per_page,
                'page': page,
                **filters
            }
            
            response = requests.get(f"{self.api_url}/posts", params=params, auth=self.auth)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo posts: {str(e)}")
            return []
    
    def delete_post(self, post_id: int, force: bool = False) -> bool:
        """Eliminar post"""
        try:
            params = {'force': force} if force else {}
            response = requests.delete(f"{self.api_url}/posts/{post_id}", 
                                     params=params, 
                                     auth=self.auth)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error eliminando post: {str(e)}")
            return False
    
    def find_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Buscar categoría por nombre"""
        categories = self.get_categories()
        for cat in categories:
            if cat['name'].lower() == name.lower():
                return cat
        return None
    
    def find_tag_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Buscar etiqueta por nombre"""
        tags = self.get_tags()
        for tag in tags:
            if tag['name'].lower() == name.lower():
                return tag
        return None
    
    def sync_categories_and_tags(self, categories: List[str], tags: List[str]) -> Dict[str, List[int]]:
        """
        Sincronizar categorías y etiquetas, creando las que no existen.
        Retorna diccionario con IDs de WordPress.
        """
        result = {'category_ids': [], 'tag_ids': []}
        
        # Sincronizar categorías
        for cat_name in categories:
            wp_category = self.find_category_by_name(cat_name)
            if not wp_category:
                # Crear categoría
                wp_category = self.create_category(cat_name)
            
            if wp_category:
                result['category_ids'].append(wp_category['id'])
        
        # Sincronizar etiquetas
        for tag_name in tags:
            wp_tag = self.find_tag_by_name(tag_name)
            if not wp_tag:
                # Crear etiqueta
                wp_tag = self.create_tag(tag_name)
            
            if wp_tag:
                result['tag_ids'].append(wp_tag['id'])
        
        return result

# Instancia global del cliente
wp_client = WordPressClient()