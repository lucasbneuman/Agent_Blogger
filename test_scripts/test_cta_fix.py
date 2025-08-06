#!/usr/bin/env python3
"""
Test para verificar que los CTAs se asignen correctamente por etapa 
y no se dupliquen en el contenido final.
"""

import os
import sys
from dotenv import load_dotenv

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from agents.nodes.cta_creator import cta_creator_node
from agents.nodes.wordpress_publisher import article_assembler_node, markdown_to_html
from agents.state import ArticleState

def test_cta_by_stage():
    """Test CTAs por cada etapa del buyer journey"""
    
    print("TESTING CTAs POR ETAPA DEL BUYER JOURNEY")
    print("=" * 60)
    
    stages = ['conciencia', 'consideracion', 'compra']
    expected_urls = {
        'conciencia': '032cf721.sibforms.com',  # Checklist form
        'consideracion': 'lucasbenites.com/5-automatizaciones',  # Recurso gratuito
        'compra': 'meet.brevo.com/lucas-benites'  # Agendar reunión
    }
    
    for stage in stages:
        print(f"\n--- TESTING ETAPA: {stage.upper()} ---")
        
        # Estado base para testing
        test_state = {
            'selected_stage': stage,
            'title': f'Artículo de prueba para {stage}',
            'selected_keyword': 'inteligencia artificial',
            'content': 'Este es el contenido base del artículo de prueba.',
            'meta_description': 'Meta descripción de prueba',
            'category': 'Tecnología',
            'tags': ['IA', 'Automatización'],
            'processing_log': []
        }
        
        # 1. Crear CTA
        print("1. Creando CTA...")
        cta_result = cta_creator_node(test_state)
        
        if cta_result.get('errors'):
            print(f"   ERROR: {cta_result['errors']}")
            continue
            
        cta_title = cta_result.get('cta_title')
        cta_content = cta_result.get('cta_content')
        cta_link = cta_result.get('cta_link')
        
        print(f"   CTA Title: {cta_title}")
        print(f"   CTA Content: {cta_content[:100]}...")
        print(f"   CTA Link: {cta_link}")
        
        # Verificar que el enlace corresponde a la etapa
        expected_domain = expected_urls[stage]
        if expected_domain in cta_link:
            print(f"   OK Enlace correcto para etapa {stage}")
        else:
            print(f"   ERROR Enlace incorrecto! Esperaba {expected_domain}")
        
        # 2. Ensamblar artículo (incluye CTA)
        print("2. Ensamblando artículo...")
        assembled_result = article_assembler_node(cta_result)
        
        if assembled_result.get('errors'):
            print(f"   ERROR en ensamblaje: {assembled_result['errors']}")
            continue
        
        final_content = assembled_result.get('content')
        
        # 3. Verificar que el CTA no se duplica
        print("3. Verificando no duplicación...")
        
        # Contar cuántas veces aparece el título del CTA
        title_count = final_content.count(cta_title)
        print(f"   Titulo del CTA aparece {title_count} veces")
        
        # Contar párrafos del CTA content (primeras 50 chars)
        content_snippet = cta_content[:50] if len(cta_content) >= 50 else cta_content
        content_count = final_content.count(content_snippet)
        print(f"   Contenido del CTA aparece {content_count} veces")
        
        if title_count == 1 and content_count == 1:
            print(f"   OK CTA NO DUPLICADO - Perfect!")
        else:
            print(f"   ERROR CTA DUPLICADO DETECTADO!")
        
        # 4. Test conversión a HTML
        print("4. Testing conversion Markdown->HTML...")
        html_content = markdown_to_html(final_content)
        
        # Verificar que el CTA se convierte correctamente a HTML
        if f"<h2>{cta_title}</h2>" in html_content:
            print(f"   OK CTA convertido a HTML correctamente")
        else:
            print(f"   ERROR Problema en conversion HTML del CTA")
        
        # Verificar que el enlace NO está duplicado en HTML
        link_count_html = html_content.count(cta_link)
        print(f"   Enlace aparece {link_count_html} vez(es) en HTML")
        
        print(f"   Contenido final: {len(final_content.split())} palabras")
        
    print(f"\nTEST COMPLETADO!")

def test_cta_links_status():
    """Verificar que todos los enlaces del CTA funcionen"""
    
    print(f"\nTESTING ENLACES DE CTA")
    print("=" * 40)
    
    import requests
    
    cta_links = {
        'conciencia': 'https://032cf721.sibforms.com/serve/MUIFAE47zttqxtfbDRc3ItIdRx3jI2XDzO5OLTijGhWzk0VnJxbYG97Q1OrgM17TZXOSEKyhy-RVK9N6MQf2nmkkAPBXeRuNM1KiAvsMf5xrdH1lBWiypothxpeUCSLwFkWWUTvFB211Gu0b8NKpEk_SlyucOKg4weycY3zSId5SERj5yKJjUHM7rVaTqJY7Z3XZ7p5H9bIKK0mY',
        'consideracion': 'https://lucasbenites.com/5-automatizaciones-inteligentes-con-ia/',
        'compra': 'https://meet.brevo.com/lucas-benites'
    }
    
    for stage, url in cta_links.items():
        print(f"\nTesting {stage}: {url[:50]}...")
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code < 400:
                print(f"   OK ENLACE OK ({response.status_code})")
            else:
                print(f"   WARNING ENLACE con issues ({response.status_code})")
        except Exception as e:
            print(f"   ERROR: {str(e)}")

if __name__ == "__main__":
    test_cta_by_stage()
    test_cta_links_status()
    print("\nTODOS LOS TESTS DE CTA COMPLETADOS!")