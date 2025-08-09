# Configuración GitHub Actions - Instrucciones

## Paso 1: Subir archivos a GitHub ✅
```bash
git add .github/workflows/auto-publish.yml
git commit -m "Add GitHub Actions for daily auto-publishing"
git push origin feature/telegram-integration
```

## Paso 2: Configurar URL en GitHub Secrets 🔐

1. **Ve a tu repositorio en GitHub.com**
2. **Click en "Settings"** (pestaña del repositorio)
3. **Click en "Secrets and variables" → "Actions"**
4. **Click en "New repository secret"**
5. **Agregar:**
   - **Name:** `RENDER_URL`  
   - **Value:** `https://tu-app-name.onrender.com`
   
   **IMPORTANTE:** Reemplaza `tu-app-name` con el nombre real de tu app en Render

## Paso 3: Probar manualmente 🧪

1. **Ve a la pestaña "Actions"** en tu repositorio
2. **Click en "Auto Publish Articles Daily"**
3. **Click en "Run workflow"** → **"Run workflow"**
4. **Observa los logs** para ver si funciona

## Paso 4: Verificar horarios ⏰

GitHub Actions usa **horario UTC**, así que:
- `0 12 * * *` = 12:00 UTC = 9:00 AM Argentina (UTC-3)
- `0 16 * * *` = 16:00 UTC = 1:00 PM Argentina (UTC-3)
- `0 20 * * *` = 20:00 UTC = 5:00 PM Argentina (UTC-3)

## ¿Qué va a pasar?

**A partir de mañana:**
- ✅ 9:00 AM: GitHub llama automáticamente a tu API → Se publica 1 artículo
- ✅ 1:00 PM: GitHub llama automáticamente a tu API → Se publica 1 artículo  
- ✅ 5:00 PM: GitHub llama automáticamente a tu API → Se publica 1 artículo

**Logs disponibles:**
- Ve a GitHub.com → tu repo → pestaña "Actions"
- Ahí verás cada ejecución con logs detallados

## Troubleshooting 🔧

Si algo falla:
1. Verificar que `RENDER_URL` esté configurado correctamente
2. Verificar que tu app de Render esté funcionando: `https://tu-app.onrender.com/`
3. Los logs de GitHub Actions mostrarán el error exacto

## Estado del Sistema 📊

Puedes verificar que todo funciona visitando:
- `https://tu-app.onrender.com/` - Health check
- `https://tu-app.onrender.com/auto-publish` - Ejecutar publicación manual