#!/usr/bin/env python3
"""
Script para resetear keywords y mejorar la diversidad
"""

from database import get_db
from database.models import Keyword

def reset_all_keywords():
    """Reset todas las keywords para que puedan ser reutilizadas"""
    db = next(get_db())
    
    try:
        # Reset todas las keywords
        keywords = db.query(Keyword).all()
        reset_count = 0
        
        for keyword in keywords:
            if keyword.is_used:
                keyword.is_used = False
                reset_count += 1
        
        db.commit()
        print(f"Reset completado: {reset_count} keywords ahora disponibles")
        
        # Mostrar estado actualizado
        print("\n*** KEYWORDS DISPONIBLES POR ETAPA ***")
        for stage in ['conciencia', 'consideracion', 'compra']:
            available = db.query(Keyword).filter(
                Keyword.stage == stage,
                Keyword.is_used == False
            ).count()
            print(f"  {stage.title()}: {available} keywords disponibles")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_all_keywords()