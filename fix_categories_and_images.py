#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar y corregir categorías en el entorno de producción
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from database.models import Category
from database.seed_data import seed_categories

def fix_categories_and_debug():
    """Verificar y corregir categorías"""
    
    print("*** VERIFICANDO CATEGORIAS EN PRODUCCION ***", flush=True)
    sys.stdout.flush()
    
    try:
        db = next(get_db())
        
        # Verificar categorías existentes
        categories = db.query(Category).all()
        
        print(f"Total categorias encontradas: {len(categories)}", flush=True)
        
        for cat in categories:
            print(f"  - {cat.name} (slug: {cat.slug}) -> WordPress ID: {cat.wordpress_id}", flush=True)
        
        sys.stdout.flush()
        
        # Si no hay categorías o faltan WordPress IDs, recrear
        if len(categories) == 0 or any(not cat.wordpress_id for cat in categories):
            print("*** RECREANDO CATEGORIAS ***", flush=True)
            sys.stdout.flush()
            
            # Ejecutar seed de categorías
            seed_categories()
            
            # Verificar nuevamente
            db = next(get_db())  # Nueva conexión
            categories = db.query(Category).all()
            
            print(f"Categorias después de seed: {len(categories)}", flush=True)
            for cat in categories:
                print(f"  - {cat.name} (slug: {cat.slug}) -> WordPress ID: {cat.wordpress_id}", flush=True)
            
            sys.stdout.flush()
        
        db.close()
        
        print("*** VERIFICACION COMPLETADA ***", flush=True)
        sys.stdout.flush()
        
    except Exception as e:
        print(f"*** ERROR EN VERIFICACION: {str(e)} ***", flush=True)
        sys.stdout.flush()
        raise

if __name__ == "__main__":
    fix_categories_and_debug()