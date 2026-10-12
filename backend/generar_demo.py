"""
Genera órdenes de servicio (PDF) FICTICIAS para la demostración: empresas inventadas, mismo formato que las
de Opera, siempre desde hoy hasta hoy+4 (5 días vista). Las deja en inbox/ y las procesa la misma Action
de siempre (backend/procesar_os.py), así la demo recorre el camino real: PDF -> extractor -> events.json.

    python -m backend.generar_demo                -> escribe los PDF de los próximos 5 días en inbox/
    python -m backend.generar_demo --salida RUTA  -> en otra carpeta
    python -m backend.generar_demo --hoy 2026-10-14   -> como si hoy fuese esa fecha (pruebas)

Es determinista: la misma fecha produce siempre el mismo PDF (nombre y contenido), así que repetirlo no duplica.
Ningún dato de esta carpeta es real: ni empresas, ni asistentes, ni precios, ni menús.
"""
import argparse
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from backend.procesar_os import ahora_local

INBOX_DIR = Path(__file__).resolve().parent.parent / "inbox"
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

EMPRESAS = [
    "Altamira Biotech", "Vértice Logística", "Norte Sur Seguros", "Lumen Studio", "Tramontana Capital",
    "Órbita Software", "Casa Jazmín Eventos", "Fundación Horizonte", "Bahía Azul Congresos", "Cobalto Energía",
    "Estrella Polar Viajes", "Mirador Farma", "Alameda Consultores", "Pinar Alto Editorial", "Delta Sur Motor",
    "Faro Nuevo Medios",
]
# (sala tal como la escribe Opera, montaje, aforo mínimo y máximo)
REUNION = [("ESTUDIO 2", "Escuela", 12, 18), ("ESTUDIO 3", "U-Shape", 10, 16), ("ESTUDIO 2 + 3", "Teatro", 25, 40),
           ("SALA MULTIFUNCIONAL", "Escuela", 30, 60)]
COMIDA = [("CAÑITAS AL FRESCO", "Banquete", 10, 40), ("TERRAZA POOL BAR", "Banquete", 8, 30)]
PLATOS = ["Ensalada templada de queso de cabra y frutos rojos", "Crema fría de melón con jamón", "Tosta de salmorejo y bonito",
          "Arroz meloso de verduras de temporada", "Merluza al horno con salsa verde", "Solomillo ibérico con puré de patata",
          "Presa a la brasa con verduras asadas", "Tarta de queso con mermelada de higos", "Helado de yogur con fruta fresca",
          "Croquetas caseras de puchero", "Gazpacho de tomate rosa", "Lubina a la plancha con verduras"]
NOTAS = ["Revisar el audiovisual una hora antes del inicio", "Uniformidad impecable y servicio de agua en sala",
         "Preparar blocs de notas y bolígrafos en cada puesto", "Cuidar la presentación del servicio",
         "Pendiente confirmar el número final de asistentes", "Colocar cartelería en la entrada de la sala"]


def _marca_de_agua() -> Image.Image:
    texto = Image.new("RGBA", (1500, 140), (0, 0, 0, 0))
    ImageDraw.Draw(texto).text((10, 10), "DEMO - DOCUMENTO FICTICIO", font=ImageFont.load_default(size=90), fill=(0, 0, 0, 30))
    return texto.rotate(35, expand=True)


MARCA = _marca_de_agua()


def hhmm(h: int, m: int = 0) -> str:
    return f"{h:02d}:{m:02d}"


def un_dia(fecha: date, rnd: random.Random, plantilla: str, pax: int) -> dict:
    """Un día de una orden: sesiones (fila de la tabla), notas y menús."""
    sesiones, comidas, fb = [], [], [rnd.choice(NOTAS)]
    if plantilla in ("reunion", "grupo"):
        sala, montaje, _, _ = rnd.choice(REUNION)
        sesiones.append((hhmm(9, 30), hhmm(13, 30), sala, "Meeting", montaje, pax, "COM"))
        comidas.append((f"11:00 a 11:30 - Coffee Break - {sala}", pax, ["Café, infusiones y zumos", "Bollería y fruta de temporada"]))
        if plantilla == "grupo":
            sesiones.append((hhmm(14, 0), hhmm(15, 30), "CAÑITAS AL FRESCO", "Lunch", "Banquete", pax, "COM"))
            comidas.append((f"14:00 a 15:30 - Lunch - CAÑITAS AL FRESCO", pax, rnd.sample(PLATOS, 4)))
        info = f"Reunión de empresa para {pax} personas con coffee break."
    elif plantilla == "almuerzo":
        sala, montaje, _, _ = rnd.choice(COMIDA)
        sesiones.append((hhmm(14, 0), hhmm(16, 0), sala, "Lunch", montaje, pax, "COM"))
        comidas.append((f"14:00 a 16:00 - Lunch - {sala}", pax, rnd.sample(PLATOS, 4)))
        info = f"Almuerzo de empresa para {pax} personas."
    elif plantilla == "cena":
        sala, montaje, _, _ = rnd.choice(COMIDA)
        sesiones.append((hhmm(21, 0), hhmm(23, 0), sala, "Dinner", montaje, pax, "COM"))
        comidas.append((f"21:00 a 23:00 - Dinner - {sala}", pax, rnd.sample(PLATOS, 5)))
        info = f"Cena de empresa para {pax} personas."
    else:  # coctel
        sesiones.append((hhmm(19, 30), hhmm(21, 0), "TERRAZA POOL BAR", "Cóctel", "Cóctel", pax, "COM"))
        comidas.append((f"19:30 a 21:00 - Cóctel - TERRAZA POOL BAR", pax, rnd.sample(PLATOS, 3)))
        info = f"Cóctel de bienvenida para {pax} personas."
    if rnd.random() < 0.5:
        fb += ["Alergias e intolerancias:", f"{rnd.randint(1, 2)}x intolerancia gluten", f"{rnd.randint(1, 2)}x intolerancia lactosa"]
    return {"fecha": fecha, "info": info, "sesiones": sesiones, "fb": fb, "comidas": comidas}


def ordenes_de_la_ventana(hoy: date, dias: int) -> list:
    """Todas las órdenes que tocan [hoy, hoy+dias-1]. Cada fecha lleva siempre las mismas, sea cual sea la noche."""
    ordenes = []
    fin = hoy + timedelta(days=dias - 1)
    for k in range(dias):
        d = hoy + timedelta(days=k)
        rnd = random.Random(d.toordinal())
        for i, plantilla in enumerate(rnd.sample(["reunion", "almuerzo", "cena", "coctel"], 3)):
            r = random.Random(f"{d.isoformat()}-{i}")
            empresa = r.choice(EMPRESAS)
            tipo = {"reunion": "REUNION", "almuerzo": "ALMUERZO", "cena": "CENA", "coctel": "COCTEL"}[plantilla]
            ordenes.append({
                "block_id": f"9{d:%y%m%d}{i}", "tipo_reserva": "Social" if plantilla in ("cena", "coctel") else "Corporate",
                "nombre": f"{tipo} {empresa.upper()} {d:%d_%m_%Y}", "archivo": f"OS {tipo} {empresa.upper()} {d:%d_%m_%Y}.pdf",
                "dias": [un_dia(d, r, plantilla, r.randint(8, 40))],
            })
    # Grupos de 3 días que arrancan cada tercer día del calendario; entran los que aún solapan con la ventana
    for k in range(-2, dias):
        s = hoy + timedelta(days=k)
        if s.toordinal() % 3 != 0 or s + timedelta(days=2) < hoy or s > fin:
            continue
        r = random.Random(f"grupo-{s.isoformat()}")
        empresa, pax = r.choice(EMPRESAS), r.randint(15, 45)
        dias_g = [un_dia(s + timedelta(days=n), r, "grupo", pax) for n in range(3)]
        ordenes.append({
            "block_id": f"9{s:%y%m%d}9", "tipo_reserva": "Corporate",
            "nombre": f"GRUPO {empresa.upper()} {s:%d}-{(s + timedelta(days=2)):%d_%m_%Y}",
            "archivo": f"OS GRUPO {empresa.upper()} {s:%d}-{(s + timedelta(days=2)):%d_%m_%Y}.pdf", "dias": dias_g,
        })
    return ordenes


def fila(c, y: float, celdas: list, fuente: str = "Helvetica", tam: int = 8) -> None:
    """Dibuja varias celdas a la misma altura dentro de UN objeto de texto: pypdf las une en una sola línea."""
    t = c.beginText()
    t.setFont(fuente, tam)
    for x, texto in celdas:
        t.setTextOrigin(x, y)
        t.textOut(texto)
    c.drawText(t)


def cabecera(c, orden: dict, dia: dict, pagina: int, total: int) -> float:
    w, h = A4
    # Marca de agua como IMAGEN (sin capa de texto): así el extractor no la lee y no se cuela en las notas
    mw, mh = MARCA.size
    c.drawImage(ImageReader(MARCA), (w - mw * 0.30) / 2, (h - mh * 0.30) / 2 - 20, mw * 0.30, mh * 0.30, mask="auto")
    c.setFont("Times-Roman", 30)
    c.drawString(42, h - 70, "ME")
    c.setFont("Helvetica", 5)
    c.drawString(44, h - 82, "MALAGA")
    c.setFont("Helvetica-Oblique", 9)
    for n, t in enumerate(["ME Malaga", "C. Victoria, 6, Distrito Centro", "", "Malaga, MA 29012, ES", "000 000 000"]):
        c.drawCentredString(w / 2, h - 40 - n * 11, t)
    y = h - 130
    c.rect(36, y - 76, w - 72, 76)
    for yy, t in [(y - 20, "Nombre Contacto"), (y - 31, "Dirección:"), (y - 56, "Teléfono:"), (y - 68, "Email:")]:
        fila(c, yy, [(42, t)], "Helvetica-Bold")
    campos = [("Block ID:", orden["block_id"]), ("Catering Manager:", "Default Owner SPAIN"),
              ("Sales Manager:", "Default Owner SPAIN"), ("Tipo Reserva:", orden["tipo_reserva"]),
              ("Block Name:", orden["nombre"]), ("Status/Catering Status:", "DEF/DEF"), ("PM:", ""),
              ("Contacto del Grupo:", ""), ("Total Habs", "0")]
    for n, (k, v) in enumerate(campos):
        fila(c, y - 10 - n * 8.2, [(290, k)], "Helvetica-Bold")
        fila(c, y - 10 - n * 8.2, [(385, v)], tam=7)
    y -= 92
    c.rect(36, y - 28, w - 72, 28)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(w / 2, y - 11, f"{DIAS[dia['fecha'].weekday()]}, {dia['fecha']:%d/%m/%y}")
    fila(c, y - 24, [(42, "Hora"), (105, "Sala"), (230, "Evento"), (330, "Montaje"), (430, "Asistentes"), (520, "Precio")],
         "Helvetica-Bold", 7)
    c.drawCentredString(w / 2, 22, f"Page {pagina} of {total}")
    return y - 48


def escribe_pdf(orden: dict, destino: Path) -> None:
    c = canvas.Canvas(str(destino), pagesize=A4, invariant=1)
    c.setTitle(orden["nombre"])
    total = 2 * len(orden["dias"])
    pagina = 0
    for dia in orden["dias"]:
        # Página A: tabla de sesiones y notas
        pagina += 1
        y = cabecera(c, orden, dia, pagina, total)
        fila(c, y, [(42, "INFO GENERAL"), (105, dia["info"])])
        y -= 24
        for ini, fin, sala, evento, montaje, pax, precio in dia["sesiones"]:
            fila(c, y, [(42, f"{ini} - {fin}"), (105, sala), (230, evento), (330, montaje), (430, f"{pax} Pax"), (520, precio)])
            y -= 16
        y -= 10
        fila(c, y, [(42, "F&B"), (105, dia["fb"][0])])
        for n, linea in enumerate(dia["fb"][1:], start=1):
            fila(c, y - n * 11, [(105, linea)])
        c.showPage()
        # Página B: servicio de comida / bebida
        pagina += 1
        y = cabecera(c, orden, dia, pagina, total)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(A4[0] / 2, y, "Servicio Comida")
        y -= 14
        for cab, pax, platos in dia["comidas"]:
            fila(c, y, [(42, f"{cab} {pax} Pax")], "Helvetica-Bold")
            y -= 16
            for p in platos:
                fila(c, y, [(60, f"- {p}")])
                y -= 13
            y -= 8
        c.showPage()
    c.save()


def main() -> int:
    ap = argparse.ArgumentParser(description="Genera órdenes de servicio ficticias de hoy a hoy+4.")
    ap.add_argument("--salida", default=str(INBOX_DIR), help="carpeta de salida (por defecto inbox/)")
    ap.add_argument("--dias", type=int, default=5, help="días vista, contando hoy (por defecto 5)")
    ap.add_argument("--hoy", help="fecha de hoy AAAA-MM-DD (por defecto la de Málaga)")
    args = ap.parse_args()
    hoy = datetime.strptime(args.hoy, "%Y-%m-%d").date() if args.hoy else ahora_local().date()
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    ordenes = ordenes_de_la_ventana(hoy, args.dias)
    for o in ordenes:
        escribe_pdf(o, salida / o["archivo"])
    print(f"Demo: {len(ordenes)} órdenes ficticias de {hoy} a {hoy + timedelta(days=args.dias - 1)} en {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
