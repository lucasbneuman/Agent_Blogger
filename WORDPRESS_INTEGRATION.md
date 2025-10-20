# Integración con WordPress - Prevención de Duplicados

## 🎯 Objetivo

Resolver los siguientes problemas:
1. **Títulos y entradas duplicadas** en WordPress
2. **Artículos sin categorías asignadas**

## 🔧 Solución Implementada

### 1. Sincronización con WordPress (`wordpress_sync.py`)

Nuevo módulo que permite:

- **Obtener todos los posts** existentes en WordPress mediante la API REST
- **Sincronizar posts** a la base de datos local para mantener un registro
- **Verificar títulos duplicados** antes de crear nuevos artículos
- **Obtener lista de títulos existentes** para validaciones

#### Funciones principales:

```python
# Obtener todos los posts de WordPress
fetch_all_wordpress_posts() -> list

# Sincronizar posts WP -> BD local
sync_wordpress_to_local_db() -> int

# Verificar si un título ya existe
check_title_exists_in_wordpress(title: str) -> bool

# Obtener todos los títulos existentes
get_existing_titles_from_wordpress() -> set
```

### 2. Validación de Títulos en `content_creator.py`

Se modificó `title_creator_node()` para:

1. **Verificar** si el título generado ya existe en WordPress
2. **Regenerar** automáticamente hasta 3 veces si hay duplicado
3. **Agregar sufijo único** (año) si después de 3 intentos sigue duplicado

```python
# Ejemplo de flujo:
Título generado: "Guía de IA para empresas"
→ Ya existe en WordPress
→ Regenera: "Cómo implementar IA en tu negocio"
→ Ya existe
→ Regenera: "IA para pymes: guía práctica"
→ No existe ✓
```

### 3. Mejora en Asignación de Categorías

Se modificó `wordpress_publisher.py` para:

1. **Verificar** que la categoría del artículo tenga `wordpress_id`
2. **Buscar categoría por defecto** si la actual no es válida
3. **Usar "Uncategorized" (ID: 1)** como último recurso

```python
# Flujo de fallback:
1. Intentar categoría del estado
2. Si no existe → buscar cualquier categoría válida en BD
3. Si no hay ninguna → usar "Uncategorized" (ID: 1)
```

### 4. Sincronización Automática al Inicio

Se modificó `main.py` para sincronizar automáticamente al iniciar:

```python
def init_database():
    init_db()
    run_seed()

    # NUEVO: Sincronizar posts existentes
    sync_wordpress_to_local_db()
```

## 📋 Cómo Usar

### Primera vez (sincronizar posts existentes):

```bash
# Ejecutar sincronización manual
python wordpress_sync.py

# O simplemente iniciar el sistema (sincroniza automáticamente)
python main.py
```

### Pruebas:

```bash
# Ejecutar suite de pruebas completa
python test_wordpress_sync.py
```

### Generación normal:

```bash
# El sistema ahora valida automáticamente títulos duplicados
python main.py generate
```

## ✅ Tests Implementados

El archivo `test_wordpress_sync.py` incluye:

1. **Test de conexión**: Verifica que se puedan obtener posts de WordPress
2. **Test de sincronización**: Valida que los posts se guarden en BD local
3. **Test de duplicados**: Comprueba detección de títulos existentes
4. **Test de títulos**: Obtiene y lista todos los títulos
5. **Test de categorías**: Verifica que todos los artículos tengan categoría

## 🔐 Variables de Entorno Requeridas

Asegúrate de tener en tu `.env`:

```bash
WP_URL=https://lucasbenites.com
WP_USERNAME=tu_usuario
WP_APP_PASSWORD=tu_app_password_de_wordpress
```

## 📊 Flujo Completo

```
1. main.py inicia
   ↓
2. init_database() se ejecuta
   ↓
3. sync_wordpress_to_local_db() sincroniza posts existentes
   ↓
4. Generación de artículo inicia
   ↓
5. title_creator_node() genera título
   ↓
6. check_title_exists_in_wordpress() verifica duplicado
   ↓
7. Si existe → regenera hasta 3 veces
   ↓
8. wordpress_publisher_node() publica
   ↓
9. Verifica categoría válida antes de publicar
   ↓
10. Artículo publicado SIN duplicados y CON categoría ✓
```

## 🚨 Puntos Importantes

1. **No tocar archivos originales**: Solo se modificaron archivos necesarios
2. **Sincronización inicial**: La primera vez puede tardar dependiendo del número de posts
3. **Validación en tiempo real**: Cada título se valida contra WordPress antes de publicar
4. **Fallback de categorías**: Nunca se publicará sin categoría

## 🔄 Mantenimiento

### Resincronizar manualmente:

```bash
python wordpress_sync.py
```

### Ver estadísticas:

```python
from database import get_db
from database.models import Article

db = next(get_db())
total = db.query(Article).count()
publicados = db.query(Article).filter(Article.is_published == True).count()

print(f"Total: {total}")
print(f"Publicados: {publicados}")
```

## 📝 Archivos Modificados

- ✅ `wordpress_sync.py` - **NUEVO** módulo de sincronización
- ✅ `test_wordpress_sync.py` - **NUEVO** suite de tests
- ✅ `agents/nodes/content_creator.py` - Validación de títulos
- ✅ `agents/nodes/wordpress_publisher.py` - Mejora en categorías
- ✅ `main.py` - Sincronización automática al inicio

## ⚡ Ventajas

1. ✅ **Cero duplicados**: Títulos validados contra WordPress en tiempo real
2. ✅ **Siempre categorizado**: Fallback inteligente de categorías
3. ✅ **Sincronización automática**: Se actualiza al iniciar el sistema
4. ✅ **No invasivo**: No rompe funcionalidad existente
5. ✅ **Testeable**: Suite completa de pruebas incluida

---

**Creado en**: 2025-10-20
**Rama**: `fix/wordpress-integration-deduplication`
