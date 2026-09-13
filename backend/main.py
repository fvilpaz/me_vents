import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.extractor import (
    extract_text_from_pdf,
    parse_multi_session_opera,
    SPACES_CONFIG,
    JARGON_CONFIG
)

app = FastAPI(
    title="ME·VENTS API — ME Málaga MICE & Events Production",
    description="Motor de análisis, extracción y gestión operativa de órdenes de servicio (OS) para ME by Meliá",
    version="2.0.0"
)

# CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
BEOS_DIR = DATA_DIR / "beos"
BEOS_DIR.mkdir(exist_ok=True)
FRONTEND_BEOS_DIR = Path(__file__).resolve().parent.parent / "frontend" / "data" / "beos"
FRONTEND_BEOS_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_FILE = DATA_DIR / "events.json"

def get_stored_events() -> List[Dict[str, Any]]:
    if EVENTS_FILE.exists():
        try:
            with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_stored_events(events: List[Dict[str, Any]]) -> None:
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    # Sincronizar automáticamente con frontend/data/events.json para GitHub Pages
    frontend_events = Path(__file__).resolve().parent.parent / "frontend" / "data" / "events.json"
    if frontend_events.parent.exists():
        try:
            with open(frontend_events, "w", encoding="utf-8") as f:
                json.dump(events, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

@app.get("/api/config")
def get_config():
    """Devuelve la configuración oficial de salones de ME Málaga y el diccionario de jerga."""
    from backend.extractor import SPACES_CONFIG, JARGON_CONFIG, reload_config
    reload_config()
    return {
        "spaces": SPACES_CONFIG.get("spaces", []),
        "jargon": JARGON_CONFIG
    }

@app.get("/api/glossary")
def get_glossary():
    """Devuelve el glosario completo de términos, jerga y protocolos."""
    from backend.extractor import JARGON_CONFIG, reload_config
    reload_config()
    return JARGON_CONFIG

@app.post("/api/glossary")
def add_glossary_term(term_data: Dict[str, Any]):
    """Añade un nuevo término al glosario de jerga hotelera."""
    config_file = Path(__file__).resolve().parent.parent / "config" / "jargon_dictionary.json"
    with open(config_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    terms = data.get("terms", [])
    # Generar ID
    term_id = term_data.get("id") or term_data.get("term", "").lower().replace(" ", "-")
    term_data["id"] = term_id
    
    # Reemplazar si ya existe o agregar
    terms = [t for t in terms if t.get("id") != term_id]
    terms.append(term_data)
    data["terms"] = terms
    
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    # Sincronizar automáticamente con frontend/data/jargon_dictionary.json para GitHub Pages
    frontend_jargon = Path(__file__).resolve().parent.parent / "frontend" / "data" / "jargon_dictionary.json"
    if frontend_jargon.parent.exists():
        try:
            with open(frontend_jargon, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    from backend.extractor import reload_config
    reload_config()
    return {"status": "success", "term": term_data}


@app.get("/api/events")
def get_events():
    """Obtiene la lista de eventos registrados."""
    return get_stored_events()

@app.post("/api/events")
def create_event(event: Dict[str, Any]):
    """Crea un evento de forma manual."""
    events = get_stored_events()
    events.append(event)
    save_stored_events(events)
    return {"status": "success", "event": event}

@app.delete("/api/events")
@app.post("/api/events/clear")
def clear_events():
    """Limpia todos los eventos almacenados."""
    save_stored_events([])
    return {"status": "success", "message": "Todos los eventos han sido eliminados"}

@app.delete("/api/events/{event_id}")
def delete_event(event_id: str):
    """Elimina un evento registrado."""
    events = get_stored_events()
    new_events = [e for e in events if e.get("id") != event_id]
    save_stored_events(new_events)
    return {"status": "success", "deleted": event_id}

@app.post("/api/upload-os")
@app.post("/api/upload-beo")
async def upload_order(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None)
):
    """
    Procesa una orden de servicio (OS / BEO).
    Soporta órdenes multi-día y multi-sesión de Opera con validaciones de seguridad.
    """
    text_content = ""
    filename = None
    
    if file:
        # Prevenir Path Traversal sanitizando el nombre del archivo
        filename = Path(file.filename).name
        # Limitar tamaño a 20MB para mitigar ataques DoS por agotamiento de memoria
        content = await file.read()
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="El archivo excede el tamaño máximo permitido (20 MB).")
            
        if filename.lower().endswith(".pdf"):
            text_content = extract_text_from_pdf(content)
            try:
                with open(BEOS_DIR / filename, "wb") as f_out:
                    f_out.write(content)
                with open(FRONTEND_BEOS_DIR / filename, "wb") as f_front:
                    f_front.write(content)
            except Exception as e:
                print(f"Aviso guardando copia PDF: {e}")
        else:
            try:
                text_content = content.decode("utf-8", errors="ignore")
            except Exception:
                text_content = ""
                
    if isinstance(raw_text, str) and len(raw_text.strip()) > 0:
        # Limitar longitud de texto
        safe_raw = raw_text.strip()[:100000]
        text_content = (text_content + "\n" + safe_raw).strip()
        
    if not text_content:
        raise HTTPException(
            status_code=400,
            detail="No se ha podido extraer texto del documento."
        )
        
    # Procesar con el motor multi-sesión de Opera
    new_events = parse_multi_session_opera(text_content, filename=filename)
    
    # Deduplicación inteligente:
    existing_events = get_stored_events()
    
    # Si la orden entrante es un evento multi-día o de un grupo específico,
    # sustituimos cualquier versión anterior de ese mismo grupo o fechas para evitar duplicados
    new_block_id = new_events[0].get("block_id") if new_events else None
    new_group = new_events[0].get("multi_day", {}).get("group_name") if new_events else None
    new_dates = set(ne.get("date") for ne in new_events if ne.get("date"))
    
    kept_events = []
    for e in existing_events:
        e_block = e.get("block_id")
        e_group = e.get("multi_day", {}).get("group_name")
        e_date = e.get("date")
        
        # Si es del mismo Block ID o del mismo grupo en las mismas fechas, se sustituye
        if new_block_id and e_block and e_block == new_block_id:
            continue
        if new_group and e_group and e_group.lower() == new_group.lower() and e_date in new_dates:
            continue
        kept_events.append(e)

    all_events = kept_events + new_events
    all_events = sorted(all_events, key=lambda x: (x.get("date", ""), x.get("time_start", "")))
    save_stored_events(all_events)
    
    return {
        "status": "success",
        "events_count": len(all_events),
        "events": all_events,
        "new_count": len(new_events),
        "first_event": new_events[0] if new_events else None
    }

@app.get("/api/os/{filename}")
@app.get("/api/beos/{filename}")
def get_order_pdf(filename: str):
    """Sirve un archivo PDF de OS original para visualización."""
    safe_name = Path(filename).name
    
    # 1. Buscar en data/beos
    p1 = BEOS_DIR / safe_name
    if p1.exists() and p1.is_file():
        return FileResponse(p1, media_type="application/pdf", filename=safe_name)
        
    # 2. Buscar en frontend/data/beos
    p2 = FRONTEND_BEOS_DIR / safe_name
    if p2.exists() and p2.is_file():
        return FileResponse(p2, media_type="application/pdf", filename=safe_name)

    # 3. Buscar en sources/ods
    sources_ods = Path(__file__).resolve().parent.parent / "sources" / "ods" / safe_name
    if sources_ods.exists() and sources_ods.is_file():
        return FileResponse(sources_ods, media_type="application/pdf", filename=safe_name)

    raise HTTPException(status_code=404, detail=f"Documento de orden de servicio '{safe_name}' no encontrado")

# Servir Frontend estático si existe
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
