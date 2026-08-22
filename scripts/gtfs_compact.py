#!/usr/bin/env python3
"""Compila un GTFS en el JSON compacto que consume la app.

Lo usan build_hispano.py (bus interurbano de la Generalitat) y build_nitbus.py
(NitBus metropolitano de AMB): mismo formato de salida, así que la app lee los
dos con el mismo código.

{
  "v": "YYYY-MM-DD",                                    # día de compilación
  "lines": [[short, long], ...],
  "heads": ["destino", ...],
  "stops": [[stop_id, nombre, lat, lon], ...],
  "dates": {"YYYYMMDD": [svcIdx, ...], ...},          # de ayer a DAYS_AHEAD días
  "trips": [[lineIdx, svcIdx, headIdx, [[stopIdx, depMin], ...]], ...]
}

Los minutos son desde medianoche del día de servicio (pueden superar 1440: el
GTFS de los nocturnos usa horas 24-31 para la madrugada). La app deriva el
índice de salidas por parada y puede componer trayectos origen→destino
recorriendo la secuencia de paradas de cada viaje.
"""
import collections, csv, hashlib, io, json, os, sys, urllib.request, zipfile
from datetime import date, timedelta

DAYS_AHEAD = 30


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
    raw = urllib.request.urlopen(req, timeout=300).read()
    if cache:
        with open(cache, "wb") as f:
            f.write(raw)
    return zipfile.ZipFile(io.BytesIO(raw))


def build(gtfs_url, keep_route, out_path, days_ahead=DAYS_AHEAD):
    """Compila el GTFS de `gtfs_url` quedándose con las rutas para las que
    `keep_route(route_row, agency_name)` devuelve True."""
    zf = fetch_gtfs(gtfs_url)

    def rows(name):
        with zf.open(name) as f:
            for r in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
                yield {(k or "").strip(): (v or "").strip() for k, v in r.items()}

    agencies = {a.get("agency_id", ""): a.get("agency_name", "") for a in rows("agency.txt")}

    routes = {r["route_id"]: (r["route_short_name"], r["route_long_name"])
              for r in rows("routes.txt")
              if keep_route(r, agencies.get(r.get("agency_id", ""), ""))}
    if not routes:
        sys.exit("Ninguna ruta coincide con el filtro")

    lines, line_idx = [], {}
    for rid, (short, long_) in sorted(routes.items()):
        line_idx[rid] = len(lines)
        lines.append([short, long_])

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
    out_trips = []

    for tid, seq in trip_stops.items():
        t = trips[tid]
        if t["service_id"] not in svc_idx:
            continue
        seq.sort()
        head = t.get("trip_headsign") or stops_meta.get(seq[-1][1], ("?",))[0]
        if head not in head_idx:
            head_idx[head] = len(heads)
            heads.append(head)
        pattern = []
        prev_dep = None
        for _, sid, dep, arr in seq:
            if sid not in stops_meta:
                continue
            when = dep if dep is not None else arr
            if when is None:
                when = prev_dep  # parada sin timepoint: hereda la anterior
            if when is None:
                continue
            prev_dep = when
            if sid not in stop_idx:
                stop_idx[sid] = len(stops)
                name, lat, lon = stops_meta[sid]
                stops.append([sid, name, lat, lon])
            pattern.append([stop_idx[sid], when])
        if len(pattern) < 2:
            continue
        out_trips.append([line_idx[t["route_id"]], svc_idx[t["service_id"]], head_idx[head], pattern])

    # salida determinista: si no, el commit semanal cambia solo por el orden
    # en que Python recorre los conjuntos de fechas
    out = {"v": today.isoformat(), "lines": lines, "heads": heads,
           "stops": stops,
           "dates": {k: sorted(v) for k, v in sorted(dates.items())},
           "trips": out_trips}
    data = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(data)
    print(f"{out_path}: {len(data)} bytes · {len(stops)} paradas · {len(lines)} líneas · "
          f"{len(out_trips)} viajes", file=sys.stderr)
    return out
