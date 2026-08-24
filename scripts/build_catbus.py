#!/usr/bin/env python3
"""Genera catbus.json: TODO el bus interurbano de Catalunya.

Fuente: el GTFS que publica la Generalitat en analisi.transparenciacatalunya.cat
con los 111 operadores de transporte interurbano por carretera (Sagalés, Hispano
Igualadina, Teisa, Plana, Sarfa, Alsina Graells, Barcelona Bus…). Cubre las
cuatro provincias, así que la app deja de ser solo del área de Barcelona.

Antes se compilaba solo la Hispano Igualadina porque el fichero entero pesaba
6 MB. La clave para meterlo todo es que 28.000 viajes son en realidad ~9.000
patrones: la misma línea, con la misma secuencia de paradas y los mismos
minutos entre ellas, repetida a lo largo del día. Guardando el patrón una vez y
solo la hora de salida de cada expedición, el fichero baja a menos de 1 MB.

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

GTFS_URL = "https://analisi.transparenciacatalunya.cat/download/bca2-b4i3/application/zip"
OUT = "catbus.json"
DAYS_AHEAD = 30

# El código con el que la gente conoce la línea va entre paréntesis al principio
# del nombre largo: "(e24) Esparreguera - Barcelona". El route_short_name es un
# identificador interno ("L1990") que no sirve de nada en una parada.
CODIGO = re.compile(r"^\s*\(([^)]{1,8})\)")


def fetch_gtfs(url):
    """Descarga el GTFS. Con GTFS_CACHE apuntando a un directorio, lo reutiliza
    entre ejecuciones (cómodo en local, irrelevante en CI)."""
    cache_dir = os.environ.get("GTFS_CACHE")
    cache = None
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache = os.path.join(cache_dir, hashlib.sha1(url.encode()).hexdigest() + ".zip")
        if os.path.exists(cache):
            print(f"GTFS desde caché local: {cache}", file=sys.stderr)
            return zipfile.ZipFile(cache)
    print("Descargando GTFS…", file=sys.stderr)
    req = urllib.request.Request(url, headers={"User-Agent": "transport-bcn-build/1.0"})
    raw = urllib.request.urlopen(req, timeout=600).read()
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


def build(gtfs_url=GTFS_URL, out_path=OUT, days_ahead=DAYS_AHEAD):
    zf = fetch_gtfs(gtfs_url)

    def rows(name):
        with zf.open(name) as f:
            for r in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
                yield {(k or "").strip(): (v or "").strip() for k, v in r.items()}

    agencies = {a.get("agency_id", ""): limpia_operador(a.get("agency_name", ""))
                for a in rows("agency.txt")}

    routes = {}
    for r in rows("routes.txt"):
        largo = r.get("route_long_name", "")
        m = CODIGO.match(largo)
        codigo = m.group(1) if m else re.sub(r"^L0+", "L", r.get("route_short_name", ""))
        nombre = CODIGO.sub("", largo).strip(" -–") or codigo
        routes[r["route_id"]] = (codigo, nombre, agencies.get(r.get("agency_id", ""), ""))
    if not routes:
        sys.exit("El GTFS no trae rutas")

    lines, line_idx = [], {}
    for rid, datos in sorted(routes.items()):
        line_idx[rid] = len(lines)
        lines.append(list(datos))

    trips = {t["trip_id"]: t for t in rows("trips.txt") if t["route_id"] in routes}

    # Calendario → fechas concretas activas. Empieza en AYER a propósito: a las
    # 02:00 los buses que circulan son los del día de servicio anterior (el GTFS
    # los escribe como horas 24-31), así que sin el día de ayer la madrugada sale
    # vacía.
    today = date.today()
    horizon = {today + timedelta(d) for d in range(-1, days_ahead)}
    svc_dates = collections.defaultdict(set)
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for c in rows("calendar.txt"):
        d0 = date(int(c["start_date"][:4]), int(c["start_date"][4:6]), int(c["start_date"][6:]))
        d1 = date(int(c["end_date"][:4]), int(c["end_date"][4:6]), int(c["end_date"][6:]))
        for d in horizon:
            if d0 <= d <= d1 and c[weekdays[d.weekday()]] == "1":
                svc_dates[c["service_id"]].add(d)
    for c in rows("calendar_dates.txt"):
        d = date(int(c["date"][:4]), int(c["date"][4:6]), int(c["date"][6:]))
        if d in horizon:
            if c["exception_type"] == "1":
                svc_dates[c["service_id"]].add(d)
            else:
                svc_dates[c["service_id"]].discard(d)

    services = sorted({t["service_id"] for t in trips.values()} & set(svc_dates))
    svc_idx = {s: i for i, s in enumerate(services)}
    dates = collections.defaultdict(list)
    for s in services:
        for d in svc_dates[s]:
            dates[d.strftime("%Y%m%d")].append(svc_idx[s])

    def to_min(hms):
        # GTFS permite horas vacías en paradas sin timepoint y formatos H:MM
        parts = (hms or "").split(":")
        if len(parts) < 2 or not parts[0].strip().isdigit():
            return None
        return int(parts[0]) * 60 + int(parts[1])

    trip_stops = collections.defaultdict(list)
    for st in rows("stop_times.txt"):
        if st["trip_id"] in trips:
            trip_stops[st["trip_id"]].append(
                (int(st["stop_sequence"]), st["stop_id"], to_min(st["departure_time"]), to_min(st["arrival_time"])))

    stops_meta = {s["stop_id"]: (s["stop_name"], round(float(s["stop_lat"]), 5), round(float(s["stop_lon"]), 5))
                  for s in rows("stops.txt")}

    heads, head_idx = [], {}
    stops, stop_idx = [], {}
    patrones = collections.defaultdict(list)   # (línea, destino, paradas, saltos) → [(svc, salida)]

    for tid, seq in trip_stops.items():
        t = trips[tid]
        if t["service_id"] not in svc_idx:
            continue
        seq.sort()
        head = t.get("trip_headsign") or stops_meta.get(seq[-1][1], ("?",))[0]
        if head not in head_idx:
            head_idx[head] = len(heads)
            heads.append(head)
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
            if sid not in stop_idx:
                stop_idx[sid] = len(stops)
                name, lat, lon = stops_meta[sid]
                stops.append([sid, name, lat, lon])
            paradas.append(stop_idx[sid])
            tiempos.append(when)
        if len(paradas) < 2:
            continue
        saltos = tuple(tiempos[i + 1] - tiempos[i] for i in range(len(tiempos) - 1))
        clave = (line_idx[t["route_id"]], head_idx[head], tuple(paradas), saltos)
        patrones[clave].append((svc_idx[t["service_id"]], tiempos[0]))

    # salida determinista: si no, el commit semanal cambia solo por el orden en
    # que Python recorre los diccionarios
    pats = []
    for (li, hi, paradas, saltos), salidas in patrones.items():
        salidas.sort()
        pats.append([li, hi, list(paradas), list(saltos), [x for par in salidas for x in par]])
    pats.sort(key=lambda p: (p[0], p[1], p[4][1] if len(p[4]) > 1 else 0, p[2]))

    expediciones = sum(len(p[4]) // 2 for p in pats)
    out = {"v": today.isoformat(), "lines": lines, "heads": heads, "stops": stops,
           "dates": {k: sorted(v) for k, v in sorted(dates.items())},
           "pats": pats}
    data = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(data)
    print(f"{out_path}: {len(data)} bytes · {len(stops)} paradas · {len(lines)} líneas · "
          f"{len(pats)} patrones · {expediciones} expediciones", file=sys.stderr)
    return out


if __name__ == "__main__":
    build(out_path=sys.argv[1] if len(sys.argv) > 1 else OUT)
