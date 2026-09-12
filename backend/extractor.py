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

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extrae texto plano de un documento PDF en memoria usando pypdf o pdfplumber."""
    extracted = ""
    # Intento 1: pypdf (rápido y ligero)
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            t = page.extract_text()
            if t:
                extracted += t + "\n"
    except Exception as e:
        print(f"pypdf extraction error: {e}")

    # Intento 2: pdfplumber si no sacó suficiente texto
    if len(extracted.strip()) < 30:
        try:
            import io
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        extracted += t + "\n"
        except Exception as e:
            print(f"pdfplumber extraction error: {e}")

    return extracted.strip()

def match_space(text: str) -> Optional[Dict[str, Any]]:
    """Identifica el salón oficial de ME Málaga mediante los alias configurados."""
    text_lower = text.lower()
    spaces = SPACES_CONFIG.get("spaces", [])
    
    # Ordenar por longitud de alias descendente para evitar falsos positivos
    for space in spaces:
        for alias in sorted(space.get("aliases", []), key=len, reverse=True):
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text_lower):
                return space
    return None

def match_setup(text: str) -> Dict[str, Any]:
    """Identifica el tipo de montaje según el diccionario de jerga."""
    text_lower = text.lower()
    montajes = JARGON_CONFIG.get("montajes", [])
    
    for m in montajes:
        for alias in sorted(m.get("aliases", []), key=len, reverse=True):
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text_lower):
                return m
                
    # Default si no se detecta
    return {
        "key": "estandar",
        "label": "Montaje Estándar",
        "icon": "📋",
        "description": "Distribución a confirmar según orden de servicio"
    }

def match_services(text: str) -> List[Dict[str, Any]]:
    """Detecta servicios de F&B y equipamiento especial (CB, AV, mic, etc.)."""
    text_lower = text.lower()
    services_found = []
    
    # F&B
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
                
    # Equipamiento
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
    # Buscar patrones como: "12 pax", "45 personas", "PAX: 30", "asistentes: 20", "12 comensales"
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
                
    # Búsqueda general de números de 1 o 2 dígitos acompañados de contexto
    num_match = re.search(r'\b([1-9]\d{0,2})\s*(?:pax|px)\b', text, re.IGNORECASE)
    if num_match:
        return int(num_match.group(1))
        
    return 15 # Valor representativo si no viene especificado

def extract_times(text: str) -> Dict[str, str]:
    """Extrae horario de inicio y fin del evento."""
    # Buscar rangos como 09:00 - 14:00 o 10:00 a 18:00
    range_match = re.search(r'(\d{1,2}[:.]\d{2})\s*(?:-|a|hasta)\s*(\d{1,2}[:.]\d{2})', text)
    if range_match:
        start = range_match.group(1).replace(".", ":").zfill(5)
        end = range_match.group(2).replace(".", ":").zfill(5)
        return {"start": start, "end": end}
        
    # Buscar solo una hora de inicio
    single_match = re.search(r'\b(?:a\s+las|hora:?|inicio:?)\s*(\d{1,2}[:.]\d{2})\b', text, re.IGNORECASE)
    if single_match:
        start = single_match.group(1).replace(".", ":").zfill(5)
        return {"start": start, "end": "--:--"}
        
    return {"start": "09:00", "end": "14:00"}

def extract_date(text: str) -> str:
    """Extrae la fecha en formato YYYY-MM-DD."""
    # Formato DD/MM/YYYY o DD-MM-YYYY
    match_dmy = re.search(r'\b(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{4})\b', text)
    if match_dmy:
        d, m, y = match_dmy.groups()
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
        
    # Formato DD de [Mes] de YYYY
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
            
    # Default: hoy
    return date.today().isoformat()

def calculate_operational_setup(space: Optional[Dict[str, Any]], setup: Dict[str, Any], pax: int) -> Dict[str, Any]:
    """Calcula las necesidades exactas de mobiliario, tiempos de montaje y valida aforo."""
    setup_key = setup.get("key", "estandar")
    
    # 1. Cálculo de mobiliario
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
        sillas = math.ceil(pax / 15) # Taburetes
    elif setup_key == "teatro":
        mesas_rectangulares = 0
        sillas = pax + 2 # Reserva cortesía
    elif setup_key == "imperial":
        mesas_rectangulares = math.ceil(pax / 2)
        sillas = pax
    elif setup_key == "cabaret":
        mesas_redondas = math.ceil(pax / 5)
        sillas = pax
    else:
        mesas_rectangulares = math.ceil(pax / 2)
        sillas = pax

    # 2. Estimación de tiempos operativos
    if pax <= 15:
        tiempo_montaje_min = 25
        tiempo_desmontaje_min = 15
    elif pax <= 40:
        tiempo_montaje_min = 45
        tiempo_desmontaje_min = 25
    else:
        tiempo_montaje_min = 75
        tiempo_desmontaje_min = 40

    # 3. Validación de aforo del salón
    warning_aforo = None
    if space and "max_capacities" in space:
        max_cap = space["max_capacities"].get(setup_key)
        if max_cap and pax > max_cap:
            warning_aforo = f"⚠️ Aforo excedido: {pax} pax solicitados vs capacidad máxima de {max_cap} pax para montaje {setup.get('label')} en {space.get('name')}."

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

def parse_event_order(raw_text: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """Función principal que procesa el texto en bruto y genera la ficha del evento."""
    space = match_space(raw_text)
    setup = match_setup(raw_text)
    services = match_services(raw_text)
    pax = extract_pax(raw_text)
    times = extract_times(raw_text)
    event_date = extract_date(raw_text)
    
    # Nombre del evento estimado
    event_name = "Orden de Servicio"
    first_lines = [l.strip() for l in raw_text.splitlines() if l.strip()][:3]
    if first_lines:
        for line in first_lines:
            if len(line) > 5 and not any(k in line.lower() for k in ["beo", "orden de servicio", "fecha", "página"]):
                event_name = line[:60]
                break
                
    if event_name == "Orden de Servicio" and filename:
        clean_fn = re.sub(r'\.(pdf|png|jpg|jpeg)$', '', filename, flags=re.IGNORECASE)
        event_name = clean_fn.replace("_", " ").replace("-", " ").title()

    operational = calculate_operational_setup(space, setup, pax)
    
    return {
        "id": f"evt-{int(datetime.now().timestamp() * 1000)}",
        "title": event_name,
        "date": event_date,
        "time_start": times["start"],
        "time_end": times["end"],
        "space": space if space else {
            "id": "multifuncional",
            "name": "Sala Multifuncional (Sugerida)",
            "color_tag": "#7b2cbf",
            "location": "Planta Baja"
        },
        "setup": setup,
        "pax": pax,
        "services": services,
        "operational": operational,
        "raw_snippet": raw_text[:200]
    }
