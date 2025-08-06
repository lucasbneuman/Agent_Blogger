#!/usr/bin/env python3
"""
Test para verificar mejoras en publicación WordPress.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db
from database.seed_data import run_seed
from agents.workflow import create_article_workflow, initialize_article_state
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_improvements():
    """Test de mejoras en publicación"""
    
    logger.info("TESTING MEJORAS EN PUBLICACION")
    logger.info("=" * 30)
    
    # Configurar entorno
    init_db()
    run_seed()
    
    # Crear workflow
    workflow = create_article_workflow()
    
    # Inicializar estado para publicación real
    initial_state = initialize_article_state()
    initial_state.update({
        'skip_wordpress_publishing': False  # Publicar en WordPress
    })
    
    try:
        logger.info("Ejecutando workflow...")
        config = {"recursion_limit": 50}
        
        final_state = workflow.invoke(initial_state, config=config)
        
        logger.info(f"Estado final: {final_state.get('current_step')}")
        
        # Verificar si se publicó
        if final_state.get('wordpress_id'):
            logger.info(f"EXITO: Post publicado con ID {final_state.get('wordpress_id')}")
            return True
        else:
            logger.error("FALLO: No se obtuvo ID de WordPress")
            errors = final_state.get('errors', [])
            for error in errors:
                logger.error(f"Error: {error}")
            return False
        
    except Exception as e:
        logger.error(f"Error en test: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_improvements()
    if success:
        print("TEST EXITOSO - Revisa WordPress admin")
    else:
        print("TEST FALLO - Revisa logs")
        sys.exit(1)