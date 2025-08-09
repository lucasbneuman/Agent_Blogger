#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simular exactamente el flujo de Telegram para reproducir el problema de categorías
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def simulate_telegram_flow():
    """Simular el flujo exacto que hace Telegram"""
    
    print("*** SIMULANDO FLUJO TELEGRAM EXACTO ***", flush=True)
    
    # La idea exacta del log
    idea = "Un artículo que explique la diferencia entre IA y LLMS, que habla sobre la utilización de datos, cuá..."
    
    print(f"Idea (del log): {idea}", flush=True)
    
    # Importar exactamente como lo hace api_render.py
    try:
        print("*** IMPORTANDO WORKFLOW ***", flush=True)
        from agents.workflow import run_article_generation_sync_with_idea
        
        print("*** EJECUTANDO WORKFLOW CON IDEA ***", flush=True)
        result = run_article_generation_sync_with_idea(idea)
        
        print("*** RESULTADO SIMULACION ***", flush=True)
        print(f"Estado: {result.get('current_step')}", flush=True)
        print(f"Categoría: {result.get('category')}", flush=True)
        print(f"Tags: {result.get('tags')}", flush=True)
        print(f"WordPress ID: {result.get('wordpress_id')}", flush=True)
        print(f"Publicado: {result.get('is_published')}", flush=True)
        
        # Verificar si hay la misma cantidad de logs que en nuestro test anterior
        if result.get('wordpress_id'):
            print("✅ SIMULACION EXITOSA - Se creó artículo", flush=True)
        else:
            print("❌ SIMULACION FALLO - No se creó artículo", flush=True)
            
        return result
        
    except Exception as e:
        print(f"*** ERROR EN SIMULACION: {str(e)} ***", flush=True)
        import traceback
        traceback.print_exc()
        raise

def compare_with_working_flow():
    """Comparar con el flujo que sabemos que funciona"""
    
    print("\n" + "="*50, flush=True)
    print("*** COMPARANDO CON FLUJO QUE FUNCIONA ***", flush=True)
    
    # El flujo que sabemos que funciona (del test anterior)
    working_idea = "Quiero un artículo sobre cómo los restaurantes pueden usar ChatGPT para automatizar la atención al cliente y mejorar las reservas"
    
    print(f"Idea que funciona: {working_idea}", flush=True)
    
    from agents.workflow import run_article_generation_sync_with_idea
    
    result = run_article_generation_sync_with_idea(working_idea)
    
    print("*** RESULTADO FLUJO QUE FUNCIONA ***", flush=True)
    print(f"Categoría: {result.get('category')}", flush=True)
    print(f"WordPress ID: {result.get('wordpress_id')}", flush=True)
    
    return result

if __name__ == "__main__":
    print("PASO 1: Simular flujo de Telegram")
    telegram_result = simulate_telegram_flow()
    
    print("\nPASO 2: Comparar con flujo que funciona")
    working_result = compare_with_working_flow()
    
    print("\n" + "="*50)
    print("*** ANALISIS COMPARATIVO ***")
    print(f"Telegram - Categoría: {telegram_result.get('category')}")
    print(f"Working  - Categoría: {working_result.get('category')}")
    print(f"Telegram - WP ID: {telegram_result.get('wordpress_id')}")
    print(f"Working  - WP ID: {working_result.get('wordpress_id')}")