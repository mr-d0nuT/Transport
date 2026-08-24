#!/usr/bin/env python3
"""Genera catbus.json: el bus de Catalunya que no es de Barcelona.

Dos orígenes, un solo fichero:

  * El GTFS interurbano de la Generalitat (analisi.transparenciacatalunya.cat),
    con los 111 operadores de carretera —Sagalés, Hispano Igualadina, Teisa,
    Plana, Sarfa, Alsina Graells, Barcelona Bus…— y las cuatro provincias.
  * Los urbanos que publican los ayuntamientos en el NAP del Ministerio
    (nap.transportes.gob.es): EMT Tarragona, TMG Girona, Autobusos de Lleida,
    Reus Transport, TMESA Terrassa y Mataró Bus. Estos piden una clave: va en
    la variable de entorno NAP_API_KEY (en CI, el secreto del repo). Sin clave
    el fichero se genera igual, solo con el interurbano.

Antes se compilaba solo la Hispano Igualadina porque todo junto pesaba 6 MB. La
clave para meterlo entero es que las expediciones del día son en realidad unos
pocos miles de patrones: la misma línea, con la misma secuencia de paradas y los
mismos minutos entre ellas, repetida a lo largo del día. Se guarda el patrón una
vez y de cada expedición solo su hora de salida.

{
  "v": "YYYY-MM-DD",                                   # día de compilación
  "lines": [[código, nombre, operador], ...],          # código público: e24, 530…
  "heads": ["destino", ...],
  "stops": [[stop_id, nombre, lat, lon], ...],
  "dates": {"YYYYMMDD": [svcIdx, ...], ...},           # de ayer a DAYS_AHEAD días
  "pats":  [[lineIdx, headIdx, [stopIdx...], [dt...], [svcIdx, salida, ...]], ...]
}

`dt` son los minutos entre parada y parada, y `salida` el minuto (desde
medianoche del día de servicio) en que esa expedición sale de la primera parada
del patrón. Puede pasar de 1440: el GTFS escribe la madrugada como horas 24-31
del día anterior. La app reconstruye cada expedición sumando.
"""
import collections, csv, hashlib, io, json, os, re, sys, urllib.request, zipfile
from datetime import date, timedelta

OUT = "catbus.json"
DAYS_AHEAD = 30
NAP = "https://nap.transportes.gob.es/api/Fichero/download/"

# tag: prefijo de los ids de parada, para que no choquen entre redes. El
# interurbano va sin prefijo (sus ids ya son únicos: PF08019019) y así no se
# rompen las paradas que la gente tenga guardadas en favoritas.
FUENTES = [
    {"tag": "", "operador": None,
     "url": "https://analisi.transparenciacatalunya.cat/download/bca2-b4i3/application/zip"},
    {"tag": "TGN", "operador": "EMT Tarragona", "nap": 1694},
    {"tag": "GIR", "operador": "TMG Girona", "nap": 1570},
    {"tag": "LLE", "operador": "Autobusos de Lleida", "nap": 1579},
    {"tag": "REU", "operador": "Reus Transport", "nap": 1788},
    {"tag": "TRS", "operador": "TMESA Terrassa", "nap": 1175},
    {"tag": "MAT", "operador": "Mataró Bus", "nap": 1173},
]

# El código con el que la gente conoce la línea va entre paréntesis al principio
# del nombre largo: "(e24) Esparreguera - Barcelona". El route_short_name del
# interurbano es un identificador interno ("L1990") que no dice nada en una
# parada; en los urbanos, en cambio, el short_name ya es el número del bus.
CODIGO = re.compile(r"^\s*\(([^)]{1,8})\)")


def fetch_gtfs(fuente):
    """Descarga el GTFS de una fuente. Con GTFS_CACHE apuntando a un directorio
    lo reutiliza entre ejecuciones (cómodo en local, irrelevante en CI). Los del
    NAP necesitan la clave; sin ella, esa fuente se salta."""
    if fuente.get("nap"):
        clave = os.environ.get("NAP_API_KEY", "").strip()
        if not clave:
            print(f"· {fuente['operador']}: sin NAP_API_KEY, se salta", file=sys.stderr)
            return None
        url = NAP + str(fuente["nap"])
        headers = {"ApiKey": clave, "accept": "application/octet-stream"}
    else:
        url, headers = fuente["url"], {"User-Agent": "transport-bcn-build/1.0"}

    cache_dir = os.environ.get("GTFS_CACHE")
    cache = None
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache = os.path.join(cache_dir, hashlib.sha1(url.encode()).hexdigest() + ".zip")
        if os.path.exists(cache):
            return zipfile.ZipFile(cache)
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=600).read()
    except Exception as e:
        print(f"· {fuente.get('operador') or 'Generalitat'}: no se ha podido descargar ({e})", file=sys.stderr)
        return None
    if cache:
        with open(cache, "wb") as f:
            f.write(raw)
    return zipfile.ZipFile(io.BytesIO(raw))


def limpia_operador(nombre):
    """Los nombres del GTFS vienen con la forma jurídica pegada y comillas
    sueltas: "Empresa Sagalés, SA" → "Empresa Sagalés"."""
    n = (nombre or "").strip().strip('"').strip()
    n = re.sub(r"[,\s]+(S\.?A\.?U?|S\.?L\.?U?|SCCL|SCP)\.?$", "", n, flags=re.I)
    return n.strip(" ,;")


def to_min(hms):
    # GTFS permite horas vacías en paradas sin timepoint y formatos H:MM
    parts = (hms or "").split(":")
    if len(parts) < 2 or not parts[0].strip().isdigit():
        return None
    return int(parts[0]) * 60 + int(parts[1])


class Acumulador:
    """Los índices compartidos por todas las redes: una línea, una parada o un
    destino se guardan una sola vez aunque salgan en varios ficheros."""

    def __init__(self):
        self.lines, self.line_idx = [], {}
        self.heads, self.head_idx = [], {}
        self.stops, self.stop_idx = [], {}
        self.svc_idx = {}
        self.dates = collections.defaultdict(set)
        self.patrones = collections.defaultdict(list)

    def linea(self, clave, datos):
        if clave not in self.line_idx:
            self.line_idx[clave] = len(self.lines)
            self.lines.append(list(datos))
        return self.line_idx[clave]

    def destino(self, texto):
        if texto not in self.head_idx:
            self.head_idx[texto] = len(self.heads)
            self.heads.append(texto)
        return self.head_idx[texto]

    def parada(self, clave, nombre, lat, lon):
        if clave not in self.stop_idx:
            self.stop_idx[clave] = len(self.stops)
            self.stops.append([clave, nombre, lat, lon])
        return self.stop_idx[clave]

    def servicio(self, clave):
        if clave not in self.svc_idx:
            self.svc_idx[clave] = len(self.svc_idx)
        return self.svc_idx[clave]


def compilar(zf, fuente, acc, horizon):
    tag = fuente["tag"]
    pref = (tag + ":") if tag else ""
    # (lat_min, lon_min, lat_max, lon_max): las fuentes nacionales (Renfe) traen
    # toda España y aquí solo interesa el trozo catalán
    bbox = fuente.get("bbox")

    def rows(name, obligatorio=True):
        if name not in zf.namelist():
            if obligatorio:
                raise KeyError(name)
            return
        with zf.open(name) as f:
            for r in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
                yield {(k or "").strip(): (v or "").strip() for k, v in r.items()}

    agencies = {a.get("agency_id", ""): limpia_operador(a.get("agency_name", ""))
                for a in rows("agency.txt")}

    routes = {}
    for r in rows("routes.txt"):
        largo = r.get("route_long_name", "")
        corto = r.get("route_short_name", "")
        m = CODIGO.match(largo)
        codigo = m.group(1) if m else re.sub(r"^L0+", "L", corto) or largo[:6]
        nombre = CODIGO.sub("", largo).strip(" -–") or codigo
        operador = fuente["operador"] or agencies.get(r.get("agency_id", ""), "")
        routes[r["route_id"]] = (codigo, nombre, operador, fuente.get("modo", "B"))
    if not routes:
        return 0

    trips = {t["trip_id"]: t for t in rows("trips.txt") if t["route_id"] in routes}

    # Calendario → fechas concretas activas. Empieza en AYER a propósito: a las
    # 02:00 los buses que circulan son los del día de servicio anterior (el GTFS
    # los escribe como horas 24-31), así que sin el día de ayer la madrugada sale
    # vacía. Hay redes (Lleida) que no traen calendar.txt, solo excepciones.
    svc_dates = collections.defaultdict(set)
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    fin_calendario = None
    for c in rows("calendar.txt", obligatorio=False):
        try:
            d0 = date(int(c["start_date"][:4]), int(c["start_date"][4:6]), int(c["start_date"][6:]))
            d1 = date(int(c["end_date"][:4]), int(c["end_date"][4:6]), int(c["end_date"][6:]))
        except (ValueError, KeyError):
            continue
        fin_calendario = max(fin_calendario or d1, d1)
        for d in horizon:
            if d0 <= d <= d1 and c.get(weekdays[d.weekday()]) == "1":
                svc_dates[c["service_id"]].add(d)
    for c in rows("calendar_dates.txt", obligatorio=False):
        try:
            d = date(int(c["date"][:4]), int(c["date"][4:6]), int(c["date"][6:]))
        except (ValueError, KeyError):
            continue
        if d in horizon:
            if c.get("exception_type") == "1":
                svc_dates[c["service_id"]].add(d)
            else:
                svc_dates[c["service_id"]].discard(d)

    activos = {s for s in {t["service_id"] for t in trips.values()} if svc_dates.get(s)}
    if not activos:
        # pasa: hay ayuntamientos que suben el GTFS al NAP y no lo vuelven a
        # tocar. Si el calendario terminó hace meses, aquí no hay nada que sacar
        raise ValueError("calendario caducado" + (f" el {fin_calendario}" if fin_calendario else " o vacío"))
    for s in sorted(activos):
        si = acc.servicio(pref + s)
        for d in svc_dates[s]:
            acc.dates[d.strftime("%Y%m%d")].add(si)

    trip_stops = collections.defaultdict(list)
    for st in rows("stop_times.txt"):
        if st["trip_id"] in trips:
            trip_stops[st["trip_id"]].append(
                (int(st["stop_sequence"]), st["stop_id"], to_min(st.get("departure_time")), to_min(st.get("arrival_time"))))

    stops_meta = {}
    for s in rows("stops.txt"):
        try:
            lat, lon = round(float(s["stop_lat"]), 5), round(float(s["stop_lon"]), 5)
        except (ValueError, KeyError, TypeError):
            continue
        if bbox and not (bbox[0] <= lat <= bbox[2] and bbox[1] <= lon <= bbox[3]):
            continue
        stops_meta[s["stop_id"]] = (s.get("stop_name") or "?", lat, lon)

    puestos = 0
    for tid, seq in trip_stops.items():
        t = trips[tid]
        if t["service_id"] not in activos:
            continue
        seq.sort()
        head = t.get("trip_headsign") or stops_meta.get(seq[-1][1], ("?",))[0]
        hi = acc.destino(head)
        paradas, tiempos = [], []
        prev = None
        for _, sid, dep, arr in seq:
            if sid not in stops_meta:
                continue
            when = dep if dep is not None else arr
            if when is None:
                when = prev          # parada sin timepoint: hereda la anterior
            if when is None:
                continue
            prev = when
            nombre, lat, lon = stops_meta[sid]
            paradas.append(acc.parada(pref + sid, nombre, lat, lon))
            tiempos.append(when)
        if len(paradas) < 2:
            continue
        # la línea se indexa por su contenido, no por route_id: Renfe publica el
        # mismo AVE bajo varios route_id y así no sale tres veces en la lista
        datos = routes[t["route_id"]]
        li = acc.linea(pref + "|".join(datos), datos)
        saltos = tuple(tiempos[i + 1] - tiempos[i] for i in range(len(tiempos) - 1))
        acc.patrones[(li, hi, tuple(paradas), saltos)].append(
            (acc.servicio(pref + t["service_id"]), tiempos[0]))
        puestos += 1
    return puestos


def build(out_path=OUT, days_ahead=DAYS_AHEAD):
    today = date.today()
    horizon = {today + timedelta(d) for d in range(-1, days_ahead)}
    acc = Acumulador()
    redes = 0
    for fuente in FUENTES:
        zf = fetch_gtfs(fuente)
        if zf is None:
            continue
        try:
            n = compilar(zf, fuente, acc, horizon)
        except Exception as e:
            print(f"· {fuente.get('operador') or 'Generalitat'}: GTFS ilegible ({e})", file=sys.stderr)
            continue
        if n:
            redes += 1
            print(f"· {fuente.get('operador') or 'Generalitat'}: {n} expediciones", file=sys.stderr)
    if not redes:
        sys.exit("Ninguna red se ha podido compilar")

    # salida determinista: si no, el commit semanal cambia solo por el orden en
    # que Python recorre los diccionarios
    pats = []
    for (li, hi, paradas, saltos), salidas in acc.patrones.items():
        salidas = sorted(set(salidas))
        pats.append([li, hi, list(paradas), list(saltos), [x for par in salidas for x in par]])
    pats.sort(key=lambda p: (p[0], p[1], p[4][1] if len(p[4]) > 1 else 0, p[2]))

    expediciones = sum(len(p[4]) // 2 for p in pats)
    out = {"v": today.isoformat(), "lines": acc.lines, "heads": acc.heads, "stops": acc.stops,
           "dates": {k: sorted(v) for k, v in sorted(acc.dates.items())},
           "pats": pats}
    data = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(data)
    print(f"{out_path}: {len(data)} bytes · {redes} redes · {len(acc.stops)} paradas · "
          f"{len(acc.lines)} líneas · {len(pats)} patrones · {expediciones} expediciones", file=sys.stderr)
    return out


if __name__ == "__main__":
    build(out_path=sys.argv[1] if len(sys.argv) > 1 else OUT)
