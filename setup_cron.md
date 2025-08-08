# Configuración de Cron Jobs para Agent Blogger

## Opción 1: cron-job.org (Recomendado)

1. **Regístrate en https://cron-job.org**
2. **Crear 3 cron jobs** para generar artículos:

### Job 1: Artículo matutino (8:00 AM Argentina)
- **URL**: `https://tu-app.onrender.com/generate-article`
- **Método**: POST
- **Headers**: `Authorization: Bearer your-secret-token-here`
- **Horario**: `0 11 * * *` (UTC - equivale a 8:00 AM Argentina)

### Job 2: Artículo medio día (2:00 PM Argentina)  
- **URL**: `https://tu-app.onrender.com/generate-article`
- **Método**: POST
- **Headers**: `Authorization: Bearer your-secret-token-here`
- **Horario**: `0 17 * * *` (UTC - equivale a 2:00 PM Argentina)

### Job 3: Artículo nocturno (8:00 PM Argentina)
- **URL**: `https://tu-app.onrender.com/generate-article`
- **Método**: POST  
- **Headers**: `Authorization: Bearer your-secret-token-here`
- **Horario**: `0 23 * * *` (UTC - equivale a 8:00 PM Argentina)

## Opción 2: GitHub Actions (Alternativo)

Crear archivo `.github/workflows/daily-articles.yml`:

```yaml
name: Generate Daily Articles

on:
  schedule:
    # 3 artículos por día (horarios en UTC)
    - cron: '0 11 * * *'  # 8:00 AM Argentina
    - cron: '0 17 * * *'  # 2:00 PM Argentina  
    - cron: '0 23 * * *'  # 8:00 PM Argentina

jobs:
  generate-article:
    runs-on: ubuntu-latest
    steps:
      - name: Generate Article
        run: |
          curl -X POST "https://tu-app.onrender.com/generate-article" \
            -H "Authorization: Bearer ${{ secrets.API_SECRET_TOKEN }}" \
            -H "Content-Type: application/json"
```

## Opción 3: Servicio de Keep-Alive

Para mantener el servicio despierto, también puedes configurar:

### Keep-Alive Job (cada 14 minutos)
- **URL**: `https://tu-app.onrender.com/`
- **Método**: GET
- **Horario**: `*/14 * * * *` (cada 14 minutos)

## Configuración en Render

1. **Configura las variables de entorno**:
   - `API_SECRET_TOKEN`: Token secreto para autenticación
   - `TELEGRAM_BOT_TOKEN`: Token del bot de Telegram
   - `OPENAI_API_KEY`: Clave de OpenAI
   - `WP_*`: Credenciales de WordPress

2. **Deploy el servicio**:
   - Un solo web service que maneja tanto el bot como la API
   - Se despierta automáticamente cuando llegan requests
   - El bot de Telegram funciona en background

## Monitoreo

Endpoints para verificar estado:
- `GET /` - Health check
- `GET /status` - Estado detallado del sistema
- `POST /generate-article` - Generar artículo (requiere auth)
- `POST /generate-with-idea` - Generar con idea específica

## Ventajas de esta arquitectura:

✅ **Un solo servicio** en Render (plan gratuito)
✅ **Bot Telegram siempre disponible** (se despierta con mensajes)
✅ **3 artículos diarios automáticos** via cron externo
✅ **Eficiente en recursos** 
✅ **Fácil de monitorear**
✅ **Escalable** si migras a plan pagado

## Notas importantes:

- Los cron jobs externos "despiertan" el servicio automáticamente
- El bot de Telegram funciona en un hilo separado
- La API maneja tanto generación automática como ideas de Telegram
- Sistema robusto y preparado para producción