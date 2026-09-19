"""
Almacén de eventos compartido por el servidor (main.py) y el procesador por línea de comandos
(procesar_os.py, que usa la GitHub Action). Así los dos aplican exactamente la misma lógica.
"""
import json
from pathlib import Path
from typing import List, Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
BEOS_DIR = DATA_DIR / "beos"
FRONTEND_BEOS_DIR = ROOT_DIR / "frontend" / "data" / "beos"
EVENTS_FILE = DATA_DIR / "events.json"
FRONTEND_EVENTS_FILE = ROOT_DIR / "frontend" / "data" / "events.json"

DATA_DIR.mkdir(exist_ok=True)
BEOS_DIR.mkdir(exist_ok=True)
FRONTEND_BEOS_DIR.mkdir(parents=True, exist_ok=True)


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
    if FRONTEND_EVENTS_FILE.parent.exists():
        try:
            with open(FRONTEND_EVENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(events, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def merge_events(existing_events: List[Dict[str, Any]], new_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicación inteligente: si la orden entrante es de un grupo ya guardado (mismo Block ID, o mismo
    nombre de grupo en las mismas fechas), sustituye a la versión anterior en lugar de sumarse a ella.
    """
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
    return sorted(all_events, key=lambda x: (x.get("date", ""), x.get("time_start", "")))
