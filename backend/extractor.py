import re
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, date

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

def load_json(filename: str) -> Dict[str, Any]:
    file_path = CONFIG_DIR / filename
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

SPACES_CONFIG = load_json("hotel_spaces.json")
JARGON_CONFIG = load_json("jargon_dictionary.json")

def reload_config():
    global SPACES_CONFIG, JARGON_CONFIG
    SPACES_CONFIG = load_json("hotel_spaces.json")
    JARGON_CONFIG = load_json("jargon_dictionary.json")

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extrae texto plano de un documento PDF en memoria usando pypdf o pdfplumber."""
    extracted = ""
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        for idx, page in enumerate(reader.pages):
            t = page.extract_text()
            if t:
                extracted += f"\n--- Page {idx+1} ---\n" + t
    except Exception as e:
        print(f"pypdf extraction error: {e}")

    if len(extracted.strip()) < 30:
        try:
            import io
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for idx, page in enumerate(pdf.pages):
                    t = page.extract_text()
                    if t:
                        extracted += f"\n--- Page {idx+1} ---\n" + t
        except Exception as e:
            print(f"pdfplumber extraction error: {e}")

    return extracted.strip()

def match_space(text: str) -> Optional[Dict[str, Any]]:
    """Identifica el salón oficial de ME Málaga mediante los alias configurados."""
    reload_config()
    text_lower = text.lower()
    spaces = SPACES_CONFIG.get("spaces", [])
    
    # Prioridad 1: espacios combinados (ej: Estudio 2 + 3)
    for space in spaces:
        if "+" in space.get("id", ""):
            for alias in space.get("aliases", []):
                pattern = r'(?:^|\W)' + re.escape(alias) + r'(?:\W|$)'
                if re.search(pattern, text_lower):
                    return space

    # Prioridad 2: espacios individuales
    for space in spaces:
        for alias in sorted(space.get("aliases", []), key=len, reverse=True):
            pattern = r'(?:^|\W)' + re.escape(alias) + r'(?:\W|$)'
            if re.search(pattern, text_lower):
                return space
    return None

def match_setup(text: str) -> Dict[str, Any]:
    """Identifica el tipo de montaje según el diccionario de jerga."""
    reload_config()
    text_lower = text.lower()
    montajes = JARGON_CONFIG.get("montajes", [])
    
    for m in montajes:
        for alias in sorted(m.get("aliases", []), key=len, reverse=True):
            pattern = r'(?:^|\W)' + re.escape(alias) + r'(?:\W|$)'
            if re.search(pattern, text_lower):
                return m
                
    return {
        "key": "estandar",
        "label": "Montaje Estándar",
        "icon": "📋",
        "description": "Distribución a confirmar según orden de servicio"
    }

def match_services(text: str) -> List[Dict[str, Any]]:
    """Detecta servicios de F&B y equipamiento especial (CB, AV, mic, etc.)."""
    reload_config()
    text_lower = text.lower()
    services_found = []
    
    for fb in JARGON_CONFIG.get("servicios_fb", []):
        for alias in fb.get("aliases", []):
            pattern = r'(?:^|\W)' + re.escape(alias) + r'(?:\W|$)'
            if re.search(pattern, text_lower):
                services_found.append({
                    "type": "fb",
                    "key": fb["key"],
                    "label": fb["label"],
                    "icon": fb["icon"],
                    "details": fb.get("elements_recommended", "")
                })
                break
                
    for eq in JARGON_CONFIG.get("equipamiento", []):
        for alias in eq.get("aliases", []):
            pattern = r'(?:^|\W)' + re.escape(alias) + r'(?:\W|$)'
            if re.search(pattern, text_lower):
                services_found.append({
                    "type": "equipment",
                    "key": eq["key"],
                    "label": eq["label"],
                    "icon": eq["icon"]
                })
                break
                
    return services_found

def extract_pax(text: str) -> int:
    """Extrae el número de asistentes garantizados o previstos."""
    pax_patterns = [
        r'(?:pax|personas|asistentes|comensales)\s*[:=]?\s*(\d+)',
        r'(\d+)\s*(?:pax|personas|asistentes|comensales|pers)',
        r'aforo\s*[:=]?\s*(\d+)'
    ]
    for pattern in pax_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
                
    num_match = re.search(r'\b([1-9]\d{0,2})\s*(?:pax|px)\b', text, re.IGNORECASE)
    if num_match:
        return int(num_match.group(1))
        
    return 15

def extract_times(text: str) -> Dict[str, str]:
    """Extrae horario de inicio y fin del evento."""
    range_match = re.search(r'(\d{1,2}[:.]\d{2})\s*(?:-|a|hasta)\s*(\d{1,2}[:.]\d{2})', text)
    if range_match:
        start = range_match.group(1).replace(".", ":").zfill(5)
        end = range_match.group(2).replace(".", ":").zfill(5)
        return {"start": start, "end": end}
        
    single_match = re.search(r'\b(?:a\s+las|hora:?|inicio:?)\s*(\d{1,2}[:.]\d{2})\b', text, re.IGNORECASE)
    if single_match:
        start = single_match.group(1).replace(".", ":").zfill(5)
        return {"start": start, "end": "--:--"}
        
    return {"start": "09:00", "end": "14:00"}

def normalize_date_string(date_str: str) -> str:
    """Convierte texto como 20/09/26 o 20-09-2026 a formato ISO YYYY-MM-DD."""
    m = re.search(r'(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2,4})', date_str)
    if m:
        d, mon, y = m.groups()
        if len(y) == 2:
            y = "20" + y
        return f"{y}-{mon.zfill(2)}-{d.zfill(2)}"
    return date.today().isoformat()

def extract_date(text: str) -> str:
    """Extrae la primera fecha encontrada en formato YYYY-MM-DD."""
    match_dmy = re.search(r'\b(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2,4})\b', text)
    if match_dmy:
        return normalize_date_string(match_dmy.group(0))
        
    meses = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04", "mayo": "05", "junio": "06",
        "julio": "07", "agosto": "08", "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
    }
    for mes_nombre, mes_num in meses.items():
        pattern = rf'(\d{{1,2}})\s+de\s+{mes_nombre}(?:\s+de\s+(\d{{4}}))?'
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            d = m.group(1).zfill(2)
            y = m.group(2) if m.group(2) else str(datetime.now().year)
            return f"{y}-{mes_num}-{d}"
            
    return date.today().isoformat()

def calculate_operational_setup(space: Optional[Dict[str, Any]], setup: Dict[str, Any], pax: int) -> Dict[str, Any]:
    """Calcula las necesidades exactas de mobiliario, tiempos de montaje y valida aforo."""
    setup_key = setup.get("key", "estandar")
    
    mesas_rectangulares = 0
    mesas_redondas = 0
    mesas_altas = 0
    sillas = pax
    
    if setup_key == "u_shape":
        mesas_rectangulares = math.ceil(pax / 2) + 1
        sillas = pax
    elif setup_key == "escuela":
        mesas_rectangulares = math.ceil(pax / 2)
        sillas = pax
    elif setup_key == "banquete":
        mesas_redondas = math.ceil(pax / 8)
        sillas = pax
    elif setup_key == "coctel":
        mesas_altas = max(2, math.ceil(pax / 10))
        sillas = math.ceil(pax / 15)
    elif setup_key == "teatro":
        mesas_rectangulares = 0
        sillas = pax + 2
    elif setup_key == "imperial":
        mesas_rectangulares = math.ceil(pax / 2)
        sillas = pax
    elif setup_key == "cabaret":
        mesas_redondas = math.ceil(pax / 5)
        sillas = pax
    else:
        mesas_rectangulares = math.ceil(pax / 2)
        sillas = pax

    if pax <= 15:
        tiempo_montaje_min = 25
        tiempo_desmontaje_min = 15
    elif pax <= 40:
        tiempo_montaje_min = 45
        tiempo_desmontaje_min = 25
    else:
        tiempo_montaje_min = 75
        tiempo_desmontaje_min = 40

    warning_aforo = None
    if space and "max_capacities" in space:
        max_cap = space["max_capacities"].get(setup_key)
        if max_cap and pax > max_cap:
            warning_aforo = f"⚠️ Aforo advertencia: {pax} pax vs aforo de {max_cap} pax para montaje {setup.get('label')} en {space.get('name')}."

    return {
        "furniture": {
            "mesas_rectangulares": mesas_rectangulares,
            "mesas_redondas": mesas_redondas,
            "mesas_altas": mesas_altas,
            "sillas": sillas
        },
        "times": {
            "setup_minutes": tiempo_montaje_min,
            "breakdown_minutes": tiempo_desmontaje_min
        },
        "warning_aforo": warning_aforo
    }

def parse_multi_session_opera(raw_text: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parsea órdenes completas de Opera Sales & Catering (ej: Kevin Murphy, Paul Taplin)
    que contienen múltiples sesiones y días.
    """
    events = []
    
    # 1. Detectar bloques por página / día
    pages = raw_text.split("--- Page ")
    current_date = date.today().isoformat()
    client_name = "ME Event"
    
    # Extraer nombre del cliente / Cuenta / Block Name
    client_match = re.search(r'(?:Cuenta|Block Name:?)\s*([A-Za-z0-9_\-\.\s]{3,40})', raw_text)
    if client_match:
        client_name = client_match.group(1).replace("_", " ").strip().title()
    elif filename:
        clean_fn = re.sub(r'^(?:V\.\d+\s+)?(?:OS\s+)?', '', filename, flags=re.IGNORECASE)
        clean_fn = re.sub(r'\.(pdf|png|jpg|jpeg)$', '', clean_fn, flags=re.IGNORECASE)
        client_name = clean_fn.replace("_", " ").title()

    for page in pages:
        if not page.strip():
            continue
            
        # Buscar fecha de cabecera de página (ej: Domingo, 20/09/26)
        date_match = re.search(r'(?:Lunes|Martes|Mi[ée]rcoles|Jueves|Viernes|S[aá]bado|Domingo),\s*(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4})', page, re.IGNORECASE)
        if date_match:
            current_date = normalize_date_string(date_match.group(1))

        # Buscar filas de tabla Opera: "08:00 - 17:30 Estudio 2 + 3 MEETING ROOM Forma U 13 Pax"
        opera_table_pattern = r'(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})\s+([A-Za-z0-9\+\s]+?)\s+([A-Za-z\s]+?)\s+(Forma\s+U|U-shape|Escuela|Teatro|Imperial|Banquete|C[oó]ctel)\s+(\d+)\s*Pax'
        matches = list(re.finditer(opera_table_pattern, page, re.IGNORECASE))
        
        if matches:
            for m in matches:
                time_range = m.group(1)
                space_str = m.group(2).strip()
                event_name_str = m.group(3).strip()
                setup_str = m.group(4).strip()
                pax_val = int(m.group(5))
                
                times = extract_times(time_range)
                matched_space = match_space(space_str) or match_space(page) or {
                    "id": "multifuncional",
                    "name": "Sala Multifuncional",
                    "color_tag": "#7b2cbf",
                    "location": "Planta Baja"
                }
                matched_setup = match_setup(setup_str)
                services = match_services(page)
                operational = calculate_operational_setup(matched_space, matched_setup, pax_val)
                
                events.append({
                    "id": f"evt-{int(datetime.now().timestamp() * 1000)}-{len(events)}",
                    "title": f"{client_name} · {event_name_str.title()}",
                    "date": current_date,
                    "time_start": times["start"],
                    "time_end": times["end"],
                    "space": matched_space,
                    "setup": matched_setup,
                    "pax": pax_val,
                    "services": services,
                    "operational": operational,
                    "raw_snippet": page[:200].replace('\n', ' ')
                })
        else:
            # Si no hay tabla estructurada pero hay mención clara de reunión en F&B (ej: Paul Taplin)
            fb_match = re.search(r'F&B.*?(?:sala|estudio|foyer|terraza).*?(\d+)\s*(?:pax|personas)', page, re.IGNORECASE | re.DOTALL)
            if fb_match:
                single_evt = parse_event_order(page, filename=filename)
                single_evt["date"] = current_date
                single_evt["title"] = client_name
                # Evitar duplicados del mismo día y salón
                if not any(e["date"] == current_date and e["space"]["id"] == single_evt["space"]["id"] for e in events):
                    events.append(single_evt)

    # Si el parseo multi-sesión no sacó nada, recurrir al parseo estándar
    if not events:
        events.append(parse_event_order(raw_text, filename=filename))

    return events

def parse_event_order(raw_text: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """Función para una única sesión o entrada rápida en jerga."""
    space = match_space(raw_text)
    setup = match_setup(raw_text)
    services = match_services(raw_text)
    pax = extract_pax(raw_text)
    times = extract_times(raw_text)
    event_date = extract_date(raw_text)
    
    event_name = "Orden de Servicio"
    client_match = re.search(r'(?:Cuenta|Block Name:?)\s*([A-Za-z0-9_\-\.\s]{3,40})', raw_text)
    if client_match:
        event_name = client_match.group(1).replace("_", " ").strip().title()
    elif filename:
        clean_fn = re.sub(r'^(?:V\.\d+\s+)?(?:OS\s+)?', '', filename, flags=re.IGNORECASE)
        clean_fn = re.sub(r'\.(pdf|png|jpg|jpeg)$', '', clean_fn, flags=re.IGNORECASE)
        event_name = clean_fn.replace("_", " ").title()

    operational = calculate_operational_setup(space, setup, pax)
    
    return {
        "id": f"evt-{int(datetime.now().timestamp() * 1000)}",
        "title": event_name,
        "date": event_date,
        "time_start": times["start"],
        "time_end": times["end"],
        "space": space if space else {
            "id": "multifuncional",
            "name": "Sala Multifuncional",
            "color_tag": "#7b2cbf",
            "location": "Planta Baja"
        },
        "setup": setup,
        "pax": pax,
        "services": services,
        "operational": operational,
        "raw_snippet": raw_text[:200].replace('\n', ' ')
    }
