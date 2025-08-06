import json
import os
from datetime import datetime
from typing import Dict, Any
import re

def create_article_html(article_data: Dict[str, Any], output_dir: str = "utils/visualizations") -> str:
    """
    Convierte un artículo JSON en una página HTML bien formateada.
    
    Args:
        article_data: Datos del artículo en formato JSON
        output_dir: Directorio donde guardar el archivo HTML
        
    Returns:
        Ruta del archivo HTML generado
    """
    
    # Crear directorio si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Generar nombre de archivo
    title_clean = re.sub(r'[^\w\s-]', '', article_data.get('title', 'articulo')).strip()
    title_clean = re.sub(r'[-\s]+', '-', title_clean)[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/articulo_{title_clean}_{timestamp}.html"
    
    # Procesar contenido markdown a HTML básico
    content = article_data.get('content', '')
    content_html = markdown_to_html(content)
    
    # Generar HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article_data.get('title', 'Artículo').strip('"')}</title>
    <meta name="description" content="{article_data.get('meta_description', '')}">
    <style>
        {get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header class="article-header">
            <div class="metadata">
                <span class="category">{article_data.get('category', 'Sin categoría')}</span>
                <span class="stage">Etapa: {article_data.get('selected_stage', 'N/A')}</span>
                <span class="keyword">Keyword: {article_data.get('selected_keyword', 'N/A')}</span>
            </div>
            
            <h1 class="article-title">{article_data.get('title', 'Sin título').strip('"')}</h1>
            
            <div class="meta-info">
                <p class="meta-description">
                    <strong>Meta descripción:</strong> {article_data.get('meta_description', 'Sin meta descripción')}
                </p>
                
                <div class="tags">
                    <strong>Etiquetas:</strong>
                    {generate_tags_html(article_data.get('tags', []))}
                </div>
                
                <div class="stats">
                    <span class="word-count">📝 {len(article_data.get('content', '').split())} palabras</span>
                    <span class="links-count">🔗 {len(article_data.get('internal_links', []))} enlaces internos</span>
                    <span class="has-cta">{'✅' if article_data.get('cta_title') else '❌'} CTA incluido</span>
                    <span class="has-image">{'✅' if article_data.get('featured_image_url') else '❌'} Imagen destacada</span>
                </div>
            </div>
        </header>
        
        {generate_featured_image_html(article_data)}
        
        <article class="article-content">
            {content_html}
        </article>
        
        {generate_cta_section(article_data)}
        
        {generate_internal_links_summary(article_data.get('internal_links', []))}
        
        {generate_quality_report(article_data)}
        
        {generate_processing_log(article_data.get('processing_log', []))}
    </div>
    
    <script>
        {get_javascript()}
    </script>
</body>
</html>
"""
    
    # Guardar archivo
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return filename

def markdown_to_html(content: str) -> str:
    """Convierte markdown básico a HTML"""
    
    # Convertir títulos
    content = re.sub(r'^### (.*$)', r'<h3>\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.*$)', r'<h2>\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^# (.*$)', r'<h1>\1</h1>', content, flags=re.MULTILINE)
    
    # Convertir negritas
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    
    # Convertir párrafos
    paragraphs = content.split('\n\n')
    html_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if para:
            if para.startswith('<h') or para.startswith('<div') or para.startswith('<ul') or para.startswith('<ol'):
                html_paragraphs.append(para)
            else:
                # Convertir saltos de línea simples en <br>
                para = para.replace('\n', '<br>')
                html_paragraphs.append(f'<p>{para}</p>')
    
    return '\n'.join(html_paragraphs)

def generate_tags_html(tags: list) -> str:
    """Genera HTML para las etiquetas"""
    if not tags:
        return '<span class="no-tags">Sin etiquetas</span>'
    
    tag_html = []
    for tag in tags:
        tag_html.append(f'<span class="tag">{tag}</span>')
    
    return ' '.join(tag_html)

def generate_featured_image_html(article_data: Dict[str, Any]) -> str:
    """Genera HTML para la imagen destacada"""
    image_url = article_data.get('featured_image_url')
    image_alt = article_data.get('featured_image_alt', 'Imagen del artículo')
    
    if not image_url:
        return '<div class="no-image">📷 Sin imagen destacada</div>'
    
    return f"""
    <div class="featured-image">
        <img src="{image_url}" alt="{image_alt}" loading="lazy">
        <p class="image-caption">{image_alt}</p>
    </div>
    """

def generate_cta_section(article_data: Dict[str, Any]) -> str:
    """Genera sección del CTA con enlace destacado"""
    cta_title = article_data.get('cta_title')
    cta_content = article_data.get('cta_content')
    cta_link = article_data.get('cta_link')
    
    if not cta_title or not cta_content:
        return ""
    
    # Preparar contenido del CTA con saltos de línea convertidos
    cta_content_html = cta_content.replace('\n\n', '</p><p>').replace('\n', '<br>')
    
    # Generar botón si hay enlace
    cta_button = ""
    if cta_link:
        cta_button = f"""
        <div class="cta-button-container">
            <a href="{cta_link}" target="_blank" rel="noopener noreferrer" class="cta-button">
                🚀 ¡Descargar Ahora!
            </a>
        </div>
        """
    
    return f"""
    <section class="cta-section">
        <div class="cta-container">
            <h3 class="cta-title">{cta_title}</h3>
            <div class="cta-content">
                <p>{cta_content_html}</p>
            </div>
            {cta_button}
        </div>
    </section>
    """

def generate_internal_links_summary(internal_links: list) -> str:
    """Genera resumen de enlaces internos"""
    if not internal_links:
        return '<div class="links-summary"><h3>🔗 Enlaces Internos</h3><p>No se encontraron enlaces internos.</p></div>'
    
    links_html = []
    for i, link in enumerate(internal_links, 1):
        links_html.append(f"""
        <div class="link-item">
            <strong>{i}. {link.get('anchor', 'Sin texto anchor')}</strong><br>
            <small>URL: <a href="{link.get('url', '#')}" target="_blank">{link.get('url', 'N/A')}</a></small><br>
            <small>Contexto: "{link.get('context', 'N/A')}"</small>
        </div>
        """)
    
    return f"""
    <div class="links-summary">
        <h3>🔗 Enlaces Internos ({len(internal_links)})</h3>
        {''.join(links_html)}
    </div>
    """

def generate_quality_report(article_data: Dict[str, Any]) -> str:
    """Genera reporte de calidad del artículo"""
    errors = article_data.get('errors', [])
    warnings = article_data.get('warnings', [])
    
    error_html = ""
    if errors:
        error_list = ''.join([f'<li class="error-item">{error}</li>' for error in errors])
        error_html = f'<div class="errors"><h4>❌ Errores ({len(errors)})</h4><ul>{error_list}</ul></div>'
    
    warning_html = ""
    if warnings:
        warning_list = ''.join([f'<li class="warning-item">{warning}</li>' for warning in warnings])
        warning_html = f'<div class="warnings"><h4>⚠️ Advertencias ({len(warnings)})</h4><ul>{warning_list}</ul></div>'
    
    # Estadísticas
    content = article_data.get('content', '')
    title = article_data.get('title', '')
    meta = article_data.get('meta_description', '')
    
    stats_html = f"""
    <div class="quality-stats">
        <h4>📊 Estadísticas de Calidad</h4>
        <div class="stat-grid">
            <div class="stat-item">
                <span class="stat-label">Palabras:</span>
                <span class="stat-value {get_word_count_class(len(content.split()))}">{len(content.split())}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Título:</span>
                <span class="stat-value {get_title_length_class(len(title))}">{len(title)} caracteres</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Meta descripción:</span>
                <span class="stat-value {get_meta_length_class(len(meta))}">{len(meta)} caracteres</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Estado:</span>
                <span class="stat-value status-{article_data.get('current_step', 'unknown')}">{article_data.get('current_step', 'Desconocido')}</span>
            </div>
        </div>
    </div>
    """
    
    return f"""
    <div class="quality-report">
        <h3>📋 Reporte de Calidad</h3>
        {stats_html}
        {error_html}
        {warning_html}
    </div>
    """

def generate_processing_log(processing_log: list) -> str:
    """Genera HTML para el log de procesamiento"""
    if not processing_log:
        return ""
    
    log_items = []
    for i, log_entry in enumerate(processing_log):
        log_items.append(f'<li class="log-item"><span class="log-number">{i+1}.</span> {log_entry}</li>')
    
    return f"""
    <div class="processing-log">
        <h3>🔄 Log de Procesamiento</h3>
        <div class="log-container">
            <ul class="log-list">
                {''.join(log_items)}
            </ul>
        </div>
    </div>
    """

def get_word_count_class(count: int) -> str:
    """Devuelve clase CSS según el conteo de palabras"""
    if count >= 1200:
        return "excellent"
    elif count >= 800:
        return "good"
    else:
        return "needs-improvement"

def get_title_length_class(length: int) -> str:
    """Devuelve clase CSS según la longitud del título"""
    if 30 <= length <= 60:
        return "excellent"
    elif 20 <= length <= 80:
        return "good"
    else:
        return "needs-improvement"

def get_meta_length_class(length: int) -> str:
    """Devuelve clase CSS según la longitud de meta descripción"""
    if 120 <= length <= 155:
        return "excellent"
    elif 100 <= length <= 180:
        return "good"
    else:
        return "needs-improvement"

def get_css_styles() -> str:
    """Devuelve los estilos CSS para la página"""
    return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            border-radius: 8px;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        
        .article-header {
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .metadata {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .metadata span {
            background: #6c757d;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
        }
        
        .category { background: #007bff !important; }
        .stage { background: #28a745 !important; }
        .keyword { background: #17a2b8 !important; }
        
        .article-title {
            font-size: 2.2em;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 20px;
            line-height: 1.2;
        }
        
        .meta-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }
        
        .meta-description {
            margin-bottom: 15px;
        }
        
        .tags {
            margin-bottom: 15px;
        }
        
        .tag {
            background: #e9ecef;
            color: #495057;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.85em;
            margin-right: 5px;
        }
        
        .stats {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .stats span {
            background: white;
            padding: 5px 10px;
            border-radius: 4px;
            border: 1px solid #dee2e6;
            font-size: 0.9em;
        }
        
        .featured-image {
            margin: 30px 0;
            text-align: center;
        }
        
        .featured-image img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .image-caption {
            font-size: 0.9em;
            color: #6c757d;
            margin-top: 10px;
            font-style: italic;
        }
        
        .no-image {
            background: #f8f9fa;
            padding: 40px;
            text-align: center;
            border-radius: 8px;
            color: #6c757d;
            margin: 20px 0;
        }
        
        .article-content {
            font-size: 1.1em;
            line-height: 1.8;
            margin-bottom: 40px;
        }
        
        .article-content h2 {
            color: #2c3e50;
            margin: 40px 0 20px 0;
            font-size: 1.8em;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }
        
        .article-content h3 {
            color: #34495e;
            margin: 30px 0 15px 0;
            font-size: 1.4em;
        }
        
        .article-content p {
            margin-bottom: 20px;
        }
        
        .article-content a {
            color: #007bff;
            text-decoration: none;
            border-bottom: 1px solid #007bff;
        }
        
        .article-content a:hover {
            background-color: #007bff;
            color: white;
            padding: 2px 4px;
            border-radius: 3px;
        }
        
        .links-summary, .quality-report, .processing-log {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 30px 0;
            border: 1px solid #dee2e6;
        }
        
        .links-summary h3, .quality-report h3, .processing-log h3 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.3em;
        }
        
        .link-item {
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            border-left: 4px solid #007bff;
        }
        
        .quality-stats {
            margin-bottom: 20px;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .stat-item {
            background: white;
            padding: 10px 15px;
            border-radius: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .stat-label {
            font-weight: 600;
            color: #495057;
        }
        
        .stat-value {
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 4px;
        }
        
        .excellent {
            background: #d4edda;
            color: #155724;
        }
        
        .good {
            background: #fff3cd;
            color: #856404;
        }
        
        .needs-improvement {
            background: #f8d7da;
            color: #721c24;
        }
        
        .status-completed {
            background: #d4edda;
            color: #155724;
        }
        
        .errors, .warnings {
            margin: 15px 0;
        }
        
        .errors h4 {
            color: #dc3545;
            margin-bottom: 10px;
        }
        
        .warnings h4 {
            color: #ffc107;
            margin-bottom: 10px;
        }
        
        .error-item {
            color: #721c24;
            background: #f8d7da;
            padding: 8px 12px;
            border-radius: 4px;
            margin-bottom: 8px;
            list-style: none;
        }
        
        .warning-item {
            color: #856404;
            background: #fff3cd;
            padding: 8px 12px;
            border-radius: 4px;
            margin-bottom: 8px;
            list-style: none;
        }
        
        .log-container {
            max-height: 400px;
            overflow-y: auto;
            background: white;
            border-radius: 6px;
            padding: 15px;
        }
        
        .log-list {
            list-style: none;
        }
        
        .log-item {
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
            font-size: 0.95em;
        }
        
        .log-item:last-child {
            border-bottom: none;
        }
        
        .log-number {
            color: #007bff;
            font-weight: bold;
            margin-right: 8px;
        }
        
        .cta-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            margin: 40px 0;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .cta-container {
            padding: 40px;
            text-align: center;
            color: white;
        }
        
        .cta-title {
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 20px;
            color: white;
        }
        
        .cta-content {
            font-size: 1.1em;
            line-height: 1.6;
            margin-bottom: 30px;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .cta-content p {
            margin-bottom: 15px;
            color: rgba(255, 255, 255, 0.95);
        }
        
        .cta-button-container {
            margin-top: 30px;
        }
        
        .cta-button {
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 50px;
            font-weight: 700;
            font-size: 1.1em;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
            border: none;
            cursor: pointer;
        }
        
        .cta-button:hover {
            background: #218838;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
            color: white;
        }
        
        .cta-button:active {
            transform: translateY(0);
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                padding: 15px;
            }
            
            .article-title {
                font-size: 1.8em;
            }
            
            .metadata {
                flex-direction: column;
                gap: 8px;
            }
            
            .stats {
                flex-direction: column;
                gap: 8px;
            }
            
            .stat-grid {
                grid-template-columns: 1fr;
            }
            
            .cta-container {
                padding: 30px 20px;
            }
            
            .cta-title {
                font-size: 1.6em;
            }
            
            .cta-content {
                font-size: 1em;
            }
            
            .cta-button {
                padding: 12px 25px;
                font-size: 1em;
            }
        }
    """

def get_javascript() -> str:
    """Devuelve JavaScript adicional para interactividad"""
    return """
        // Funcionalidad para colapsar/expandir secciones
        document.addEventListener('DOMContentLoaded', function() {
            // Hacer que el log sea colapsable
            const logHeader = document.querySelector('.processing-log h3');
            if (logHeader) {
                logHeader.style.cursor = 'pointer';
                logHeader.addEventListener('click', function() {
                    const logContainer = document.querySelector('.log-container');
                    if (logContainer.style.display === 'none') {
                        logContainer.style.display = 'block';
                        this.textContent = this.textContent.replace('▶️', '🔽');
                    } else {
                        logContainer.style.display = 'none';
                        this.textContent = this.textContent.replace('🔽', '▶️');
                    }
                });
                
                // Inicialmente contraído
                logHeader.textContent = logHeader.textContent.replace('🔄', '▶️');
                document.querySelector('.log-container').style.display = 'none';
            }
            
            // Scroll suave para enlaces internos
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    document.querySelector(this.getAttribute('href')).scrollIntoView({
                        behavior: 'smooth'
                    });
                });
            });
        });
    """

def visualize_latest_article(test_output_dir: str = "test_output", visualizations_dir: str = "utils/visualizations") -> str:
    """
    Encuentra el artículo más reciente y genera su visualización HTML.
    
    Args:
        test_output_dir: Directorio donde están los archivos JSON
        visualizations_dir: Directorio donde guardar el HTML
        
    Returns:
        Ruta del archivo HTML generado
    """
    
    # Buscar el archivo JSON más reciente
    json_files = []
    if os.path.exists(test_output_dir):
        for filename in os.listdir(test_output_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(test_output_dir, filename)
                json_files.append((filepath, os.path.getmtime(filepath)))
    
    if not json_files:
        raise FileNotFoundError(f"No se encontraron archivos JSON en {test_output_dir}")
    
    # Ordenar por fecha de modificación (más reciente primero)
    json_files.sort(key=lambda x: x[1], reverse=True)
    latest_file = json_files[0][0]
    
    # Cargar y procesar el archivo
    with open(latest_file, 'r', encoding='utf-8') as f:
        article_data = json.load(f)
    
    # Generar HTML
    html_path = create_article_html(article_data, visualizations_dir)
    
    print(f"Visualizacion generada: {html_path}")
    print(f"Archivo fuente: {latest_file}")
    
    return html_path

if __name__ == "__main__":
    # Ejemplo de uso
    try:
        html_file = visualize_latest_article()
        
        # Intentar abrir en el navegador
        import webbrowser
        import os
        
        full_path = os.path.abspath(html_file)
        webbrowser.open(f'file://{full_path}')
        print(f"Abriendo en navegador: {html_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")