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
    
    # Prioridad 1: combinados o multi-estudios (ej: Estudio 2 + 3 + 4 + 5, Estudio 2 + 3)
    for space in spaces:
        if "+" in space.get("id", "") or "all" in space.get("id", ""):
            for alias in sorted(space.get("aliases", []), key=len, reverse=True):
                pattern = r'(?:^|\W)' + re.escape(alias) + r'(?:\W|$)'
                if re.search(pattern, text_lower):
                    return space

    # Prioridad 2: espacios individuales (Estudio 1..5, Multifuncional, Cañitas, Terraza, etc.)
    for space in spaces:
        for alias in sorted(space.get("aliases", []), key=len, reverse=True):
            pattern = r'(?:^|\W)' + re.escape(alias) + r'(?:\W|$)'
            if re.search(pattern, text_lower):
                return space
    return None

def match_setup(text: str) -> Dict[str, Any]:
    """Identifica el tipo de montaje según la jerga hotelera oficial de ME Málaga."""
    reload_config()
    text_lower = text.lower()
    terms = JARGON_CONFIG.get("terms", [])
    montajes = [t for t in terms if t.get("category") == "montajes"]
    
    for m in montajes:
        for alias in sorted(m.get("aliases", []), key=len, reverse=True):
            pattern = r'(?:^|\W)' + re.escape(alias) + r'(?:\W|$)'
            if re.search(pattern, text_lower):
                return {
                    "key": m.get("id", "estandar"),
                    "label": m.get("term", "Montaje"),
                    "icon": m.get("icon", "🏛️"),
                    "description": m.get("definition", "")
                }
                
    return {
        "key": "estandar",
        "label": "Montaje Estándar",
        "icon": "📋",
        "description": "Distribución a confirmar según orden de servicio"
    }

def match_services(text: str) -> List[Dict[str, Any]]:
    """Detecta servicios de F&B, SSTT y Protocolo según el glosario."""
    reload_config()
    text_lower = text.lower()
    services_found = []
    terms = JARGON_CONFIG.get("terms", [])
    
    for t in terms:
        if t.get("category") == "montajes":
            continue
        for alias in sorted(t.get("aliases", []), key=len, reverse=True):
            pattern = r'(?:^|\W)' + re.escape(alias) + r'(?:\W|$)'
            if re.search(pattern, text_lower):
                services_found.append({
                    "type": t.get("category"),
                    "key": t.get("id"),
                    "label": t.get("term"),
                    "icon": t.get("icon", "✨"),
                    "details": t.get("operational_tip") or t.get("definition", "")
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

def extract_section_notes(text: str) -> Dict[str, Any]:
    """
    Extrae las notas e instrucciones operativas reales del BEO:
    - Montaje (instrucciones textuales de distribución)
    - SSTT (audiovisuales, megafonía, TVs, climatización)
    - F&B (coffee breaks, almuerzos, cenas, bebidas, minutas)
    - Pisos / Aura / Protocolo
    - Tiempos de montaje previos
    """
    montaje_notes = []
    sstt_notes = []
    fb_notes = []
    pisos_notes = []
    timing_notes = []
    explicit_furniture = {}

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    in_section = None
    for line in lines:
        lower = line.lower()
        
        # Detectar cabeceras de sección
        if line.startswith("SSTT") or line.startswith("COMERCIAL") or "audiovisuales" in lower[:15]:
            in_section = "sstt"
            clean_l = re.sub(r'^(?:SSTT|COMERCIAL)\s*:?\s*', '', line).strip()
            if clean_l: sstt_notes.append(clean_l)
            continue
        elif line.startswith("F&B MONTAJE") or "montaje de la sala" in lower or lower.startswith("montaje:"):
            in_section = "montaje"
            clean_l = re.sub(r'^(?:F&B MONTAJE|Montaje:?)\s*', '', line, flags=re.IGNORECASE).strip()
            if clean_l: montaje_notes.append(clean_l)
            continue
        elif line.startswith("F&B") or line.startswith("Servicio Comida") or line.startswith("Servicio Bebida"):
            in_section = "fb"
            clean_l = re.sub(r'^(?:F&B|Servicio Comida|Servicio Bebida)\s*:?\s*', '', line).strip()
            if clean_l: fb_notes.append(clean_l)
            continue
        elif line.startswith("PISOS") or "perfumar" in lower or "aura" in lower:
            in_section = "pisos"
            clean_l = re.sub(r'^PISOS\s*:?\s*', '', line).strip()
            if clean_l: pisos_notes.append(clean_l)
            continue
        elif any(k in lower for k in ["recepcion", "administracion", "page ", "hora sala evento"]):
            in_section = None
            continue

        # Clasificación por contenido
        if any(w in lower for w in ["tiene que estar montado", "a partir de las", "antes del evento"]):
            timing_notes.append(line)

        if any(w in lower for w in ["formato workshop", "mesas de cóctel", "mesa imperial", "tablero", "hospitality desk", "u-shape", "forma u"]):
            if line not in montaje_notes:
                montaje_notes.append(line)

        # Si estamos dentro de una sección activa
        if in_section == "sstt" and len(sstt_notes) < 8:
            if line not in sstt_notes: sstt_notes.append(line)
        elif in_section == "montaje" and len(montaje_notes) < 8:
            if line not in montaje_notes: montaje_notes.append(line)
        elif in_section == "fb" and len(fb_notes) < 8:
            if line not in fb_notes: fb_notes.append(line)
        elif in_section == "pisos" and len(pisos_notes) < 4:
            if line not in pisos_notes: pisos_notes.append(line)

    # Detectar cantidades explícitas de mobiliario mencionadas en el texto
    # Ej: "17 mesas formato workshop", "5 mesas de cóctel", "mesa imperial para 18 pax", "tablero con dos sillas"
    m_workshop = re.search(r'(\d+)\s*mesas?\s*(?:formato\s+)?workshop', text, re.I)
    if m_workshop:
        explicit_furniture["workshop_tables"] = int(m_workshop.group(1))

    m_coctel_tab = re.search(r'(\d+)\s*mesas?\s*de\s*c[oó]ctel', text, re.I)
    if m_coctel_tab:
        explicit_furniture["coctel_tables"] = int(m_coctel_tab.group(1))

    m_tableros = re.search(r'(\d+)\s*tableros?', text, re.I)
    if m_tableros:
        explicit_furniture["tableros"] = int(m_tableros.group(1))

    return {
        "montaje_notes": "\n".join(montaje_notes[:6]) if montaje_notes else None,
        "sstt_notes": "\n".join(sstt_notes[:6]) if sstt_notes else None,
        "fb_notes": "\n".join(fb_notes[:6]) if fb_notes else None,
        "pisos_notes": "\n".join(pisos_notes[:4]) if pisos_notes else None,
        "timing_notes": "\n".join(timing_notes[:3]) if timing_notes else None,
        "explicit_furniture": explicit_furniture
    }

def calculate_operational_setup(space: Optional[Dict[str, Any]], setup: Dict[str, Any], pax: int, notes: Dict[str, Any]) -> Dict[str, Any]:
    """Calcula las necesidades operativas sin inventar datos genéricos absurdos."""
    setup_key = setup.get("key", "estandar")
    space_id = space.get("id", "") if space else ""
    explicit_furn = notes.get("explicit_furniture", {})
    
    mesas_rectangulares = 0
    mesas_redondas = 0
    mesas_altas = 0
    sillas = pax
    furniture_summary = ""

    # 1. Si el PDF especifica explícitamente mobiliario (workshop, cóctel, tableros)
    if "workshop_tables" in explicit_furn:
        furniture_summary = f"{explicit_furn['workshop_tables']} mesas formato workshop (según BEO)"
    elif "coctel_tables" in explicit_furn:
        mesas_altas = explicit_furn["coctel_tables"]
        furniture_summary = f"{mesas_altas} mesas altas de cóctel vestidas con servilleteros"
    elif setup_key == "forma_u":
        sillas = pax
        furniture_summary = f"Montaje en U (U-Shape) para {pax} pax mirando a pantalla/atril"
    elif setup_key == "imperial":
        sillas = pax
        furniture_summary = f"Mesa imperial única para {pax} pax"
    elif setup_key == "coctel":
        mesas_altas = max(4, math.ceil(pax / 10))
        furniture_summary = f"{mesas_altas} mesas altas de cóctel de apoyo"
    elif setup_key == "banquete":
        mesas_redondas = math.ceil(pax / 8)
        furniture_summary = f"{mesas_redondas} mesas redondas de banquete (8-10 pax)"
    elif setup_key == "teatro":
        sillas = pax
        furniture_summary = f"{sillas} sillas en filas orientadas al frente (auditorio)"
    elif setup_key == "escuela":
        mesas_rectangulares = math.ceil(pax / 2)
        furniture_summary = f"{mesas_rectangulares} mesas de escuela con 2 sillas por mesa"
    else:
        furniture_summary = f"Distribución oficial según BEO para {pax} pax"

    # Tiempos de montaje
    if pax <= 15:
        setup_min = 25
        breakdown_min = 15
    elif pax <= 40:
        setup_min = 45
        breakdown_min = 25
    else:
        setup_min = 75
        breakdown_min = 40

    warning_aforo = None
    if space and "max_capacities" in space:
        max_cap = space["max_capacities"].get(setup_key)
        if max_cap and pax > max_cap:
            warning_aforo = f"⚠️ Advertencia de aforo: {pax} pax supera la capacidad recomendada ({max_cap} pax) en {space.get('name')}."

    return {
        "furniture": {
            "mesas_rectangulares": mesas_rectangulares,
            "mesas_redondas": mesas_redondas,
            "mesas_altas": mesas_altas,
            "sillas": sillas
        },
        "furniture_summary": furniture_summary,
        "times": {
            "setup_minutes": setup_min,
            "breakdown_minutes": breakdown_min
        },
        "warning_aforo": warning_aforo
    }

def parse_multi_session_opera(raw_text: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parsea órdenes completas de Opera Sales & Catering extrayendo sesiones múltiples
    y el desglose operativo completo para cada evento.
    """
    events = []
    
    # 1. Metadatos generales del BEO
    client_match = re.search(r'Cuenta\s+([A-Za-z0-9_\-\.\s&]{3,50})(?=\s*Block ID|\s*Nombre|\s*Direcci|\n)', raw_text)
    if client_match:
        client_name = client_match.group(1).replace("_", " ").strip().title()
    else:
        block_match = re.search(r'Block Name:\s*([^\n\r]+)', raw_text)
        if block_match:
            clean_bn = re.sub(r'^\d+\s*[-_]\s*', '', block_match.group(1).strip())
            client_name = clean_bn.replace("_", " ").strip().title()
        elif filename:
            clean_fn = re.sub(r'^(?:V\.\d+\s+)?(?:OS\s+)?', '', filename, flags=re.IGNORECASE)
            clean_fn = re.sub(r'\.(pdf|png|jpg|jpeg)$', '', clean_fn, flags=re.IGNORECASE)
            client_name = clean_fn.replace("_", " ").title()
        else:
            client_name = "ME Evento"

    cat_mgr_match = re.search(r'Catering Manager:\s*([^\n\r]+)', raw_text)
    catering_manager = cat_mgr_match.group(1).strip() if cat_mgr_match else None

    sales_mgr_match = re.search(r'Sales Manager:\s*([^\n\r]+)', raw_text)
    sales_manager = sales_mgr_match.group(1).strip() if sales_mgr_match else None

    block_id_match = re.search(r'Block ID:\s*([0-9]+)', raw_text)
    block_id = block_id_match.group(1).strip() if block_id_match else None

    pm_match = re.search(r'PM:\s*([0-9]+)', raw_text)
    pm = pm_match.group(1).strip() if pm_match else None

    # Notas globales del documento completo como respaldo
    doc_global_notes = extract_section_notes(raw_text)

    # 2. Partir por páginas
    pages = raw_text.split("--- Page ")
    current_date = date.today().isoformat()

    for page in pages:
        if not page.strip():
            continue
            
        # Detectar fecha de cabecera de página (ej: Domingo, 20/09/26 o Martes, 21/04/26)
        date_match = re.search(r'(?:Lunes|Martes|Mi[ée]rcoles|Jueves|Viernes|S[aá]bado|Domingo),\s*(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4})', page, re.IGNORECASE)
        if date_match:
            current_date = normalize_date_string(date_match.group(1))

        # Extraer notas operativas de esta página
        page_notes = extract_section_notes(page)

        # Buscar filas de tabla Opera con variantes amplias de formato
        opera_table_pattern = r'(\d{1,2}[:.]\d{2}\s*(?:-|a)\s*\d{1,2}[:.]\d{2})\s+([A-Za-z0-9\+\s]+?)\s+([A-Za-z0-9\s]+?)\s+(Forma\s+U|U-Shape|U\s+Shape|Escuela|Teatro|Imperial|Banquete|C[oó]ctel|Cocktail|Reuni[oó]n|Almuerzo|Cena)\s+(\d+)\s*Pax'
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
                
                # Si en las notas de montaje de la página se especifica otro montaje más preciso
                page_lower = page.lower()
                if "montaje en u-shape" in page_lower or "montaje en u" in page_lower or "forma u" in page_lower:
                    matched_setup = match_setup("forma u")
                elif "formato workshop" in page_lower:
                    matched_setup = match_setup("workshop")
                else:
                    matched_setup = match_setup(setup_str)

                services = match_services(page)
                operational = calculate_operational_setup(matched_space, matched_setup, pax_val, page_notes)
                
                # Adjuntar notas completas (específicas de página o globales del documento)
                operational["montaje_notes"] = page_notes["montaje_notes"] or doc_global_notes["montaje_notes"]
                operational["sstt_notes"] = page_notes["sstt_notes"] or doc_global_notes["sstt_notes"]
                operational["fb_notes"] = page_notes["fb_notes"] or doc_global_notes["fb_notes"]
                operational["pisos_notes"] = page_notes["pisos_notes"] or doc_global_notes["pisos_notes"]
                operational["timing_notes"] = page_notes["timing_notes"] or doc_global_notes["timing_notes"]

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
                    "manager": catering_manager or sales_manager or "Marta Delange",
                    "block_id": block_id,
                    "pm": pm,
                    "raw_snippet": page[:250].replace('\n', ' ')
                })
        else:
            # Caso 2: Orden con montaje narrativo (ej: Caterpillar, eventos sin tabla)
            if "montaje" in page.lower() and ("pax" in page.lower() or "personas" in page.lower()):
                single_evt = parse_single_session_narrative(page, current_date, client_name, filename)
                single_evt["manager"] = catering_manager or sales_manager or "Marta Delange"
                single_evt["block_id"] = block_id
                single_evt["pm"] = pm
                # Evitar duplicados del mismo día y salón
                if not any(e["date"] == single_evt["date"] and e["space"]["id"] == single_evt["space"]["id"] for e in events):
                    events.append(single_evt)

    # Si no se detectó ninguna sesión en las páginas, fallback estructurado
    if not events:
        events.append(parse_event_order(raw_text, filename=filename))

    return events

def parse_single_session_narrative(raw_text: str, current_date: str, client_name: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """Parsea una sesión descrita en texto narrativo (sin tabla Opera)."""
    space = match_space(raw_text) or {
        "id": "terraza-pool-bar",
        "name": "Terraza Pool Bar / Rooftop",
        "color_tag": "#e76f51",
        "location": "Rooftop / Terraza Panorámica"
    }
    setup = match_setup(raw_text)
    services = match_services(raw_text)
    pax = extract_pax(raw_text)
    times = extract_times(raw_text)
    notes = extract_section_notes(raw_text)
    operational = calculate_operational_setup(space, setup, pax, notes)
    operational["montaje_notes"] = notes["montaje_notes"]
    operational["sstt_notes"] = notes["sstt_notes"]
    operational["fb_notes"] = notes["fb_notes"]
    operational["pisos_notes"] = notes["pisos_notes"]
    operational["timing_notes"] = notes["timing_notes"]

    return {
        "id": f"evt-{int(datetime.now().timestamp() * 1000)}",
        "title": client_name,
        "date": current_date,
        "time_start": times["start"],
        "time_end": times["end"],
        "space": space,
        "setup": setup,
        "pax": pax,
        "services": services,
        "operational": operational,
        "raw_snippet": raw_text[:250].replace('\n', ' ')
    }

def parse_event_order(raw_text: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """Fallback para una orden de servicio general."""
    space = match_space(raw_text) or {
        "id": "multifuncional",
        "name": "Sala Multifuncional",
        "color_tag": "#7b2cbf",
        "location": "Planta Baja"
    }
    setup = match_setup(raw_text)
    services = match_services(raw_text)
    pax = extract_pax(raw_text)
    times = extract_times(raw_text)
    event_date = extract_date(raw_text)
    notes = extract_section_notes(raw_text)
    
    event_name = "ME Evento"
    client_match = re.search(r'Cuenta\s+([A-Za-z0-9_\-\.\s&]{3,50})', raw_text)
    if client_match:
        event_name = client_match.group(1).replace("_", " ").strip().title()
    elif filename:
        clean_fn = re.sub(r'^(?:V\.\d+\s+)?(?:OS\s+)?', '', filename, flags=re.IGNORECASE)
        clean_fn = re.sub(r'\.(pdf|png|jpg|jpeg)$', '', clean_fn, flags=re.IGNORECASE)
        event_name = clean_fn.replace("_", " ").title()

    operational = calculate_operational_setup(space, setup, pax, notes)
    operational["montaje_notes"] = notes["montaje_notes"]
    operational["sstt_notes"] = notes["sstt_notes"]
    operational["fb_notes"] = notes["fb_notes"]
    operational["pisos_notes"] = notes["pisos_notes"]
    operational["timing_notes"] = notes["timing_notes"]
    
    cat_match = re.search(r'Catering Manager:\s*([^\n\r]+)', raw_text)
    manager = cat_match.group(1).strip() if cat_match else "Marta Delange"

    return {
        "id": f"evt-{int(datetime.now().timestamp() * 1000)}",
        "title": event_name,
        "date": event_date,
        "time_start": times["start"],
        "time_end": times["end"],
        "space": space,
        "setup": setup,
        "pax": pax,
        "services": services,
        "operational": operational,
        "manager": manager,
        "raw_snippet": raw_text[:250].replace('\n', ' ')
    }
