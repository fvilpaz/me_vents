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
    
    # Lista plana de (alias, space), ordenada por longitud de alias DESCENDENTE
    # De este modo, combinados largos (ej: 'estudio 2 + 3', 'pérgola terraza')
    # SIEMPRE se evalúan antes que componentes cortos ('estudio 2', 'terraza')
    all_alias_pairs = []
    for space in spaces:
        for alias in space.get("aliases", []):
            all_alias_pairs.append((alias.lower().strip(), space))
            
    all_alias_pairs.sort(key=lambda x: len(x[0]), reverse=True)
    
    for alias, space in all_alias_pairs:
        pattern = r'(?<![a-záéíóúñ0-9])' + re.escape(alias) + r'(?![a-záéíóúñ0-9])'
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

def unwrap_opera_table_lines(text: str) -> str:
    """Desenvuelve filas de tabla Opera rotas por columnas estrechas (ej: Multifuntional Meeting \\n Room \\n Cóctel 5 Pax)."""
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r'^\s*\d{1,2}[:.]\d{2}\s*(?:-|a)\s*\d{1,2}[:.]\d{2}', line) and 'pax' not in line.lower():
            combined = line.strip()
            j = i + 1
            while j < len(lines) and j <= i + 3:
                next_l = lines[j].strip()
                if re.match(r'^\s*\d{1,2}[:.]\d{2}\s*(?:-|a)\s*\d{1,2}[:.]\d{2}', next_l):
                    break
                combined += " " + next_l
                if 'pax' in next_l.lower():
                    j += 1
                    break
                j += 1
            out.append(combined)
            i = j
        else:
            out.append(line)
            i += 1
    return "\n".join(out)

def parse_multi_session_opera(raw_text: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parsea órdenes completas de Opera Sales & Catering extrayendo sesiones múltiples
    y el desglose operativo completo para cada evento.
    Soporta eventos multi-día y conserva el menú gastronómico íntegro.
    """
    # 1. Metadatos generales del BEO
    client_name = "Evento MICE"
    client_match = re.search(r'Cuenta\s+([^\n\r]+?)(?=\s*Block ID|\s*Nombre|\s*Direcci|\n)', raw_text)
    if client_match:
        client_name = client_match.group(1).strip()
        client_name = re.sub(r'\s+(?:SL|SA|S\.L\.|S\.A\.|LTD|INC|GMBH)\b', '', client_name, flags=re.I).strip().title()
    else:
        block_match = re.search(r'Block Name:\s*([^\n\r]+)', raw_text)
        if block_match:
            clean_bn = re.sub(r'^\d+\s*[-_]\s*', '', block_match.group(1).strip())
            clean_bn = re.sub(r'\s*\d{1,2}\s*[-–]\s*\d{1,2}[_/\.-]\d{2}[_/\.-]\d{2,4}', '', clean_bn).strip()
            client_name = clean_bn.replace("_", " ").strip().title()
        elif filename:
            clean_fn = re.sub(r'^(?:V\.\d+\s+)?(?:OS\s+)?', '', filename, flags=re.IGNORECASE)
            clean_fn = re.sub(r'\.(pdf|png|jpg|jpeg)$', '', clean_fn, flags=re.IGNORECASE)
            clean_fn = re.sub(r'\s*\d{1,2}\s*[-–_]\s*\d{1,2}[_/\.-]\d{2}[_/\.-]\d{2,4}', '', clean_fn).strip()
            client_name = clean_fn.replace("_", " ").strip().title()

    cat_mgr_match = re.search(r'Catering Manager:\s*([^\n\r]+)', raw_text)
    catering_manager = cat_mgr_match.group(1).strip() if cat_mgr_match else "Default Owner SPAIN"

    sales_mgr_match = re.search(r'Sales Manager:\s*([^\n\r]+)', raw_text)
    sales_manager = sales_mgr_match.group(1).strip() if sales_mgr_match else "Default Owner SPAIN"

    block_id_match = re.search(r'Block ID:\s*([0-9]+)', raw_text)
    block_id = block_id_match.group(1).strip() if block_id_match else None

    pm_match = re.search(r'PM:\s*([0-9]+)', raw_text)
    pm = pm_match.group(1).strip() if pm_match else None

    total_habs_match = re.search(r'Total Habs\s*([0-9]+)', raw_text)
    total_habs = total_habs_match.group(1).strip() if total_habs_match else None

    # Pre-procesado de líneas rotas
    unwrapped_text = unwrap_opera_table_lines(raw_text)

    # 2. Agrupación por días de calendario
    day_regex = r'(?:Lunes|Martes|Mi[ée]rcoles|Jueves|Viernes|S[aá]bado|Domingo),\s*(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4})'
    day_matches = list(re.finditer(day_regex, unwrapped_text, re.I))

    if not day_matches:
        # Fallback a split por páginas o narrativa
        return [parse_event_order(raw_text, filename=filename)]

    days_blocks = {}
    for i in range(len(day_matches)):
        start = day_matches[i].start()
        end = day_matches[i+1].start() if i + 1 < len(day_matches) else len(unwrapped_text)
        d_key = day_matches[i].group(1)
        d_header = day_matches[i].group(0)
        if d_key not in days_blocks:
            days_blocks[d_key] = {"header": d_header, "pages": []}
        days_blocks[d_key]["pages"].append(unwrapped_text[start:end])

    # Ordenar cronológicamente
    def parse_d_key(k):
        parts = re.split(r'[\/\.-]', k)
        y = int("20" + parts[2]) if len(parts[2]) == 2 else int(parts[2])
        m = int(parts[1])
        d = int(parts[0])
        return (y, m, d)

    sorted_day_keys = sorted(days_blocks.keys(), key=parse_d_key)
    all_dates_iso = []
    for k in sorted_day_keys:
        p = re.split(r'[\/\.-]', k)
        y = f"20{p[2]}" if len(p[2]) == 2 else p[2]
        all_dates_iso.append(f"{y}-{p[1].zfill(2)}-{p[0].zfill(2)}")

    min_date = all_dates_iso[0] if all_dates_iso else "2026-09-18"
    max_date = all_dates_iso[-1] if all_dates_iso else "2026-09-25"
    total_event_days = len(sorted_day_keys)

    events = []

    for day_idx, d_key in enumerate(sorted_day_keys):
        d_info = days_blocks[d_key]
        d_val = all_dates_iso[day_idx]
        combined_day_text = "\n".join(d_info["pages"])

        multi_day_info = {
            "is_multi_day": total_event_days > 1,
            "group_name": client_name,
            "date_start": min_date,
            "date_end": max_date,
            "day_index": day_idx + 1,
            "total_days": total_event_days,
            "day_label": f"Día {day_idx + 1} de {total_event_days}"
        }

        # Extraer bloques individuales de menús y gastronomía del día
        day_menu_blocks = []
        menu_splits = re.split(r'(?:Servicio Comida|Servicio Bebida)', combined_day_text, flags=re.I)
        for ms in menu_splits[1:]:
            clean_lines = []
            for l in ms.split("\n"):
                l_s = l.strip()
                if l_s and not any(k in l_s for k in ["ME Malaga", "C. Victoria", "Distrito Centro", "Cuenta", "Block ID", "Total Habs", "Viernes,", "Sábado,", "Domingo,", "Lunes,", "Martes,", "Miércoles,", "Jueves,", "Date Last", "Page ", "Teléfono:", "Email:", "PM:"]):
                    clean_lines.append(l_s)
            clean_text = "\n".join(clean_lines)
            raw_blocks = re.split(r'(?=\b\d{1,2}[:.]\d{2}\s*(?:-|a)\s*\d{1,2}[:.]\d{2})', clean_text)
            for b in raw_blocks:
                b_s = b.strip()
                if not b_s:
                    continue
                b_lines = [l for l in b_s.split("\n") if l.strip()]
                header = b_lines[0]
                sp = match_space(header)
                pax_m = re.search(r'(\d+)\s*Pax', header, re.I)
                pax_num = int(pax_m.group(1)) if pax_m else None
                day_menu_blocks.append({
                    "header": header,
                    "space": sp,
                    "pax": pax_num,
                    "text": "\n".join(b_lines[:25])
                })

        # Separar partes operativas
        ops_texts = []
        for p_txt in d_info["pages"]:
            ops_texts.append(re.split(r'(?:Servicio Comida|Servicio Bebida)', p_txt, flags=re.I)[0])
        combined_ops_text = "\n".join(ops_texts)

        session_line_regex = r'(?:^|\n)\s*(\d{1,2}[:.]\d{2}\s*(?:-|a)\s*\d{1,2}[:.]\d{2})\s+([^\n]+?\b\d+\s*Pax[^\n]*)'
        raw_session_matches = list(re.finditer(session_line_regex, combined_ops_text, re.I))
        session_matches = []
        for sm in raw_session_matches:
            rest = sm.group(2).strip()
            # En Opera los servicios F&B tienen el formato '- Item -' o empiezan por '-'
            starts_with_dash = rest.startswith('-')
            has_dash_service = bool(re.search(r'\s-\s', rest))
            is_food = starts_with_dash or (has_dash_service and any(k in rest.lower() for k in ['lunch', 'almuerzo', 'buffet', 'coffee', 'non stop', 'finger', 'desayuno', 'breakfast', 'cena', 'dinner', 'pausa', 'simple', 'premium', 'healthy']))
            if is_food:
                continue
            session_matches.append(sm)

        # Caso Llegadas / Alojamiento (ej: grupo en hotel sin sala el primer día)
        if not session_matches:
            if "INFO GENERAL" in combined_day_text or "RECEPCI" in combined_day_text or "habitaciones" in combined_day_text.lower():
                ig_match = re.search(r'(?:INFO GENERAL|RECEPCI[OÓ]N)(.*?)(?=(?:AURA|PISOS|SSTT|F&B|Servicio|Page|\Z))', combined_day_text, re.I | re.DOTALL)
                info_text = ""
                if ig_match:
                    info_lines = [l.strip() for l in ig_match.group(1).split("\n") if l.strip() and not any(k in l for k in ["ME Malaga", "Page ", "Total Habs", "C. Victoria"])]
                    info_text = "\n".join(info_lines[:12])

                events.append({
                    "id": f"evt-{len(events)+1}",
                    "title": f"{client_name} · Llegadas & Alojamiento",
                    "date": d_val,
                    "time_start": "12:00",
                    "time_end": "20:00",
                    "space": {
                        "id": "foyer",
                        "name": "Recepción / AURA",
                        "color_tag": "#d4af37",
                        "location": "Planta Baja"
                    },
                    "setup": {
                        "key": "hospitality_desk",
                        "label": "Llegadas & Check-in",
                        "icon": "🏨",
                        "description": "Recepción escalonada del grupo y gestión de habitaciones"
                    },
                    "pax": int(total_habs) if total_habs else 20,
                    "multi_day": multi_day_info,
                    "operational": {
                        "furniture_summary": f"Llegada de grupo ({total_habs or 20} habs contratadas)",
                        "montaje_notes": info_text or "Llegadas escalonadas del grupo. Gestión de habitaciones Opera PMS.",
                        "sstt_notes": "Soporte de recepción y terminales Opera PMS",
                        "fb_notes": "Facturación y régimen según BEO",
                        "menu_notes": None,
                        "pisos_notes": "AURA / PISOS: Revisar habitaciones y atenciones VIP.",
                        "times": { "setup_minutes": 15, "breakdown_minutes": 0 }
                    },
                    "manager": catering_manager or sales_manager or "Default Owner SPAIN",
                    "block_id": block_id,
                    "pm": pm
                })
            continue

        # Procesar sesiones operativas con resolución GENÉRICA de espacios y montajes
        for s_idx, sm in enumerate(session_matches):
            time_str = sm.group(1).strip()
            rest_line = sm.group(2).strip()

            s_start = sm.start()
            s_end = session_matches[s_idx+1].start() if s_idx + 1 < len(session_matches) else len(combined_ops_text)
            session_block = combined_ops_text[s_start:s_end]

            times = time_str.split("-") if "-" in time_str else time_str.split("a")
            t_start = times[0].strip().replace(".", ":").zfill(5)
            t_end = times[1].strip().replace(".", ":").zfill(5) if len(times) > 1 else "18:00"

            pax_m = re.search(r'(\d+)\s*Pax', rest_line, re.I)
            pax_val = int(pax_m.group(1)) if pax_m else 15

            # Resolución dinámica del Salón según catálogo oficial de ME Málaga
            space_obj = match_space(rest_line) or match_space(session_block)
            if not space_obj:
                space_obj = { "id": "multifuncional", "name": "Sala Multifuncional", "color_tag": "#7b2cbf", "location": "Planta Baja" }

            # Resolución dinámica del Montaje según diccionario oficial de sala
            setup_obj = match_setup(rest_line) or match_setup(session_block)
            if not setup_obj:
                setup_obj = { "key": "reunion", "label": "Reunión MICE", "icon": "💼", "description": "Montaje de sala para reunión" }

            montaje_lines = []
            for l in session_block.split("\n"):
                l_s = l.strip()
                if any(k in l_s.lower() for k in ["u-shape", "forma u", "taburete", "tablero", "flip chart", "blocs de notas", "bolígra", "sofás de la pérgola", "montar para 5 personas", "mesas de cóctel"]):
                    if l_s not in montaje_lines and not re.search(r'^\d{1,2}:\d{2}', l_s):
                        montaje_lines.append(l_s)

            sstt_lines = []
            in_sstt = False
            for l in session_block.split("\n"):
                l_s = l.strip()
                if l_s.startswith("SSTT"):
                    in_sstt = True
                    clean = re.sub(r'^SSTT\s*:?\s*', '', l_s).strip()
                    if clean: sstt_lines.append(clean)
                elif in_sstt:
                    if any(l_s.startswith(k) for k in ["PISOS", "AURA", "Servicio", "F&B", "Facturación", "08:", "18:", "Hora Sala", "Page "]):
                        in_sstt = False
                    elif l_s and not any(k in l_s for k in ["ME Malaga", "Page ", "Total Habs", "Catering Manager", "Sales Manager"]):
                        sstt_lines.append(l_s)

            fb_lines = []
            for l in session_block.split("\n"):
                l_s = l.strip()
                if any(k in l_s.lower() for k in ["coffee break permanente", "almuerzo en cañitas", "reservar una mesa", "finger buffet", "welcome drink", "minutas", "alérgenos", "intolerancias", "a la carta", "facturación"]):
                    if l_s not in fb_lines and not re.search(r'^\d{1,2}:\d{2}\s*(?:-|a)\s*\d{1,2}:\d{2}', l_s):
                        fb_lines.append(l_s)

            pisos_lines = [l.strip() for l in session_block.split("\n") if any(k in l.lower() for k in ["perfumar la sala", "revisar y perfumar", "aura", "pisos"])]

            furniture_sum = f"Montaje oficial según BEO para {pax_val} pax"
            if "u-shape" in setup_obj["key"] or "forma_u" in setup_obj["key"]:
                furniture_sum = f"Montaje en U (U-Shape) para {pax_val} pax"
            elif "coctel" in setup_obj["key"]:
                furniture_sum = f"Formato Cóctel / Welcome Drink ({pax_val} pax)"
            elif "imperial" in setup_obj["key"]:
                furniture_sum = f"Mesa Imperial única ({pax_val} pax)"

            # Asignación de menús estrictamente aislada por salón y comensales
            session_menus = []
            for mb in day_menu_blocks:
                mb_sp = mb.get("space")
                mb_pax = mb.get("pax")
                
                # 1. Coincidencia directa de salón
                if mb_sp and space_obj and mb_sp.get("id") == space_obj.get("id"):
                    session_menus.append(mb["text"])
                # 2. Comedores y anexos gastronómicos (Foyer, Cañitas al Fresco, Restaurante, Pérgola)
                elif mb_sp and mb_sp.get("id") in ["foyer", "canitas-al-fresco", "restaurante", "pergola", "rooftop"]:
                    # Asignar a la sesión cuyos comensales coinciden (ej: 15 pax vs 5 pax)
                    if mb_pax and pax_val and abs(mb_pax - pax_val) <= 3:
                        session_menus.append(mb["text"])
                # 3. Si solo hay 1 sesión en todo el día, recibe los menús de la jornada
                elif len(session_matches) == 1:
                    session_menus.append(mb["text"])
                    
            session_menu_text = "\n\n".join([f"🍴 {m}" for m in session_menus]) if session_menus else None

            events.append({
                "id": f"evt-{len(events)+1}",
                "title": f"{client_name} · {space_obj['name']}",
                "date": d_val,
                "time_start": t_start,
                "time_end": t_end,
                "space": space_obj,
                "setup": setup_obj,
                "pax": pax_val,
                "multi_day": multi_day_info,
                "operational": {
                    "furniture_summary": furniture_sum,
                    "montaje_notes": "\n".join(montaje_lines) if montaje_lines else f"Montaje {setup_obj['label']} para {pax_val} pax según BEO",
                    "sstt_notes": "\n".join(sstt_lines) if sstt_lines else "AC, conectividad y soporte técnico de sala",
                    "fb_notes": "\n".join(fb_lines) if fb_lines else None,
                    "menu_notes": session_menu_text,
                    "pisos_notes": "\n".join(pisos_lines) if pisos_lines else "Revisar y perfumar sala (Protocolo AURA)",
                    "times": { "setup_minutes": 30, "breakdown_minutes": 20 }
                },
                "manager": catering_manager or sales_manager or "Default Owner SPAIN",
                "block_id": block_id,
                "pm": pm
            })

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
