#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para sincronizar WordPress IDs de categorías en base de datos
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from database.models import Category

def sync_wordpress_category_ids():
    """Sincronizar WordPress IDs correctos para las categorías"""
    
    print("*** SINCRONIZANDO WORDPRESS IDS ***", flush=True)
    sys.stdout.flush()
    
    # Mapeo correcto de categorías según seed_data.py y verificación local
    correct_mappings = {
        "Atención al Cliente con IA": 6,
        "Automatización de Procesos": 2, 
        "Casos de Éxito en Pymes": 25,
        "Eficiencia y Productividad": 5,
        "Estrategia y Gestión Empresarial": 26,
        "Inteligencia Artificial para Pymes": 3,
        "Marketing y Ventas Automatizadas": 23,
        "Recursos y Guías Prácticas": 24,
        "Transformación Digital": 4
    }
    
    try:
        db = next(get_db())
        
        updated_count = 0
        for category_name, wp_id in correct_mappings.items():
            category = db.query(Category).filter(Category.name == category_name).first()
            
            if category:
                if category.wordpress_id != wp_id:
                    old_id = category.wordpress_id
                    category.wordpress_id = wp_id
                    updated_count += 1
                    print(f"[ACTUALIZADO] {category_name} -> WP ID: {old_id} -> {wp_id}", flush=True)
                else:
                    print(f"[OK] {category_name} -> WP ID: {wp_id}", flush=True)
            else:
                print(f"[ERROR] No encontrada: {category_name}", flush=True)
        
        if updated_count > 0:
            db.commit()
            print(f"*** {updated_count} categorías actualizadas ***", flush=True)
        else:
            print("*** No se necesitaron actualizaciones ***", flush=True)
        
        # Verificar resultado final
        print("\n*** VERIFICACION FINAL ***", flush=True)
        categories = db.query(Category).all()
        for cat in categories:
            print(f"  - {cat.name} -> WP ID: {cat.wordpress_id}", flush=True)
        
        db.close()
        sys.stdout.flush()
        
        return updated_count
        
    except Exception as e:
        print(f"*** ERROR: {str(e)} ***", flush=True)
        sys.stdout.flush()
        raise

if __name__ == "__main__":
    sync_wordpress_category_ids()