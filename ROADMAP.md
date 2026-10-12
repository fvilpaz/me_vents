# 🗺️ ME·VENTS — Roadmap & Arquitectura Futura

> **Objetivo**: Que el equipo de operaciones de **ME Málaga** puedan subir y consultar órdenes de servicio (BEO) de Opera Sales & Catering de manera 100% autónoma, desde cualquier dispositivo (móvil, tablet o PC), sin depender de un servidor local en tu ordenador ni de subidas manuales.

---

## 📍 Estado Actual: Fase 1 (Completada con Éxito) ✅

1. **Motor de Extracción Genérico (`backend/extractor.py`)**:
   - Parseo automático de BEOs de Opera de cualquier cliente y duración.
   - Soporte multi-día y multi-sesión con desglose por horas y salones (`Estudio 2 + 3`, `Sala Multifuncional`, `Pérgola Terraza`, etc.).
   - Extracción íntegra de gastronomía (menús, finger buffets, coffee breaks) y requerimientos técnicos (SSTT, climatización, protocolo AURA).
   - Deduplicación inteligente: si se vuelve a subir un BEO corregido, actualiza los montajes existentes sin duplicar tarjetas.
2. **Frontend PWA de Vanguardia (`frontend/`)**:
   - Identidad visual prémium inspirada en **ME by Meliá** y **Meliá Hotels International**.
   - Navegación táctil por días (*swipe gesture* y flechas).
   - Acordeones interactivos con planes de montaje, requerimientos de salas y menús.
   - Desplegado en **GitHub Pages**: `https://fvilpaz.github.io/me_vents/`.

---

## 🚀 Fase 2: Desacoplar del Localhost (Opciones de Arquitectura)

Actualmente, el backend de Python corre en tu PC (`http://127.0.0.1:8000`). Para que el equipo pueda subir un PDF directamente desde su teléfono o desde el ordenador de recepción, evaluamos las siguientes opciones:

### 🏆 Opción 1: Backend Python en la Nube + Base de Datos Ligera (Recomendada)
* **Cómo funciona**:
  - Alojar [backend/main.py](file:///d:/Fernando/Coding/github/Me_vents/backend/main.py) y [backend/extractor.py](file:///d:/Fernando/Coding/github/Me_vents/backend/extractor.py) en un servicio gratuito o de coste ínfimo como **Render**, **Railway** o **Fly.io**.
  - Los eventos ya no se guardan en un archivo JSON local, sino en una base de datos en la nube en tiempo real gratuita como **Supabase (PostgreSQL)** o **Firebase Firestore**.
* **Experiencia para el equipo**:
  - Entra a la web en su móvil o PC.
  - Pulsa el botón **"Nueva Orden (BEO)"**, selecciona el PDF del BEO descargado de Opera.
  - En 2 segundos, el backend en la nube procesa el PDF, guarda los montajes en la base de datos y la agenda se actualiza al instante en todos los móviles del equipo.
* **Ventajas**:
  - El equipo tiene autonomía total.
  - No requiere que tu ordenador esté encendido ni que abras terminales.
  - Soporta subida concurrente y sincronización en tiempo real.
* **Coste**: **0 € / mes** (Tanto Render/Railway como Supabase tienen tiers gratuitos generosos para este volumen).

---

### 💬 Opción 2: Bot de Telegram de Operaciones (Zero-UI para el equipo)
* **Cómo funciona**:
  - Creamos un bot de Telegram exclusivo (ej: `@MEMalagaEventsBot`).
  - El equipo simplemente abre Telegram, le reenvía el PDF de la orden de servicio al bot.
  - El bot procesa el archivo con el extractor de Python, responde con un resumen:
    > *«✅ BEO Procesado: Grupo Demo (19-25 Sep) — 11 montajes registrados en Estudio 2+3 y Multifuncional.»*
  - Y actualiza la base de datos de la web automáticamente.
* **Ventajas**:
  - Experiencia nativa y ultra cómoda para el personal de hotel (muchos usan WhatsApp/Telegram en su día a día).
  - No tienen que entrar a formularios de subida.
* **Coste**: **0 € / mes**.

---

### 📂 Opción 3: Carpeta Compartida de Google Drive + Webhook
* **Cómo funciona**:
  - Se crea una carpeta de Google Drive llamada `ME Málaga - BEOs Entrantes`.
  - Cuando el equipo o el departamento de Sales & Catering guarda ahí un PDF, un script en la nube (Google Apps Script o GitHub Action) lo detecta, lo procesa con `extractor.py` y publica los datos en la web.
* **Ventajas**:
  - Se integra de forma natural con los flujos de oficina de Meliá si ya usan Google Workspace.

---

### 🌐 Opción 4: Extractor 100% en el Navegador (WebAssembly / Pyodide)
* **Cómo funciona**:
  - Ejecutar Python dentro del propio navegador del usuario mediante WebAssembly (Pyodide).
  - No se necesita ningún servidor backend externo.
* **Ventajas**: Cero servidores que mantener.
* **Inconvenientes**: La carga inicial del navegador es más pesada (~10-15 MB) y los móviles de gama media pueden tardar unos segundos en inicializar el intérprete.

---

## 📋 Comparativa Rápida

| Solución | Autonomía del equipo | Facilidad de Uso | Coste | Tiempo de Implementación |
| :--- | :---: | :---: | :---: | :---: |
| **Opción 1: Render + Supabase** | ⭐⭐⭐⭐⭐ (Total) | ⭐⭐⭐⭐⭐ (Botón en la web) | **0 €** | 1-2 horas |
| **Opción 2: Bot de Telegram** | ⭐⭐⭐⭐⭐ (Total) | ⭐⭐⭐⭐⭐ (Reenviar archivo) | **0 €** | 1-2 horas |
| **Opción 3: Google Drive Sync** | ⭐⭐⭐⭐ (Alta) | ⭐⭐⭐⭐ (Guardar en Drive) | **0 €** | 2-3 horas |
| **Opción 4: WebAssembly (Pyodide)**| ⭐⭐⭐⭐ (Alta) | ⭐⭐⭐ (Carga pesada) | **0 €** | 3-4 horas |

---

## 🛠️ Fase 3: Próximas Funcionalidades Operativas

Una vez desacoplado el backend, las siguientes mejoras potenciarán el día a día del equipo:

1. **Checklist Operativo Interactivo de Sala**:
   - Botón para que el jefe de sala o montador marque:
     - `[X] Sala montada y alineada`
     - `[X] SSTT & Pantalla conectada`
     - `[X] Clima 22ºC activado`
     - `[X] Protocolo AURA perfumado`
   - Estado visual en la tarjeta: *Pendiente* 🟡 ➔ *En Proceso* 🔵 ➔ *Montada y Lista* 🟢.

2. **Vista de Impresión / Hoja de Sala (Door Sheet)**:
   - Botón "Imprimir Ficha de Sala" para generar en 1 clic un A4 con diseño corporativo ME Meliá para colgar en el atril o puerta del Estudio antes de que llegue el cliente.

3. **Filtro Rápido por Turno / Departamento**:
   - Filtros directos: *Solo Montajes*, *Solo Gastronomía (Cocina/Pase)*, *Solo Técnica (SSTT)*.

4. **Alertas de Cambios de Última Hora (Revisiones de BEO)**:
   - Si Opera emite una revisión (ej. `V.2` o cambio de 16 a 22 PAX), el sistema resalta automáticamente en color ámbar/rojo los campos modificados.

---

## 🎯 Plan de Acción Inmediato Sugerido

1. **Paso 1**: Probar con el equipo la versión actual en GitHub Pages (`https://fvilpaz.github.io/me_vents/`) para recoger su feedback de diseño, tamaño de letra y legibilidad en su teléfono real.
2. **Paso 2**: Implementar la **Opción 1 (Render + Supabase)** o la **Opción 2 (Bot de Telegram)** para que no tengas que levantar localhost nunca más.

---

## 📎 Anexo: Operativa local (archivada, oct-2026)

> Retirada por **protección de datos de clientes**: la app real ya no se ejecuta en este PC. El flujo
> diario es la PWA de GitHub Pages con la demo, que se regenera sola vía la Action `procesar-os.yml`.
> Se conserva aquí como referencia por si algún día se quiere recuperar la operativa 100% local.

El antiguo acceso directo del Escritorio (`ME_VENTS.bat`) hacía exactamente esto:

```bat
@echo off
title ME·VENTS - Servidor Local
cd /d D:\Fernando\Coding\github\Me_vents
start "" http://localhost:8000
uvicorn backend.main:app --reload --port 8000
```

- **Requisitos**: `pip install -r backend/requirements.txt`
- **Levanta** el backend FastAPI en `http://127.0.0.1:8000` (equivalente a la "Opción B" del README).
- **OS de demo en local**:
  ```bash
  python -m backend.generar_demo --salida inbox
  python -m backend.procesar_os --aplicar --consumir
  ```
