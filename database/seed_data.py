from sqlalchemy.orm import Session
from .models import Category, Tag, Article, Keyword
from .database import SessionLocal

def seed_categories():
    """Crear categorías basadas en categories_and_tags.txt"""
    db = SessionLocal()
    
    categories_data = [
        ("Atención al Cliente con IA", "atencion-al-cliente-con-ia"),
        ("Automatización de Procesos", "automatizacion-de-procesos"),
        ("Casos de Éxito en Pymes", "casos-de-exito-en-pymes"),
        ("Eficiencia y Productividad", "eficiencia-y-productividad"),
        ("Estrategia y Gestión Empresarial", "estrategia-y-gestion-empresarial"),
        ("Inteligencia Artificial para Pymes", "inteligencia-artificial-para-pymes"),
        ("Marketing y Ventas Automatizadas", "marketing-y-ventas-automatizadas"),
        ("Recursos y Guías Prácticas", "recursos-y-guias-practicas"),
        ("Transformación Digital", "transformacion-digital")
    ]
    
    for name, slug in categories_data:
        existing = db.query(Category).filter(Category.name == name).first()
        if not existing:
            category = Category(name=name, slug=slug)
            db.add(category)
    
    db.commit()
    db.close()

def seed_existing_articles():
    """Crear artículos existentes basados en post.txt"""
    db = SessionLocal()
    
    # Primero obtener categorías
    categories = {cat.slug: cat.id for cat in db.query(Category).all()}
    
    articles_data = [
        {
            "title": "5 soluciones de IA para empresas pequeñas que están cambiando el juego",
            "slug": "5-soluciones-de-ia-para-empresas-pequenas-que-estan-cambiando-el-juego",
            "main_keyword": "soluciones de IA para empresas pequeñas",
            "stage": "conciencia",
            "category_slug": "recursos-y-guias-practicas",
            "wordpress_url": "https://lucasbenites.com/recursos-y-guias-practicas/5-soluciones-de-ia-para-empresas-pequenas-que-estan-cambiando-el-juego/"
        },
        {
            "title": "Consultoría en IA: qué es, beneficios y cómo puede transformar tu pyme",
            "slug": "consultoria-en-ia-que-es-beneficios-y-como-puede-transformar-tu-pyme",
            "main_keyword": "consultoría en IA",
            "stage": "consideracion",
            "category_slug": "inteligencia-artificial-para-pymes",
            "wordpress_url": "https://lucasbenites.com/inteligencia-artificial-para-pymes/consultoria-en-ia-que-es-beneficios-y-como-puede-transformar-tu-pyme/"
        },
        {
            "title": "Consultoría IA para pymes: qué es y cómo puede transformar tu negocio",
            "slug": "consultoria-ia-para-pymes",
            "main_keyword": "consultoría IA para pymes",
            "stage": "consideracion",
            "category_slug": "inteligencia-artificial-para-pymes",
            "wordpress_url": "https://lucasbenites.com/inteligencia-artificial-para-pymes/consultoria-ia-para-pymes/"
        },
        {
            "title": "Implementación de IA en mi empresa: pasos, herramientas y resultados esperados",
            "slug": "implementacion-de-ia-en-mi-empresa",
            "main_keyword": "implementación de IA en empresa",
            "stage": "compra",
            "category_slug": "transformacion-digital",
            "wordpress_url": "https://lucasbenites.com/transformacion-digital/implementacion-de-ia-en-mi-presa/"
        },
        {
            "title": "Consultoría en Inteligencia Artificial: qué es y qué puede hacer por tu pyme",
            "slug": "consultoria-en-inteligencia-artificial-que-es-y-que-puede-hacer-por-tu-pyme",
            "main_keyword": "consultoría en inteligencia artificial",
            "stage": "consideracion",
            "category_slug": "inteligencia-artificial-para-pymes",
            "wordpress_url": "https://lucasbenites.com/inteligencia-artificial-para-pymes/consultoria-en-inteligencia-artificial-que-es-y-que-puede-hacer-por-tu-pyme/"
        },
        {
            "title": "Qué tareas administrativas podés automatizar con IA (con ejemplos reales)",
            "slug": "que-tareas-administrativas-podes-automatizar-con-ia-con-ejemplos-reales",
            "main_keyword": "automatizar tareas administrativas con IA",
            "stage": "conciencia",
            "category_slug": "automatizacion-de-procesos",
            "wordpress_url": "https://lucasbenites.com/automatizacion-de-procesos/que-tareas-administrativas-podes-automatizar-con-ia-con-ejemplos-reales/"
        },
        {
            "title": "Implementación de IA en mi empresa: pasos, herramientas y resultados esperados",
            "slug": "implementacion-de-ia-en-mi-empresa-pasos-herramientas-y-resultados-esperados",
            "main_keyword": "implementación de IA empresa pasos",
            "stage": "compra",
            "category_slug": "transformacion-digital",
            "wordpress_url": "https://lucasbenites.com/transformacion-digital/implementacion-de-ia-en-mi-empresa-pasos-herramientas-y-resultados-esperados/"
        },
        {
            "title": "Automatizá tu pyme con IA: cómo funciona el servicio paso a paso",
            "slug": "automatiza-tu-pyme-con-ia-como-funciona-el-servicio-paso-a-paso",
            "main_keyword": "automatizar pyme con IA",
            "stage": "compra",
            "category_slug": "automatizacion-de-procesos",
            "wordpress_url": "https://lucasbenites.com/automatizacion-de-procesos/automatiza-tu-pyme-con-ia-como-funciona-el-servicio-paso-a-paso/"
        }
    ]
    
    for article_data in articles_data:
        existing = db.query(Article).filter(Article.slug == article_data["slug"]).first()
        if not existing:
            article = Article(
                title=article_data["title"],
                slug=article_data["slug"],
                content="Contenido importado desde WordPress",
                main_keyword=article_data["main_keyword"],
                stage=article_data["stage"],
                category_id=categories.get(article_data["category_slug"], 1),
                is_published=True
            )
            db.add(article)
    
    db.commit()
    db.close()

def seed_sample_keywords():
    """Crear keywords de ejemplo para diferentes etapas"""
    db = SessionLocal()
    
    keywords_data = [
        # Conciencia
        ("qué es la inteligencia artificial", "conciencia", 5),
        ("beneficios de la IA en empresas", "conciencia", 4),
        ("automatización empresarial", "conciencia", 4),
        ("herramientas de IA para pymes", "conciencia", 3),
        ("transformación digital empresas", "conciencia", 3),
        
        # Consideración  
        ("consultoría en IA", "consideracion", 5),
        ("implementar IA en empresa", "consideracion", 4),
        ("servicios de automatización", "consideracion", 4),
        ("consultora IA Argentina", "consideracion", 3),
        ("soluciones IA personalizadas", "consideracion", 3),
        
        # Compra
        ("contratar consultor IA", "compra", 5),
        ("presupuesto automatización IA", "compra", 4),
        ("agendar consulta IA", "compra", 4),
        ("Lucas Benites consultor", "compra", 3),
        ("reunión gratuita IA", "compra", 3)
    ]
    
    for keyword, stage, priority in keywords_data:
        existing = db.query(Keyword).filter(Keyword.keyword == keyword).first()
        if not existing:
            keyword_obj = Keyword(
                keyword=keyword,
                stage=stage,
                priority=priority
            )
            db.add(keyword_obj)
    
    db.commit()
    db.close()

def run_seed():
    """Ejecutar todas las funciones de seed"""
    print("Seeding categories...")
    seed_categories()
    
    print("Seeding existing articles...")
    seed_existing_articles()
    
    print("Seeding sample keywords...")
    seed_sample_keywords()
    
    print("Database seeded successfully!")

if __name__ == "__main__":
    run_seed()