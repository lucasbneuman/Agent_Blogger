# Configuración de Publicación Automática en Render

## Sistema Dual Implementado

### 1. **Publicación por Telegram** (Manual)
- **Método**: Envío de audio/texto por Telegram
- **Endpoint**: `POST /telegram-webhook`  
- **Uso**: Ideas específicas del usuario

### 2. **Publicación Automática** (Programada)
- **Método**: Selección automática desde keywords
- **Endpoint**: `GET/POST /auto-publish`
- **Uso**: 3 veces por día, automático

## Configuración en Render

### Opción A: Usar Render Cron Jobs
```bash
# En el dashboard de Render, crear 3 cron jobs:

# Mañana (9:00 AM GMT-3)
0 12 * * * curl -X GET https://tu-app.onrender.com/auto-publish

# Mediodía (1:00 PM GMT-3) 
0 16 * * * curl -X GET https://tu-app.onrender.com/auto-publish

# Tarde (5:00 PM GMT-3)
0 20 * * * curl -X GET https://tu-app.onrender.com/auto-publish
```

### Opción B: Script Python Local
```bash
# Ejecutar desde tu computadora/servidor
python run_simple.py --method http --url https://tu-app.onrender.com
```

### Opción C: GitHub Actions (Recomendado)
```yaml
# .github/workflows/auto-publish.yml
name: Auto Publish Articles
on:
  schedule:
    # 3 veces por día (UTC)
    - cron: '0 12 * * *'  # 9:00 AM Argentina
    - cron: '0 16 * * *'  # 1:00 PM Argentina  
    - cron: '0 20 * * *'  # 5:00 PM Argentina

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - name: Call auto-publish endpoint
        run: |
          curl -X GET ${{ secrets.RENDER_URL }}/auto-publish
```

## Endpoints Disponibles

1. **`GET /`** - Health check
2. **`POST /telegram-webhook`** - Webhook de Telegram (ideas)
3. **`GET/POST /auto-publish`** - Publicación automática desde keywords
4. **`GET /status`** - Estado del sistema

## Logs y Monitoreo

Los logs mostrarán:
```
INICIANDO publicación automática desde keywords
ARTÍCULO AUTO-PUBLICADO: [Título] (ID: [WordPress ID])
```

## Testing

```bash
# Test local
python run_simple.py --method local

# Test HTTP
python run_simple.py --method http --url https://tu-app.onrender.com
```