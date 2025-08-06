# 🤖 Agent Blogger

Generador automático de artículos SEO para lucasbenites.com usando IA y LangGraph.

## 🎯 Características

- **Generación automática** de artículos extensos y optimizados para SEO
- **Flujo de trabajo inteligente** con LangGraph y múltiples nodos especializados
- **Equilibrio automático** entre etapas del buyer journey (conciencia, consideración, compra)
- **Integración completa** con WordPress API
- **Generación de imágenes** con DALL-E 3
- **Enlaces internos automáticos** entre artículos
- **CTAs personalizados** según la etapa del artículo
- **Sistema de revisión** y control de calidad
- **API REST** para gestión y monitoreo

## 🏗️ Arquitectura

### Nodos del Workflow (LangGraph)
- **Selector**: Elige keyword y etapa balanceando el contenido existente
- **Creador de Contenido**: Genera artículos extensos con GPT-4o-mini
- **Creador de Título**: Optimiza títulos para SEO (máx. 60 caracteres)
- **Categorizador**: Asigna categoría y crea etiquetas relevantes
- **Creador de Imágenes**: Genera imágenes profesionales con DALL-E
- **Enlaces Internos**: Crea vínculos contextuales a artículos existentes
- **Creador de CTA**: Genera llamadas a la acción según la etapa
- **Revisor**: Valida calidad y corrige errores
- **Publicador**: Publica en WordPress como borrador

### Base de Datos
- **Articles**: Artículos generados con metadatos completos
- **Keywords**: Keywords organizadas por etapa y prioridad
- **Categories/Tags**: Taxonomía sincronizada con WordPress
- **Internal Links**: Registro de enlaces entre artículos

## 🚀 Instalación

### 1. Clonar repositorio
```bash
git clone <repository-url>
cd agent_bloger
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Crear archivo `.env`:
```env
# OpenAI
OPENAI_API_KEY=tu_clave_openai

# WordPress
WP_URL=https://lucasbenites.com
WP_USERNAME=tu_usuario_wp
WP_APP_PASSWORD=tu_app_password_wp

# Base de datos (opcional, por defecto SQLite)
DATABASE_URL=sqlite:///./agent_blogger.db
```

### 5. Inicializar base de datos
```bash
python main.py init
```

## 📖 Uso

### Servidor API (Recomendado)
```bash
python main.py server
```
- API disponible en `http://localhost:8000`
- Documentación automática en `http://localhost:8000/docs`

### Generar artículo individual
```bash
python main.py generate
```

### Ejecutar tests
```bash
python main.py test
```

## 🔌 API Endpoints

### Principales
- `GET /` - Información de la API
- `POST /generate` - Generar artículo (async)
- `POST /generate/sync` - Generar artículo (sync, para testing)
- `GET /status/{workflow_id}` - Estado del workflow
- `GET /articles` - Listar artículos
- `GET /stats` - Estadísticas del sistema

### Gestión
- `GET /keywords` - Listar keywords
- `POST /keywords` - Crear keyword
- `GET /categories` - Listar categorías

## 🧪 Testing

El sistema incluye una suite completa de tests:

### Ejecutar todos los tests
```bash
python test_scripts/run_all_tests.py
```

### Tests individuales
```bash
# Base de datos
python test_scripts/test_database.py

# WordPress
python test_scripts/test_wordpress_connection.py

# Workflow completo
python test_scripts/test_full_workflow.py
```

Los resultados se guardan en `test_output/` para análisis posterior.

## 📁 Estructura del Proyecto

```
agent_bloger/
├── agents/                 # Sistema LangGraph
│   ├── nodes/             # Nodos especializados
│   ├── state.py           # Estado compartido
│   ├── supervisor.py      # Coordinador del workflow
│   └── workflow.py        # Definición del grafo
├── api/                   # FastAPI
│   ├── main.py           # Servidor principal
│   └── models.py         # Modelos Pydantic
├── database/             # Base de datos
│   ├── models.py         # Modelos SQLAlchemy
│   ├── database.py       # Configuración DB
│   └── seed_data.py      # Datos iniciales
├── wordpress/            # Integración WordPress
│   ├── client.py         # Cliente API REST
│   └── sync.py           # Sincronización
├── test_scripts/         # Suite de tests
├── test_output/          # Resultados de tests
├── logs/                 # Logs del sistema
└── main.py              # Punto de entrada
```

## ⚙️ Configuración WordPress

### 1. Crear Application Password
1. Ir a WordPress Admin → Usuarios → Perfil
2. Generar nueva "Application Password"
3. Usar en variable `WP_APP_PASSWORD`

### 2. Verificar permisos
El usuario debe tener permisos para:
- Crear/editar posts
- Gestionar categorías y etiquetas
- Subir media

### 3. Probar conexión
```bash
python test_scripts/test_wordpress_connection.py
```

## 🌐 Deployment en Render

### 1. Conectar repositorio
- Crear cuenta en [Render](https://render.com)
- Conectar repositorio de GitHub

### 2. Configurar variables de entorno
En Render Dashboard:
- `OPENAI_API_KEY`
- `WP_USERNAME`
- `WP_APP_PASSWORD`
- `DATABASE_URL` (PostgreSQL recomendado para producción)

### 3. Deploy automático
El archivo `render.yaml` configura el deployment automático.

## 📊 Monitoreo

### Logs
- Logs automáticos en `logs/`
- Niveles: INFO, WARNING, ERROR
- Rotación diaria automática

### Métricas
- Estadísticas via `/stats`
- Conteo de artículos por etapa
- Keywords disponibles/usadas
- Workflows activos

## 🔧 Desarrollo

### Agregar nuevos nodos
1. Crear archivo en `agents/nodes/`
2. Implementar función que reciba/retorne `ArticleState`
3. Registrar en `agents/workflow.py`
4. Actualizar routing en `supervisor.py`

### Personalizar prompts
Los prompts están en cada nodo, optimizados para:
- Público objetivo: dueños/gerentes de pymes argentinas
- Tono conversacional
- Marca personal Lucas Benites
- SEO y optimización

## 🐛 Troubleshooting

### Error de conexión OpenAI
```bash
# Verificar clave API
python -c "import openai; print('OK')"
```

### Error de conexión WordPress
```bash
# Test de conexión
python test_scripts/test_wordpress_connection.py
```

### Error de base de datos
```bash
# Reinicializar DB
rm agent_blogger.db
python main.py init
```

## 📝 Roadmap

- [ ] Soporte para múltiples idiomas
- [ ] Integración con Google Analytics
- [ ] Programación automática de publicaciones
- [ ] Dashboard web para gestión
- [ ] Integración con redes sociales
- [ ] Análisis de rendimiento SEO

## 🤝 Contribuir

1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto es privado y propietario de Lucas Benites.

## 📞 Soporte

Para soporte técnico o consultas:
- Email: [contacto@lucasbenites.com](mailto:contacto@lucasbenites.com)
- Web: [lucasbenites.com](https://lucasbenites.com)

---

**Desarrollado con ❤️ por Lucas Benites** - Automatizando la creación de contenido con IA