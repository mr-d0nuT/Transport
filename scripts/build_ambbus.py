#!/usr/bin/env python3
"""Genera los horarios de TODA la red de bus de AMB (metropolitanos + NitBus)
a partir de su GTFS abierto.

Ni la API de paradas de TMB ni iBus conocen esta red: sus paradas tienen códigos
de seis cifras y otro operador (Avanza, Monbus, Soler i Sauret, TUSGSAL…). Sin
esto, en media área metropolitana la app no tenía llegadas que enseñar.

La red entera son ~890.000 salidas, unos 10 MB: demasiado para bajárselo de una
pieza en el móvil. Por eso se trocea en celdas geográficas de 0,05° (~5 km): la
app baja solo la del sitio donde estás mirando.

Salida:
  amb-bus/stops.json   -> {"v", "s": [[codi, nom, lat, lon, tros, [línies]], ...]}
  amb-bus/<tros>.json  -> {"v", "lines": [[curt, llarg, color, color_text]], "heads": [...],
                           "dates": {"YYYYMMDD": [svcIdx]},
                           "stops": {codi: [[lineIdx, headIdx, svcIdx, [minut, ...]], ...]}}

  amb-bus/lines.json   -> {"v", "r": [[línia, destí, [codi, ...]], ...],
                           "c": {línia: [color, color_text]}}

El nombre del trozo va escrito en cada parada de stops.json, así que la app no
tiene que saber cómo se ha troceado: mira la parada y pide su fichero.
lines.json guarda el recorrido de cada línea y sentido (solo los códigos de
parada; el nombre y las coordenadas ya están en stops.json) para poder desplegar
el itinerario sin cargar los horarios enteros.

Los minutos van desde medianoche del día de servicio y pueden pasar de 1440
(la madrugada del NitBus son las horas 24-31 del día anterior).
"""
import collections, json, os, shutil, sys
from datetime import date, timedelta

import gtfs_compact

GTFS_URL = "https://www.ambmobilitat.cat/OpenData/google_transit.zip"
OUT_DIR = "amb-bus"
DAYS_AHEAD = 10      # se regenera cada semana; con 10 días sobra margen
CELL = 20            # 1/0,05° : celdas de ~5 km
MAX_CELL_BYTES = 400_000   # por encima de esto, la celda se parte en trozos


def cell_of(lat, lon):
    return f"{int(round(lat * CELL))}_{int(round(lon * CELL))}"


def main():
    zf = gtfs_compact.fetch_gtfs(GTFS_URL)

    def rows(name):
        import csv, io
        with zf.open(name) as f:
            for r in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
                yield {(k or "").strip(): (v or "").strip() for k, v in r.items()}

    # el GTFS trae los colores oficiales: ámbar el bus metropolitano, azul el NitBus
    routes = {r["route_id"]: (r["route_short_name"], r["route_long_name"],
                              (r.get("route_color") or "FFAA00").upper(),
                              (r.get("route_text_color") or "343434").upper())
              for r in rows("routes.txt")}
    lines, line_idx = [], {}
    for rid, info in sorted(routes.items(), key=lambda kv: kv[1][0]):
        line_idx[rid] = len(lines)
        lines.append(list(info))

    trips = {t["trip_id"]: t for t in rows("trips.txt")}

    # calendario: desde ayer (la madrugada es del día de servicio anterior)
    today = date.today()
    horizon = {today + timedelta(d) for d in range(-1, DAYS_AHEAD)}
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
    dates = {k: sorted(v) for k, v in sorted(dates.items())}

    heads, head_idx = [], {}
    def head_of(t):
        h = t.get("trip_headsign") or ""
        if h not in head_idx:
            head_idx[h] = len(heads)
            heads.append(h)
        return head_idx[h]

    stops_meta = {}
    for s in rows("stops.txt"):
        try:
            stops_meta[s["stop_id"]] = (s["stop_name"].strip(), round(float(s["stop_lat"]), 5),
                                        round(float(s["stop_lon"]), 5))
        except (TypeError, ValueError):
            continue

    print("Recorriendo stop_times…", file=sys.stderr)
    by_stop = collections.defaultdict(list)      # stop_id -> [[li, svc, hi, min], ...]
    lines_at = collections.defaultdict(set)
    patterns = {}                                # (li, hi) -> recorrido más largo
    trip_seq = collections.defaultdict(list)
    for st in rows("stop_times.txt"):
        t = trips.get(st["trip_id"])
        if not t or t["service_id"] not in svc_idx or st["stop_id"] not in stops_meta:
            continue
        when = gtfs_compact_to_min(st.get("departure_time") or st.get("arrival_time"))
        if when is None:
            continue
        li = line_idx[t["route_id"]]
        hi = head_of(t)
        by_stop[st["stop_id"]].append([li, svc_idx[t["service_id"]], hi, when])
        lines_at[st["stop_id"]].add(lines[li][0])
        trip_seq[st["trip_id"]].append((int(st["stop_sequence"]), st["stop_id"], li, hi))

    # de cada línea y sentido nos quedamos con el recorrido más largo: es el que
    # sirve para desplegar el itinerario
    for seq in trip_seq.values():
        seq.sort()
        key = (seq[0][2], seq[0][3])
        if key not in patterns or len(seq) > len(patterns[key]):
            patterns[key] = [x[1] for x in seq]

    # --- reparto en celdas ---
    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)

    # Las salidas se agrupan por línea+destino+servicio: son cientos por parada
    # y repetir los tres índices en cada una multiplica el tamaño por tres
    grouped = {}
    for sid, deps in by_stop.items():
        g = collections.defaultdict(list)
        for li, svc, hi, when in deps:
            g[(li, hi, svc)].append(when)
        grouped[sid] = [[li, hi, svc, sorted(mins)] for (li, hi, svc), mins in sorted(g.items())]

    # Reparto en celdas geográficas; las que se pasan de tamaño se parten en
    # trozos consecutivos (las paradas van ordenadas, así que siguen juntas)
    raw_cells = collections.defaultdict(list)
    for sid in grouped:
        name, lat, lon = stops_meta[sid]
        raw_cells[cell_of(lat, lon)].append(sid)

    shard_of = {}
    shards = collections.defaultdict(dict)
    for cell, sids in raw_cells.items():
        sids.sort(key=lambda s: (stops_meta[s][1], stops_meta[s][2]))
        chunk, size, part = [], 0, 1
        def flush(chunk, part, multi):
            name = f"{cell}-{part}" if multi else cell
            for s2 in chunk:
                shard_of[s2] = name
                shards[name][s2] = grouped[s2]
        for sid in sids:
            weight = sum(12 + 5 * len(g[3]) for g in grouped[sid])
            if chunk and size + weight > MAX_CELL_BYTES:
                flush(chunk, part, True)
                chunk, size, part = [], 0, part + 1
            chunk.append(sid)
            size += weight
        if chunk:
            flush(chunk, part, part > 1)

    stop_list = []
    for sid in grouped:
        name, lat, lon = stops_meta[sid]
        stop_list.append([sid, name, lat, lon, shard_of[sid], sorted(lines_at[sid])])
    stop_list.sort(key=lambda s: s[0])
    version = today.isoformat()
    with open(os.path.join(OUT_DIR, "stops.json"), "w", encoding="utf-8") as f:
        json.dump({"v": version, "s": stop_list}, f, ensure_ascii=False, separators=(",", ":"))

    with open(os.path.join(OUT_DIR, "lines.json"), "w", encoding="utf-8") as f:
        json.dump({"v": version,
                   "r": [[lines[li][0], heads[hi], pat] for (li, hi), pat in sorted(patterns.items())],
                   "c": {l[0]: [l[2], l[3]] for l in lines}},
                  f, ensure_ascii=False, separators=(",", ":"))

    total = 0
    for cell, stops in shards.items():
        payload = {"v": version, "lines": lines, "heads": heads, "dates": dates, "stops": stops}
        path = os.path.join(OUT_DIR, f"{cell}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        total += os.path.getsize(path)

    sizes = sorted(os.path.getsize(os.path.join(OUT_DIR, f)) for f in os.listdir(OUT_DIR))
    print(f"{OUT_DIR}/: {len(stop_list)} paradas · {len(lines)} líneas · {len(shards)} trozos · "
          f"{total / 1e6:.1f} MB en total · celda mediana {sizes[len(sizes) // 2] / 1024:.0f} KB · "
          f"mayor {sizes[-1] / 1024:.0f} KB", file=sys.stderr)


def gtfs_compact_to_min(hms):
    parts = (hms or "").split(":")
    if len(parts) < 2 or not parts[0].strip().isdigit():
        return None
    return int(parts[0]) * 60 + int(parts[1])


if __name__ == "__main__":
    main()
