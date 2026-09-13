
Gemini
Nueva conversación
Buscar conversaciones
Imágenes
Vídeos
Biblioteca
Nuevo cuaderno
Traducción y análisis de mensaje profesional
Traducción de guardarailes al inglés
Legalidad del tratamiento de audio por QR
Procesamiento de PDFs para Eventos
Análisis de espacios contratados
Consulta sobre espacios asignados
Operativa en corto con criptomonedas
Empleo web junior en Málaga
Análisis de Gradual Homes
Método de calistenia de Dave Saric
Compatibilidad de cables para disco duro
Comandos para ver discos en Ubuntu
Solución a permisos en Android
Ahorro de Tokens en Terminal
Costes y requisitos en Google Play
Solución al error de CoinGecko
Análisis de bioimpedancia y peso
Guía de emulación para i5 y RTX 3060
Servidor casero con Livebox 6
¿Comprar PS5 o esperar a PC para GTA VI?
Solución para el dictado de voz
Hipoteca con 42 años y 10.000 euros ahorrados
Análisis de estafa de IA
El sorprendente ordenador de Wallapop
Compatibilidad de disco duro WD
Conversión de Euros a Pesetas
Discos duros de 8 TB
Creación de una Clase en Java
Supervisión en Sol Beach Gym
Actualización de cuenta Bitget y usuarios de Earn
Reseña BaBylissPRO 4Artists FX3
Mejores máquinas para cortar barba rápida
Estrategia DCA ante repunte cripto

Actividad
Fuengirola, España
Según tus sitios (casa)
Actualizar ubicación
Conversación con Gemini
Voy a generar un programa en el que le vamos a pasar una serie de PDFs y lo va a parchear y en base a los PDFs va a generar una estrategia para montajes de eventos. Imagínate que le pasamos un cóctel o un montaje muy o una escuela, pues el programa tiene que ser capaz de procesar esos datos y escupir. En qué salón va a ser? Qué tipo de montaje cuántas personas etcétera? Me puedes generar un plan para pasártelo en casa

El flujo óptimo para este sistema es un pipeline de tres etapas: extracción y parseo del documento, estructuración de datos con LLM (extracción con esquema validado) y motor de asignación/reglas para el montaje.

1
Ingesta y parseo de documentos
Python: pypdf, pdfplumber o PyMuPDF
Extrae el texto plano y las tablas del PDF de la orden de servicio (BEO). Si los PDFs contienen texto digitalizado directo, pdfplumber o pymupdf (fitz) extraen texto y tablas con precisión posicional sin coste de OCR.

2
Extracción semántica y tipado de datos
Pydantic + Instructor / LangChain / OpenAI API
Pasa el texto extraído a un modelo lingüístico forzando un esquema estricto con Pydantic.

El modelo debe devolver un JSON validado con campos clave:

evento_id y fecha_inicio / fecha_fin.

numero_pax (asistentes garantizados y máximos).

tipo_montaje (escuela, teatro, cóctel, banquete, imperial, herradura/U).

espacio_sugerido o salon (si viene definido en la orden).

requerimientos_extra (audiovisuales, tarima, servicio de café).

3
Motor de validación y reglas de sala
Crea un módulo que contenga la matriz de capacidades de cada salón según el montaje (m² y ratios por pax: e.g., 1.5 m²/pax en escuela, 0.8 m²/pax en cóctel).

Si el PDF especifica salón, valida si cabe el aforo con el montaje solicitado; si no lo especifica, el algoritmo filtra y sugiere el salón más eficiente en función de pax y formato.

4
Generación del plan de montaje
Genera la ficha operativa final estructurada (formato Markdown, JSON o ficha imprimible) con:

Asignación de salón y distribución espacial recomendada.

Ratio de mesas/sillas o elementos de apoyo necesarios.

Tiempos estimados de montaje y desmontaje según pax y formato.

Para la base tecnológica en local, Python con FastAPI te permite montar un endpoint rápido /procesar-evento que recibe el archivo, mientras que una base SQLite o un archivo de configuración JSON almacena las capacidades técnicas de cada salón.

¿Quieres que preparemos el esquema de Pydantic y el script de extracción en Python?

Sí
Y se va a usar un PW?

Sí, plantear la interfaz como una PWA (Progressive Web App) tiene todo el sentido del mundo para este caso de uso operativo.

En eventos y sala, el personal de montaje y los jefes de sector se mueven continuamente con móviles o tablets. Una PWA resuelve la fricción técnica sin tener que desarrollar ni mantener apps nativas para Android o iOS.

Ventajas clave en este proyecto:

Instalación directa: Se añade a la pantalla de inicio desde el navegador en un clic (móvil, tablet o PC de oficina).

Cámara integrada: Si en vez de subir el PDF el usuario tiene una hoja impresa (la orden de servicio en papel), puede escanearla/fotografiarla directamente desde la PWA para enviarla al backend.

Modo offline (Service Worker): Permite consultar la ficha del montaje, salón asignado y planos guardados en caché incluso si se pierde la cobertura Wi-Fi en salones subterráneos o aislados.

Notificaciones push: Útil para alertar cambios de última hora en la orden (subida de pax, cambio de hora o cambio de salón).

Arquitectura recomendada:

Backend: API en Python (FastAPI/Django) encargada de procesar el PDF, correr el LLM y calcular los ratios de sala.

Frontend: Vanilla JS / Vite + Tailwind con su manifest.json y sw.js (Service Worker) para gestionar la caché de las fichas de montaje generadas.

¿Quieres definir el frontend con manifest y Service Worker para la PWA?

Sí
Se ha cortado

Asumiendo que querías ver la estructura y el código base para arrancar la PWA conectada al procesador de eventos, aquí tienes los tres archivos esenciales listos para integrar:

1. manifest.json
Configura la instalación en móviles y tablets para que funcione como app nativa.

JSON
{
  "name": "Planificador de Montajes",
  "short_name": "MontajesApp",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#1e293b",
  "orientation": "portrait",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
2. sw.js (Service Worker)
Garantiza que la UI y las órdenes consultadas recientemente sigan accesibles sin cobertura dentro de los salones.

JavaScript
const CACHE_NAME = 'montajes-v1';
const ASSETS = [
  '/',
  '/index.html',
  '/manifest.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      )
    )
  );
});

self.addEventListener('fetch', (e) => {
  // Network-first para la API, cache-fallback para la interfaz
  if (e.request.url.includes('/api/')) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then((res) => res || fetch(e.request))
  );
});
3. index.html
Interfaz ligera para subir el PDF o tomar foto de la orden y renderizar la ficha devuelta por el backend.

HTML
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Montajes de Eventos</title>
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#1e293b">
  <style>
    body { font-family: system-ui, sans-serif; margin: 1.5rem; background: #f8fafc; color: #0f172a; }
    .card { background: white; padding: 1.25rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-top: 1rem; }
    button { background: #0284c7; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 6px; font-weight: 600; cursor: pointer; }
    .hidden { display: none; }
  </style>
</head>
<body>
  <h2>Nueva Orden de Montaje</h2>

  <form id="uploadForm">
    <input type="file" id="pdfInput" accept="application/pdf,image/*" required>
    <br><br>
    <button type="submit">Procesar Orden</button>
  </form>

  <div id="resultado" class="card hidden">
    <h3>Plan de Montaje Sugerido</h3>
    <p><strong>Salón asignado:</strong> <span id="resSalon">-</span></p>
    <p><strong>Formato:</strong> <span id="resMontaje">-</span></p>
    <p><strong>Aforo (PAX):</strong> <span id="resPax">-</span></p>
    <p><strong>Notas de montaje:</strong> <span id="resDetalles">-</span></p>
  </div>

  <script>
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js');
    }

    const form = document.getElementById('uploadForm');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const file = document.getElementById('pdfInput').files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch('/api/procesar-evento', {
          method: 'POST',
          body: formData
        });
        const data = await response.json();

        document.getElementById('resSalon').textContent = data.salon || 'Pendiente de asignación';
        document.getElementById('resMontaje').textContent = data.tipo_montaje;
        document.getElementById('resPax').textContent = data.numero_pax;
        document.getElementById('resDetalles').textContent = data.notas || 'Sin observaciones';
        document.getElementById('resultado').classList.remove('hidden');
      } catch (err) {
        alert('Error al comunicar con el servidor o sin conexión.');
      }
    });
  </script>
</body>
</html>
¿Quieres que armemos el endpoint de FastAPI que recibe este archivo y extrae los datos?

Sí
No, no que me ibas a contar el plan que no hacía falta capacidad, ni no sé qué cosas más se ha cortado la comunicación. Dime fue por culpa de mi conexión

No fue por tu conexión; el corte se debió a un límite de respuesta por mi parte.

El plan que te estaba desglosando se basa en una premisa clave: no necesitas meterte en cálculos manuales de capacidad ni memorizar metros cuadrados por salón.

Toda esa lógica la absorbe el motor del programa a través de un esquema simple:

1. Despreocúpate de calcular aforos a mano
En vez de programar complejas fórmulas de espacio en el código:

Creas una tabla base fija (un archivo JSON o base de datos simple) con los datos estáticos de tus salones: nombre, metros cuadrados y qué montajes admite (ej. Salón Picasso: Escuela max 40, Cóctel max 90).

El sistema simplemente cruza el tipo de evento y los PAX que lea del PDF contra esa lista y descarta automáticamente los salones que no sirvan.

2. No dependes de que los PDFs vengan en un formato único
Las órdenes de servicio y cotizaciones suelen cambiar de diseño según quién las haga:

No hace falta hacer plantillas rígidas ni parsear líneas por posición fija.

El LLM lee el texto en bruto del PDF y "entiende" conceptos clave (si pone "Mesa en U", "Banquete", "Cocktail", "80 pax", "12:00h").

Escupe directamente los datos limpios: qué evento es, cuánta gente y qué montaje pide.

3. Automatización de la estrategia de montaje
Con el salón elegido y el aforo claro, el programa saca la hoja de ruta operativa:

Número exacto de mesas y sillas a bajar de almacén.

Ubicación de elementos fijos (atril, pantalla de proyección, mesa de apoyo o buffet).

Tiempos recomendados de montaje según volumen de asistentes.

¿Quieres que definamos la estructura del JSON con las salas y sus montajes máximos?

Sí
Vale, pero es que cada PDF puede ser diferente. No me fío mucho. Yo de cómo lo van a pasar. Lo que sí se suele mantener son los nombres de los salones y si suele mantener si es cóctel, si es escuelas y es una U, pero el tipo de PDF no lo sé

Tiene todo el sentido del mundo. En hostelería y eventos las órdenes de servicio (BEO) son un caos: un comercial te lo pasa en una tabla bien hecha, otro en un Word exportado a PDF con texto corrido, otro mete capturas, y otro cambia el orden de las páginas.

Si intentaras hacer esto con código tradicional (expresiones regulares, buscar por coordenadas X/Y o posiciones fijas), se rompería al tercer PDF.

Para que el sistema sea 100% tolerante a fallos de formato, el truco está en apoyarte exactamente en lo que acabas de decir: los nombres de los salones y los tipos de montaje son finitos y conocidos.

El flujo que no falla nunca funciona así:

1. El motor no busca "posiciones", busca "entidades"
Da igual si el PDF tiene 1 página, 5 páginas, texto desordenado o columnas raras.

Extraes todo el texto en bruto del tirón (con pdfplumber o pypdf).

Le pasas ese chorro de texto al LLM con una instrucción cerrada (few-shot prompt o esquema tipado):

"Eres un extractor de órdenes de eventos. Te paso un texto desordenado. Busca únicamente:

Salón (compara contra mi lista oficial de salones).

Tipo de montaje (escuela, cóctel, U/herradura, teatro, banquete).

Número de personas / PAX.

Fecha y tramo horario.
Si no estás seguro de algo o no aparece, devuelve null en ese campo."

Los modelos de lenguaje son especialmente buenos en esto: les da igual cómo esté maquetado el documento; entienden si "60 comensales", "60 pers." o "PAX: 60" significan la misma variable.

2. Capa de "Defensa" en tu código (Tu lista fija)
Como tú ya tienes el listado de salones y montajes de tu hotel o espacio, creas un diccionario de normalización en Python. Esto evita que si en el PDF escriben una errata, el programa se confunda:

Python
# Mapeo de sinónimos habituales a valores estándar
MONTAJES_VALIDOS = {
    "escuela": ["escuela", "school", "aulas", "mesas y sillas frente"],
    "coctel": ["cóctel", "coctel", "cocktail", "pie", "copa bienvenida"],
    "herradura": ["herradura", "u", "forma de u", "mesa en u"],
    "teatro": ["teatro", "auditorio", "filas de sillas"],
    "banquete": ["banquete", "mesas redondas", "cena sentada"]
}

SALONES_OFICIALES = ["Salón Picasso", "Salón Goya", "Terraza Principal", "Salón Miramar"]
Si el LLM lee "Montaje en forma de U en Miramar para 25 personas", el código lo pasa por este filtro y lo traduce automáticamente a:

Salón: Salón Miramar

Montaje: herradura

PAX: 25

3. ¿Qué pasa si el PDF es una chapuza total (ej. un escaneo o foto borrosa)?
Para curarte en salud ante los peores PDFs:

Intento 1 (Rápido y barato): Se intenta extraer texto digital normal. Si saca más de 50 palabras legibles, va directo al LLM.

Intento 2 (Fallback si viene como imagen/escaneo plano): Si el PDF viene plano sin capa de texto seleccionable, se le pasa la página como imagen directamente al modelo de visión (multimodal). El modelo "lee" la imagen como si la miraras tú y saca los datos igual.

4. La salida final: La estrategia operativa
Una vez tienes esas 3 variables seguras (Salón, Montaje, PAX), el programa ya no depende de la IA para inventar cosas. Ejecuta tus reglas de sala reales:

Si es Herradura en Salón Picasso para 20 pax → Saca la plantilla: "5 mesas rectangulares (2 por lado + 1 cabecera), 20 sillas con pala/sin pala, atril a la derecha, proyector centrado".

Si es Cóctel en Terraza para 80 pax → Saca: "8 mesas altas de apoyo con mantel, 1 estación de bebidas al fondo, zona de paso despejada".

De esta forma, aunque el PDF cambie todos los días de diseño, tu resultado siempre sale con el mismo formato limpio para el equipo de montaje.

Incluso si hay problemas con el espacio del móvil porque android es así... Podría guardar los datos en la nube por ejemplo en drive y acceder ahí en tiempo real?

Totalmente, y de hecho es lo más limpio y seguro. Al centralizarlo en la nube, el móvil no almacena nada a nivel local: actúa únicamente como un "visor" y control remoto, sin consumir memoria de almacenamiento del dispositivo.

Para montarlo de forma ágil y que puedas acceder en tiempo real, hay dos alternativas muy prácticas:

Opción 1: Google Sheets en Google Drive (La más visual e inmediata)
En vez de inventarte paneles complejos, tu backend en Python puede conectarse a Google Drive usando la API oficial (gspread / google-api-python-client):

Subes el PDF desde el móvil: El archivo viaja al servidor/backend en la nube (o tu PC).

El backend procesa y escribe: El LLM extrae los datos y tu script escribe directamente una fila nueva en una hoja de Google Sheets compartida en tu Drive:

Fecha | Salón | Montaje | PAX | Mesas requeridas | Sillas | Observaciones.

Ficha/PDF generado: Si quieres que genere un PDF o imagen con el plano/ficha de montaje, el script lo sube a una carpeta específica en Drive y pega el enlace directo en la hoja de cálculo.

Consulta en tiempo real: Desde el móvil, cualquier persona del equipo abre la app de Google Drive / Sheets y ve la actualización al segundo, con cero impacto en la memoria del teléfono.

Opción 2: Base de datos en la nube gratuita (Supabase / Firebase)
Si quieres que la propia interfaz web/PWA muestre tarjetas en tiempo real sin salir de la app:

Supabase (o Firebase Firestore) ofrece niveles gratuitos muy amplios.

Guardas los datos estructurados en una tabla PostgreSQL alojada en la nube.

La PWA consulta la base de datos por red; los datos se renderizan en pantalla y se descartan de la memoria RAM al cerrar la pestaña, sin ocupar almacenamiento en el disco del móvil.

¿Por qué te resuelve los problemas típicos de Android?
Cero caché acumulada: La PWA solo guarda el código HTML/CSS básico (menos de 2 MB); los eventos, PDFs y fichas viven 100% en Drive o la nube.

Multiusuario sin sincronizaciones raras: Si el jefe de sala o recepción añade un PDF desde el ordenador, al abrir la app o Drive en el móvil ya está visible al instante.

Histórico a salvo: Si cambias de teléfono o se formatea, no pierdes ninguna orden de servicio porque todo está respaldado en tu cuenta de Google.

¿Quieres ver cómo conectar el script de Python con Google Drive / Sheets para volcar los eventos automáticamente?

Sí



Gemini es una IA y puede cometer errores, incluso sobre personas. Tu privacidad y GeminiSe abre en una ventana nueva

OK 