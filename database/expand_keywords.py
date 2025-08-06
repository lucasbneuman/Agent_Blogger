#!/usr/bin/env python3
"""
Expansión masiva de keywords para diversificar el contenido generado.
Agrega keywords variadas por tema y resetea las usadas.
"""

import os
import sys
from dotenv import load_dotenv

# Agregar el directorio raíz al path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

load_dotenv()

from database import get_db
from database.models import Keyword

def reset_used_keywords():
    """Reset keywords marcadas como usadas para reutilizarlas"""
    
    db = next(get_db())
    try:
        updated = db.query(Keyword).update({Keyword.is_used: False})
        db.commit()
        print(f"✅ Reset {updated} keywords como disponibles")
    finally:
        db.close()

def add_diverse_keywords():
    """Agregar keywords diversas organizadas por temas"""
    
    db = next(get_db())
    
    # KEYWORDS DIVERSAS POR TEMAS Y ETAPAS
    new_keywords = [
        
        # ============ CONCIENCIA ============
        # Productividad y Eficiencia
        ("como mejorar la productividad empresarial", "conciencia", 5),
        ("herramientas para aumentar eficiencia", "conciencia", 4),
        ("optimizar procesos de trabajo", "conciencia", 4),
        ("reducir tiempo en tareas repetitivas", "conciencia", 3),
        ("software de gestión empresarial", "conciencia", 3),
        
        # Transformación Digital
        ("qué es la transformación digital", "conciencia", 5),
        ("digitalizar mi empresa", "conciencia", 4),
        ("tecnología para pequeñas empresas", "conciencia", 4),
        ("modernizar procesos empresariales", "conciencia", 3),
        ("ventajas de la digitalización", "conciencia", 3),
        
        # Gestión de Datos y Análisis
        ("importancia de los datos empresariales", "conciencia", 4),
        ("análisis de datos para pymes", "conciencia", 4),
        ("tomar decisiones basadas en datos", "conciencia", 3),
        ("reportes automáticos empresariales", "conciencia", 3),
        ("dashboard para empresas", "conciencia", 2),
        
        # Marketing Digital
        ("marketing digital para pymes", "conciencia", 5),
        ("automatización de marketing", "conciencia", 4),
        ("email marketing automatizado", "conciencia", 3),
        ("gestión de redes sociales empresas", "conciencia", 3),
        ("lead generation para pymes", "conciencia", 2),
        
        # Atención al Cliente
        ("mejorar atención al cliente", "conciencia", 4),
        ("chatbots para empresas", "conciencia", 4),
        ("automatizar respuestas clientes", "conciencia", 3),
        ("sistema de tickets soporte", "conciencia", 3),
        ("customer service digitalizado", "conciencia", 2),
        
        # Gestión de Equipos
        ("gestión de equipos remotos", "conciencia", 4),
        ("colaboración digital empresas", "conciencia", 3),
        ("herramientas trabajo en equipo", "conciencia", 3),
        ("comunicación interna empresas", "conciencia", 3),
        ("productividad equipos trabajo", "conciencia", 2),
        
        # ============ CONSIDERACION ============
        # Servicios de Consultoría
        ("consultoría en transformación digital", "consideracion", 5),
        ("servicios de automatización empresarial", "consideracion", 5),
        ("consultora tecnológica Argentina", "consideracion", 4),
        ("implementación de sistemas empresariales", "consideracion", 4),
        ("asesoría en digitalización pymes", "consideracion", 4),
        
        # Soluciones Específicas
        ("soluciones de productividad empresarial", "consideracion", 5),
        ("sistemas de gestión personalizados", "consideracion", 4),
        ("automatización procesos administrativos", "consideracion", 4),
        ("optimización de flujos trabajo", "consideracion", 4),
        ("integración de herramientas digitales", "consideracion", 3),
        
        # Análisis y Evaluación
        ("auditoría procesos empresariales", "consideracion", 4),
        ("evaluación de eficiencia operativa", "consideracion", 4),
        ("análisis de oportunidades mejora", "consideracion", 3),
        ("diagnóstico tecnológico empresarial", "consideracion", 3),
        ("assessment digital empresas", "consideracion", 3),
        
        # Capacitación y Formación
        ("capacitación en herramientas digitales", "consideracion", 4),
        ("training tecnológico equipos", "consideracion", 3),
        ("formación en automatización", "consideracion", 3),
        ("workshops productividad empresarial", "consideracion", 3),
        ("mentoring transformación digital", "consideracion", 2),
        
        # Desarrollo de Estrategias
        ("estrategia de digitalización empresarial", "consideracion", 5),
        ("plan de transformación digital", "consideracion", 4),
        ("roadmap tecnológico pymes", "consideracion", 4),
        ("metodología de optimización", "consideracion", 3),
        ("framework de mejora continua", "consideracion", 3),
        
        # ============ COMPRA ============
        # Servicios Directos
        ("contratar consultor transformación digital", "compra", 5),
        ("presupuesto automatización empresarial", "compra", 5),
        ("contratar servicios optimización", "compra", 4),
        ("precio consultoría digitalización", "compra", 4),
        ("costo implementación sistemas", "compra", 4),
        
        # Contacto y Reuniones
        ("agendar consulta transformación digital", "compra", 5),
        ("reunión gratuita optimización", "compra", 5),
        ("contactar consultor tecnológico", "compra", 4),
        ("solicitar propuesta digitalización", "compra", 4),
        ("evaluación gratuita procesos", "compra", 4),
        
        # Servicios Específicos de Lucas
        ("Lucas Benites consultor digital", "compra", 5),
        ("servicios Lucas Benites", "compra", 4),
        ("contratar Lucas Benites", "compra", 4),
        ("consultoría Lucas Benites precio", "compra", 3),
        ("contacto Lucas Benites", "compra", 3),
        
        # Implementación y Proyectos
        ("proyecto automatización empresarial", "compra", 4),
        ("implementar solución digitalización", "compra", 4),
        ("desarrollo sistema gestión", "compra", 3),
        ("personalización herramientas empresa", "compra", 3),
        ("soporte implementación tecnológica", "compra", 3),
        
        # Planes y Paquetes
        ("paquetes transformación digital", "compra", 4),
        ("planes automatización empresarial", "compra", 4),
        ("servicios mensuales optimización", "compra", 3),
        ("retainer consultoría tecnológica", "compra", 3),
        ("mantenimiento sistemas empresariales", "compra", 2),
        
        # ============ KEYWORDS ESTACIONALES ============
        # Fin de Año / Planificación
        ("optimizar empresa para nuevo año", "conciencia", 3),
        ("planificación tecnológica anual", "consideracion", 3),
        ("presupuesto tecnología nuevo año", "compra", 3),
        
        # Inicio de Año / Objetivos
        ("objetivos digitales empresariales", "conciencia", 3),
        ("metas productividad anual", "consideracion", 3),
        ("implementar cambios enero", "compra", 3),
        
        # Crecimiento Empresarial
        ("escalar mi empresa digitalmente", "conciencia", 4),
        ("crecimiento sostenible pymes", "consideracion", 4),
        ("expansión con tecnología", "compra", 3),
        
        # ============ LONG TAIL KEYWORDS ============
        ("como automatizar facturación empresa pequeña", "conciencia", 2),
        ("mejor software gestión clientes pymes", "conciencia", 2),
        ("reducir costos operativos con tecnología", "consideracion", 2),
        ("implementar CRM personalizado empresa", "compra", 2),
        ("digitalizar procesos contables pyme", "compra", 2),
    ]
    
    try:
        added = 0
        for keyword, stage, priority in new_keywords:
            # Verificar si ya existe
            existing = db.query(Keyword).filter(Keyword.keyword == keyword).first()
            if not existing:
                keyword_obj = Keyword(
                    keyword=keyword,
                    stage=stage,
                    priority=priority,
                    is_used=False
                )
                db.add(keyword_obj)
                added += 1
        
        db.commit()
        print(f"✅ Agregadas {added} nuevas keywords diversas")
        
        # Mostrar estadísticas finales
        for stage in ['conciencia', 'consideracion', 'compra']:
            total = db.query(Keyword).filter(Keyword.stage == stage).count()
            available = db.query(Keyword).filter(
                Keyword.stage == stage, 
                Keyword.is_used == False
            ).count()
            print(f"   {stage.upper()}: {total} total, {available} disponibles")
            
    finally:
        db.close()

def main():
    """Ejecutar expansión completa de keywords"""
    
    print("EXPANSION MASIVA DE KEYWORDS")
    print("=" * 40)
    
    print("\n1. Resetear keywords usadas...")
    reset_used_keywords()
    
    print("\n2. Agregar keywords diversas...")
    add_diverse_keywords()
    
    print(f"\n✅ EXPANSION COMPLETADA!")
    print("""
TEMAS AGREGADOS:
- Productividad y Eficiencia  
- Transformación Digital
- Gestión de Datos y Análisis
- Marketing Digital
- Atención al Cliente
- Gestión de Equipos
- Consultoría Especializada
- Soluciones Personalizadas
- Servicios de Implementación
- Keywords Estacionales
- Long Tail Keywords

RESULTADO: Contenido mucho más diverso y variado!
    """)

if __name__ == "__main__":
    main()