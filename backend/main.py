import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from backend.extractor import (
    extract_text_from_pdf,
    parse_multi_session_opera,
    SPACES_CONFIG,
    JARGON_CONFIG
)

app = FastAPI(
    title="Me_vents API - ME Málaga",
    description="Motor de análisis y gestión operativa de montajes de eventos para ME by Meliá",
    version="1.1.0"
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

@app.post("/api/upload-beo")
async def upload_beo(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None)
):
    """
    Procesa una orden de servicio (BEO).
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
    
    # Deduplicación inteligente: si ya existen eventos para la misma fecha, hora y salón, se actualizan limpiamente
    existing_events = get_stored_events()
    event_map = {}
    for e in existing_events:
        sp_id = e.get("space", {}).get("id", "default")
        key = f"{e.get('date')}_{e.get('time_start')}_{sp_id}"
        event_map[key] = e

    for ne in new_events:
        sp_id = ne.get("space", {}).get("id", "default")
        key = f"{ne.get('date')}_{ne.get('time_start')}_{sp_id}"
        event_map[key] = ne

    # Reordenar cronológicamente por fecha y hora
    updated_events = sorted(list(event_map.values()), key=lambda x: (x.get("date", ""), x.get("time_start", "")))
    save_stored_events(updated_events)
    
    return {
        "status": "success",
        "events_count": len(new_events),
        "events": new_events,
        "first_event": new_events[0] if new_events else None
    }

# Servir Frontend estático si existe
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
