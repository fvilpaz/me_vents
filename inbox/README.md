# inbox/

Sube aquí el PDF de una orden de servicio (github.com → esta carpeta → **Add file → Upload files** → Commit).

La Action **Procesar OS** lo procesa sola en 1-2 minutos: sustituye la versión anterior de ese grupo,
actualiza `events.json`, guarda el PDF en `data/beos/` y retira el archivo de esta carpeta.

Si el PDF no se puede procesar (sin texto o sin eventos), la Action queda en rojo en la pestaña **Actions**
y el archivo se queda aquí.

En local (o en Termux) se puede hacer lo mismo: `python -m backend.procesar_os` simula, y con `--aplicar` escribe.
