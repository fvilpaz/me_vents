"""
Procesa órdenes de servicio (PDF) sin levantar el servidor: extrae, sustituye la versión anterior del
grupo y actualiza data/events.json + frontend/data/events.json. Lo usa la GitHub Action (carpeta inbox/),
pero también sirve en local o en Termux.

    python -m backend.procesar_os                    -> SIMULA lo que haya en inbox/
    python -m backend.procesar_os ruta/orden.pdf     -> SIMULA ese PDF
    python -m backend.procesar_os --aplicar          -> escribe (y copia los PDF a data/beos)
    python -m backend.procesar_os --aplicar --consumir   -> además borra de inbox/ los PDF ya procesados
    python -m backend.procesar_os --carpeta RUTA     -> SIMULA todos los PDF de esa carpeta, de V.1 a V.n
    python -m backend.procesar_os --limpiar-terminados   -> SIMULA retirar los grupos ya terminados

Al sustituir una versión o retirar un grupo, sus PDF se borran de data/beos solo si ya no los usa
ningún evento (y de la carpeta de origen solo con --consumir).

Sale con código 1 si algún PDF falla (sin texto o sin eventos): un resultado vacío es un fallo, no un dato.
"""
import argparse
import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

from backend.extractor import extract_text_from_pdf, parse_multi_session_opera
from backend.store import (
    ROOT_DIR, BEOS_DIR, FRONTEND_BEOS_DIR, get_stored_events, save_stored_events, merge_events,
)

INBOX_DIR = ROOT_DIR / "inbox"


def pdf_sort_key(pdf: Path):
    version_match = re.match(r"(?i)^V\.(\d+)", pdf.name)
    version = int(version_match.group(1)) if version_match else 0
    try:
        modified = pdf.stat().st_mtime
    except OSError:
        modified = 0.0
    return version, modified


def ahora_local() -> datetime:
    """Hora de Málaga sin zona (así se guardan las fechas). La Action corre en UTC."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Madrid")).replace(tzinfo=None)
    except Exception:
        return datetime.now()


def evento_terminado(evento: dict, ahora: datetime) -> bool:
    fecha = evento.get("date")
    hora = evento.get("time_end") or evento.get("time_start")
    if not fecha or not hora:
        return False
    try:
        fin = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
    except (TypeError, ValueError):
        return False
    inicio = evento.get("time_start")
    if inicio and evento.get("time_end") and evento["time_end"] < inicio:
        fin += timedelta(days=1)  # termina pasada la medianoche
    return fin < ahora


def clave_grupo(evento: dict) -> str:
    return evento.get("block_id") or evento.get("multi_day", {}).get("group_name") or evento.get("id")


def retirar_terminados(eventos: list, ahora: datetime):
    """Quita los grupos cuyos eventos han terminado TODOS; un grupo que sigue en marcha se queda entero."""
    grupos = {}
    for e in eventos:
        grupos.setdefault(clave_grupo(e), []).append(e)
    terminados = {k for k, g in grupos.items() if all(evento_terminado(e, ahora) for e in g)}
    quedan = [e for e in eventos if clave_grupo(e) not in terminados]
    retirados = [e for e in eventos if clave_grupo(e) in terminados]
    return quedan, retirados


def pdfs_en_uso(eventos: list) -> set:
    return {e.get("source_file") for e in eventos if e.get("source_file")}


def directorios_origen(pdfs: list) -> set:
    return {pdf.parent.resolve() for pdf in pdfs} | {BEOS_DIR.resolve(), FRONTEND_BEOS_DIR.resolve()}


def eliminar_pdfs(nombres: set, directorios: set) -> list:
    eliminados = []
    for nombre in nombres:
        if not nombre:
            continue
        for directorio in directorios:
            pdf = directorio / nombre
            if pdf.is_file():
                pdf.unlink()
                eliminados.append(str(pdf))
    return eliminados


def procesar(pdf: Path, eventos: list):
    """Devuelve (eventos_resultantes, resumen). Lanza ValueError si el PDF no produce datos."""
    filename = pdf.name
    contenido = pdf.read_bytes()
    texto = extract_text_from_pdf(contenido)
    if len(texto.strip()) < 30:
        raise ValueError(f"no se pudo extraer texto ({len(texto)} caracteres): ¿PDF escaneado o dañado?")

    nuevos = parse_multi_session_opera(texto, filename=filename)
    if not nuevos:
        raise ValueError("el extractor no ha encontrado ningún evento")

    resultado = merge_events(eventos, nuevos)
    antes = {e["id"]: e for e in eventos}
    ids_despues = {e["id"] for e in resultado}
    modificados = []
    for e in nuevos:
        if e["id"] in antes:
            campos = campos_distintos(antes[e["id"]], e)
            if campos:
                modificados.append((e, campos))
    resumen = {
        "chars": len(texto),
        "nuevos": nuevos,
        "quitados": [e for e in eventos if e["id"] not in ids_despues],
        "anadidos": [e for e in nuevos if e["id"] not in antes],
        "modificados": modificados,
    }
    return resultado, resumen


def campos_distintos(viejo: dict, nuevo: dict, prefijo: str = "") -> list:
    """Nombres de los campos cuyo valor cambia entre dos versiones del mismo evento (entra en 'operational')."""
    campos = []
    for k in sorted(set(viejo) | set(nuevo)):
        a, b = viejo.get(k), nuevo.get(k)
        if isinstance(a, dict) and isinstance(b, dict):
            campos += campos_distintos(a, b, f"{prefijo}{k}.")
        elif a != b:
            campos.append(f"{prefijo}{k}")
    return campos


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description="Procesa órdenes de servicio PDF (simula por defecto).")
    ap.add_argument("pdfs", nargs="*", help="PDF a procesar (por defecto, todos los de inbox/)")
    ap.add_argument("--carpeta", "--directorio", dest="carpeta", help="procesar los PDF de una carpeta")
    ap.add_argument("--aplicar", action="store_true", help="escribir los cambios (por defecto solo simula)")
    ap.add_argument("--consumir", action="store_true", help="borrar los PDF procesados de la carpeta de origen")
    ap.add_argument("--limpiar-terminados", action="store_true", help="retirar eventos vencidos y sus PDF")
    args = ap.parse_args()

    if args.pdfs:
        pdfs = [Path(p) for p in args.pdfs]
    elif args.carpeta:
        # Todos: el nombre no garantiza nada (muchas órdenes no llevan "OS"). Lo que no sea una orden sale como ERROR
        pdfs = sorted(Path(args.carpeta).glob("*.pdf"), key=pdf_sort_key)
    else:
        pdfs = sorted(INBOX_DIR.glob("*.pdf"), key=pdf_sort_key)
    if not pdfs:
        print(f"No hay ningún PDF que procesar (busqué en {args.carpeta or INBOX_DIR}).")
        if not args.limpiar_terminados:
            return 0

    eventos = get_stored_events()
    # Los PDF de data/beos se limpian siempre; los de la carpeta de origen, solo con --consumir
    directorios = directorios_origen(pdfs) if args.consumir else {BEOS_DIR.resolve(), FRONTEND_BEOS_DIR.resolve()}
    # Una versión nueva puede conservar los ids (sale como MODIFICA), así que se compara el uso antes/después
    pdfs_antes = pdfs_en_uso(eventos)
    print(f"Eventos guardados ahora: {len(eventos)} | PDF a procesar: {len(pdfs)}")
    fallos = 0
    procesados = []
    retirados = []

    for pdf in pdfs:
        print(f"\n=== {pdf.name} ===")
        try:
            eventos, r = procesar(pdf, eventos)
        except Exception as e:
            fallos += 1
            print(f"  ERROR: {e}")
            continue
        procesados.append(pdf)
        grupo = r["nuevos"][0].get("multi_day", {}).get("group_name")
        print(f"  texto: {r['chars']} caracteres | eventos extraídos: {len(r['nuevos'])} | grupo: {grupo}")
        for e in r["quitados"]:
            print(f"  - SUSTITUYE {e['date']} {e['time_start']} {e['space'].get('name')}  ({e['id']})")
        for e in r["anadidos"]:
            print(f"  + NUEVO     {e['date']} {e['time_start']} {e['space'].get('name')}  ({e['id']})")
        for e, campos in r["modificados"]:
            print(f"  ~ MODIFICA  {e['date']} {e['time_start']} {e['space'].get('name')}: {', '.join(campos)}")
        if not r["quitados"] and not r["anadidos"] and not r["modificados"]:
            print("  = sin cambios: ya estaba guardada exactamente esta versión")

    if args.limpiar_terminados:
        ahora = ahora_local()
        eventos, retirados = retirar_terminados(eventos, ahora)
        print(f"\n=== Grupos terminados antes de {ahora:%Y-%m-%d %H:%M} ===")
        for e in retirados:
            print(f"  - RETIRA    {e['date']} {e.get('time_end') or e.get('time_start')} {e.get('title')}  ({e['id']})")
        if not retirados:
            print("  = ninguno: todos los grupos guardados siguen en marcha")

    huerfanos = (pdfs_antes | {pdf.name for pdf in procesados}) - pdfs_en_uso(eventos)
    for nombre in sorted(huerfanos):
        print(f"  - PDF sin uso: {nombre}")

    print(f"\nEventos tras procesar: {len(eventos)}")
    if not args.aplicar:
        print("MODO: SIMULACIÓN (no se ha escrito nada). Usa --aplicar para guardar.")
        return 1 if fallos else 0

    if procesados or retirados:
        save_stored_events(eventos)
        for pdf in procesados:
            for destino in (BEOS_DIR, FRONTEND_BEOS_DIR):
                if pdf.resolve().parent != destino.resolve():
                    shutil.copy2(pdf, destino / pdf.name)
            if args.consumir and pdf.resolve().parent not in (BEOS_DIR.resolve(), FRONTEND_BEOS_DIR.resolve()):
                pdf.unlink()
        for ruta in eliminar_pdfs(huerfanos, directorios):
            print(f"  PDF borrado: {ruta}")
        print(f"MODO: APLICAR -> escrito. PDF copiados a data/beos: {len(procesados)} | eventos retirados: {len(retirados)}")
    if fallos:
        print(f"ATENCIÓN: {fallos} PDF han fallado y NO se han procesado.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
