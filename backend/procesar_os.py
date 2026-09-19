"""
Procesa órdenes de servicio (PDF) sin levantar el servidor: extrae, sustituye la versión anterior del
grupo y actualiza data/events.json + frontend/data/events.json. Lo usa la GitHub Action (carpeta inbox/),
pero también sirve en local o en Termux.

    python -m backend.procesar_os                    -> SIMULA lo que haya en inbox/
    python -m backend.procesar_os ruta/orden.pdf     -> SIMULA ese PDF
    python -m backend.procesar_os --aplicar          -> escribe (y copia los PDF a data/beos)
    python -m backend.procesar_os --aplicar --consumir   -> además borra de inbox/ los PDF ya procesados

Sale con código 1 si algún PDF falla (sin texto o sin eventos): un resultado vacío es un fallo, no un dato.
"""
import argparse
import shutil
import sys
from pathlib import Path

from backend.extractor import extract_text_from_pdf, parse_multi_session_opera
from backend.store import (
    ROOT_DIR, BEOS_DIR, FRONTEND_BEOS_DIR, get_stored_events, save_stored_events, merge_events,
)

INBOX_DIR = ROOT_DIR / "inbox"


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
    ap.add_argument("--aplicar", action="store_true", help="escribir los cambios (por defecto solo simula)")
    ap.add_argument("--consumir", action="store_true", help="borrar de inbox/ los PDF procesados con éxito")
    args = ap.parse_args()

    pdfs = [Path(p) for p in args.pdfs] if args.pdfs else sorted(INBOX_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No hay ningún PDF que procesar (busqué en {INBOX_DIR}).")
        return 0

    eventos = get_stored_events()
    print(f"Eventos guardados ahora: {len(eventos)} | PDF a procesar: {len(pdfs)}")
    fallos = 0
    procesados = []

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

    print(f"\nEventos tras procesar: {len(eventos)}")
    if not args.aplicar:
        print("MODO: SIMULACIÓN (no se ha escrito nada). Usa --aplicar para guardar.")
        return 1 if fallos else 0

    if procesados:
        save_stored_events(eventos)
        for pdf in procesados:
            for destino in (BEOS_DIR, FRONTEND_BEOS_DIR):
                if pdf.resolve().parent != destino.resolve():
                    shutil.copy2(pdf, destino / pdf.name)
            if args.consumir and pdf.resolve().parent == INBOX_DIR.resolve():
                pdf.unlink()
        print(f"MODO: APLICAR -> escrito. PDF copiados a data/beos: {len(procesados)}")
    if fallos:
        print(f"ATENCIÓN: {fallos} PDF han fallado y NO se han procesado.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
