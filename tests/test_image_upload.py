#!/usr/bin/env python3
"""
Test para verificar subida automática de imágenes a WordPress.
"""

import sys
import os
from agents.nodes.wordpress_publisher import download_dalle_image, upload_image_to_wordpress
from dotenv import load_dotenv

load_dotenv()

def test_image_functions():
    """Test de funciones de imagen"""
    
    print("TESTING FUNCIONES DE IMAGEN")
    print("=" * 30)
    
    # URLs de ejemplo (estas son URLs reales de DALL-E que expiran)
    sample_urls = [
        "https://oaidalleapiprodscus.blob.core.windows.net/private/org-DsUiusLI9ti0Xg2WJe8DJcNK/user-sewIJQ68B1N9hpJetrEGGCJv/img-whwIUEJLhwmkg8fsTfD0iW75.png"
    ]
    
    wp_url = os.getenv('WP_URL')
    wp_user = os.getenv('WP_USERNAME') 
    wp_password = os.getenv('WP_APP_PASSWORD')
    
    if not all([wp_url, wp_user, wp_password]):
        print("ERROR: Faltan credenciales de WordPress")
        return False
    
    # Test 1: Descargar imagen
    print("\n1. Probando descarga de imagen...")
    image_bytes, filename = download_dalle_image(sample_urls[0])
    
    if image_bytes:
        print(f"   OK: Descargada {len(image_bytes)} bytes como {filename}")
        
        # Test 2: Subir a WordPress
        print("\n2. Probando subida a WordPress...")
        media_id = upload_image_to_wordpress(
            image_bytes=image_bytes,
            filename=filename,
            alt_text="Imagen de prueba generada por IA",
            wp_url=wp_url,
            wp_user=wp_user,
            wp_password=wp_password
        )
        
        if media_id:
            print(f"   OK: Subida exitosa con Media ID {media_id}")
            print(f"   URL: {wp_url}/wp-admin/upload.php?item={media_id}")
            return True
        else:
            print("   ERROR: No se pudo subir a WordPress")
            return False
    else:
        print("   ERROR: No se pudo descargar imagen")
        return False

def main():
    """Función principal"""
    print("IMPORTANTE: Este test descarga y sube una imagen real a WordPress")
    print()
    
    success = test_image_functions()
    
    if success:
        print("\nTEST EXITOSO!")
        print("La imagen se subio correctamente a WordPress.")
        print("Ve a tu biblioteca de medios para verificar.")
    else:
        print("\nTEST FALLO!")
        print("Revisa la configuracion de WordPress.")

if __name__ == "__main__":
    main()