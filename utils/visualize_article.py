#!/usr/bin/env python3
"""
Script para visualizar el último artículo generado en formato HTML.
"""

import os
import sys
import webbrowser
from utils.article_visualizer import visualize_latest_article

def main():
    """Función principal"""
    
    print("Generador de Visualización de Artículos")
    print("=" * 40)
    
    try:
        # Generar visualización HTML
        html_file = visualize_latest_article(
            test_output_dir="test_output",
            visualizations_dir="visualizations"
        )
        
        # Crear ruta absoluta
        full_path = os.path.abspath(html_file)
        
        print(f"\nVisualizacion generada exitosamente!")
        print(f"Archivo HTML: {html_file}")
        print(f"Ruta completa: {full_path}")
        
        # Abrir automáticamente en navegador
        try:
            webbrowser.open(f'file:///{full_path.replace(os.sep, "/")}')
            print("Abriendo en navegador automaticamente...")
        except Exception as e:
            print(f"No se pudo abrir automaticamente: {str(e)}")
            print(f"Puedes abrir manualmente: file:///{full_path}")
            
        print(f"\nDirectorio de visualizaciones: visualizations/")
        
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        print("\nAsegurate de haber ejecutado el test de articulo completo primero:")
        print("   python test_scripts/test_complete_article.py")
        
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()