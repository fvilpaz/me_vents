# Me_vents — ME Málaga Operations & Banquets Suite

[![Brand](https://img.shields.io/badge/Brand-ME_by_Meliá-0080ff.svg)](https://www.melia.com)
[![Hotel](https://img.shields.io/badge/Hotel-ME_Málaga-blue.svg)]()
[![PWA](https://img.shields.io/badge/PWA-Offline_Ready-success.svg)]()

**Me_vents** es una aplicación Progressive Web App (PWA) de diseño vanguardista y alta fidelidad estética inspirada en el universo visual de **ME by Meliá** y **Meliá Hotels International**.

Diseñada para **Fai** y el equipo de operaciones/banquetes de ME Málaga para simplificar y automatizar la gestión y montaje de eventos a partir de órdenes de servicio (BEO) en PDF o fotografías.

---

## ✨ Características Principales

1. **Dashboard Táctil Deslizable por Días**:
   - Navegación horizontal fluida (*swipe gesture*) con el dedo en móviles o con flechas en PC.
   - Indicador de montajes diarios y cómputo de comensales (PAX).
2. **Cards de Montaje de Alto Impacto Visual**:
   - Salón oficial con código cromático exclusivo por espacio.
   - Tipo de montaje (*Herradura / U-Shape, Escuela, Banquete, Cóctel, Teatro, Imperial*).
   - Desglose operativo interactivo: cálculo exacto de mesas (rectangulares, redondas, altas), sillas a bajar de almacén y tiempos estimados de montaje y desmontaje.
   - Checkbox interactivo de confirmación de montaje en sala.
3. **Diccionario de Jerga Hotelera & Normalización**:
   - Comprensión automática de abreviaturas del sector:
     - `CB`, `c.b`, `coffee break`, `pausa café` &rarr; ☕ Coffee Break.
     - `lunch`, `almuerzo`, `finger buffet` &rarr; 🥪 Almuerzo de trabajo.
     - `welcome drink`, `copa bienvenida`, `cava` &rarr; 🥂 Welcome Drink.
     - `u-shape`, `herradura`, `en u` &rarr; 🧲 Montaje en U.
     - `av`, `audiovisuales`, `pantalla`, `clicker` &rarr; 🎥 Audiovisuales.
4. **Catálogo de Salones de ME Málaga**:
   - Estudio 1, Estudio 2, Estudio 3, Estudio 4, Estudio 5.
   - Foyer.
   - Sala Multifuncional.
   - Preparado para exteriores: Cañitas al Fresco y Terraza / Rooftop.
5. **Motor Híbrido (Online / Offline)**:
   - Backend en **Python (FastAPI)** con `pypdf`/`pdfplumber` para ingesta de documentos.
   - Motor cliente de respaldo en **JavaScript**: la PWA funciona y procesa texto de órdenes en local aunque no haya conexión o servidor levantado.

---

## 🚀 Puesta en Marcha Rápida

### Opción A: Probar la PWA directamente en el navegador
Puedes abrir directamente el archivo `frontend/index.html` en cualquier navegador web moderno o servir la carpeta `frontend/` con cualquier servidor HTTP ligero:

```bash
# Con Python
python -m http.server 8000 --directory frontend
```

Abre en tu navegador: [http://localhost:8000](http://localhost:8000)

### Opción B: Ejecutar con el Backend FastAPI
1. Instalar dependencias de Python:
```bash
pip install -r backend/requirements.txt
```

2. Arrancar el servidor Uvicorn:
```bash
uvicorn backend.main:app --reload --port 8000
```

---

## 📁 Estructura del Repositorio

```
Me_vents/
├── backend/
│   ├── main.py              # API FastAPI y gestión de endpoints
│   ├── extractor.py         # Motor de parseo de PDFs, cálculo de ratios y jerga
│   └── requirements.txt     # Dependencias de Python
├── config/
│   ├── hotel_spaces.json    # Catálogo de salones y aforos de ME Málaga
│   └── jargon_dictionary.json # Mapeo de términos, abreviaturas y servicios
├── data/
│   └── events.json          # Almacenamiento y eventos de muestra
├── frontend/
│   ├── index.html           # Interfaz principal de la PWA
│   ├── css/
│   │   └── style.css        # Sistema de diseño ME by Meliá (dark mode & neon)
│   ├── js/
│   │   └── app.js           # Controlador reactivo y gestos táctiles
│   ├── manifest.json        # Manifiesto PWA para instalación en móvil
│   ├── sw.js                # Service Worker para funcionamiento offline
│   └── assets/
│       └── images/          # Logos de ME Málaga, Meliá y foto de Fai
└── sources/                 # Carpeta para documentos BEO de entrada
```
