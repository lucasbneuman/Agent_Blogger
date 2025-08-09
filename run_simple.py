#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script simple para ejecutar publicación automática
Se puede llamar desde cron jobs o sistemas de programación
"""

import sys
import os
import requests
from datetime import datetime

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_auto_publish_local():
    """Ejecutar publicación automática local (sin HTTP)"""
    try:
        print("*** INICIANDO PUBLICACION AUTOMATICA LOCAL ***", flush=True)
        
        from agents.workflow import run_article_generation_sync
        
        start_time = datetime.now()
        result = run_article_generation_sync()
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        if result and result.get('is_complete') and result.get('wordpress_id'):
            print(f"[EXITO] {result.get('title')}", flush=True)
            print(f"WordPress ID: {result.get('wordpress_id')}", flush=True)
            print(f"Keyword: {result.get('selected_keyword')}", flush=True)
            print(f"Categoria: {result.get('category')}", flush=True)
            print(f"Duracion: {duration:.2f}s", flush=True)
            return True
        else:
            print("[ERROR] No se genero articulo", flush=True)
            if result and result.get('errors'):
                print(f"Errores: {result['errors']}", flush=True)
            return False
            
    except Exception as e:
        print(f"[ERROR CRITICO] {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return False

def run_auto_publish_http(render_url=None):
    """Ejecutar publicación automática vía HTTP"""
    try:
        if not render_url:
            render_url = os.getenv('RENDER_URL', 'http://localhost:10000')
            
        print(f"*** LLAMANDO HTTP: {render_url}/auto-publish ***", flush=True)
        
        response = requests.get(f"{render_url}/auto-publish", timeout=300)  # 5 min timeout
        
        if response.status_code == 200:
            data = response.json()
            print(f"[EXITO HTTP] {data.get('title')}", flush=True)
            print(f"WordPress ID: {data.get('wordpress_id')}", flush=True)
            return True
        else:
            print(f"[ERROR HTTP] {response.status_code}", flush=True)
            print(f"Response: {response.text}", flush=True)
            return False
            
    except Exception as e:
        print(f"[ERROR HTTP CRITICO] {str(e)}", flush=True)
        return False

def main():
    """Main function con opciones"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ejecutar publicación automática')
    parser.add_argument('--method', choices=['local', 'http'], default='local',
                       help='Método de ejecución (default: local)')
    parser.add_argument('--url', help='URL de Render (solo para método http)')
    parser.add_argument('--no-telegram', action='store_true', 
                       help='No usar funciones de telegram (para evitar errores)')
    
    args = parser.parse_args()
    
    print(f"Método: {args.method}", flush=True)
    print(f"Timestamp: {datetime.now()}", flush=True)
    
    if args.method == 'local':
        success = run_auto_publish_local()
    else:
        success = run_auto_publish_http(args.url)
    
    if success:
        print("[SUCCESS] PUBLICACION COMPLETADA EXITOSAMENTE", flush=True)
        sys.exit(0)
    else:
        print("[FAILED] PUBLICACION FALLO", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()