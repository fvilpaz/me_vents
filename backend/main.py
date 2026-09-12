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

@app.get("/api/config")
def get_config():
    """Devuelve la configuración oficial de salones de ME Málaga y el diccionario de jerga."""
    return {
        "spaces": SPACES_CONFIG.get("spaces", []),
        "jargon": JARGON_CONFIG
    }

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
    Soporta órdenes multi-día y multi-sesión de Opera.
    """
    text_content = ""
    filename = None
    
    if file:
        filename = file.filename
        content = await file.read()
        if filename.lower().endswith(".pdf"):
            text_content = extract_text_from_pdf(content)
        else:
            try:
                text_content = content.decode("utf-8", errors="ignore")
            except Exception:
                text_content = ""
                
    if raw_text and len(raw_text.strip()) > 0:
        text_content = (text_content + "\n" + raw_text).strip()
        
    if not text_content:
        raise HTTPException(
            status_code=400,
            detail="No se ha podido extraer texto del documento."
        )
        
    # Procesar con el motor multi-sesión de Opera
    new_events = parse_multi_session_opera(text_content, filename=filename)
    
    # Guardar en almacenamiento
    events = get_stored_events()
    events.extend(new_events)
    save_stored_events(events)
    
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
