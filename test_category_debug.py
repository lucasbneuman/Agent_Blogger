#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test específico para debugging de categorías
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.workflow import run_article_generation_sync_with_idea

def test_category_debugging():
    """Test completo del sistema con logging forzado"""
    
    print("*** INICIANDO TEST COMPLETO CON DEBUGGING ***", flush=True)
    sys.stdout.flush()
    
    # Idea que debería generar una categoría específica
    idea = "Quiero un artículo sobre cómo los restaurantes pueden usar ChatGPT para automatizar la atención al cliente y mejorar las reservas"
    
    print(f"Idea: {idea}", flush=True)
    sys.stdout.flush()
    
    try:
        # Ejecutar workflow completo
        final_state = run_article_generation_sync_with_idea(idea)
        
        print("*** RESULTADO FINAL ***", flush=True)
        print(f"Estado: {final_state.get('current_step')}", flush=True)
        print(f"Publicado: {final_state.get('is_published')}", flush=True)
        print(f"WordPress ID: {final_state.get('wordpress_id')}", flush=True)
        print(f"Categoría seleccionada: {final_state.get('category')}", flush=True)
        print(f"Tags: {final_state.get('tags')}", flush=True)
        
        if final_state.get('errors'):
            print(f"Errores: {final_state['errors']}", flush=True)
            
        sys.stdout.flush()
        
        return final_state
        
    except Exception as e:
        print(f"*** ERROR EN TEST: {str(e)} ***", flush=True)
        sys.stdout.flush()
        raise

if __name__ == "__main__":
    test_category_debugging()