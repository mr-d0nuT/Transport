#!/usr/bin/env python3
"""Compila un GTFS grande en horarios por parada, troceados por zonas.

Lo usan build_ambbus.py (red de AMB) y build_tmb.py (metro y bus de TMB), que
son demasiado grandes para bajárselos de una pieza en el móvil: la app pide
solo el trozo de la zona que estás mirando.

Salida en <out_dir>/:
  stops.json  -> {"v", "s": [[codi, nom, lat, lon, tros, [línies]], ...]}
  lines.json  -> {"v", "r": [[línia, destí, [codi, ...]], ...],
                  "c": {línia: [color, color_text]}}
  <tros>.json -> {"v", "lines": [[curt, llarg, color, color_text]], "heads": [...],
                  "dates": {"YYYYMMDD": [svcIdx]},
                  "stops": {codi: [[lineIdx, headIdx, svcIdx, [minut, ...]], ...]}}

El nombre del trozo va escrito en cada parada de stops.json: la app no necesita
saber cómo se ha troceado, mira la parada y pide su fichero.

Los minutos van desde medianoche del día de servicio y pueden pasar de 1440
(la madrugada se escribe como horas 24-31 del día anterior).
"""
import collections, csv, io, json, os, shutil, sys
from datetime import date, timedelta

import gtfs_compact

DAYS_AHEAD = 10          # se regenera cada semana; con 10 días sobra margen
CELL = 20                # 1/0,05° : celdas de ~5 km
MAX_CELL_BYTES = 400_000 # por encima de esto, la celda se parte en trozos


def cell_of(lat, lon):
    return f"{int(round(lat * CELL))}_{int(round(lon * CELL))}"


def to_min(hms):
    parts = (hms or "").split(":")
    if len(parts) < 2 or not parts[0].strip().isdigit():
        return None
    return int(parts[0]) * 60 + int(parts[1])


def build(gtfs_url, out_dir, color_default=("FFAA00", "343434"), keep_route=None,
          days_ahead=DAYS_AHEAD, stop_key_fn=None):
    """stop_key_fn(fila de stops.txt) -> con qué identificador se guarda cada
    parada. Por defecto el stop_id; TMB necesita el stop_code, que es el número
    que usan su API y la app ("523" y no "1.523")."""
    stop_key_fn = stop_key_fn or (lambda s: s["stop_id"])
    zf = gtfs_compact.fetch_gtfs(gtfs_url)
    nombres = set(zf.namelist())

    def rows(name):
        if name not in nombres:
            return
        with zf.open(name) as f:
            for r in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
                yield {(k or "").strip(): (v or "").strip() for k, v in r.items()}

    routes = {}
    for r in rows("routes.txt"):
        if keep_route and not keep_route(r):
            continue
        routes[r["route_id"]] = (r["route_short_name"] or r.get("route_long_name", ""),
                                 r.get("route_long_name", ""),
                                 (r.get("route_color") or color_default[0]).upper(),
                                 (r.get("route_text_color") or color_default[1]).upper())
    lines, line_idx = [], {}
    for rid, info in sorted(routes.items(), key=lambda kv: kv[1][0]):
        line_idx[rid] = len(lines)
        lines.append(list(info))

    trips = {t["trip_id"]: t for t in rows("trips.txt") if t["route_id"] in routes}

    # calendario: desde ayer, porque la madrugada es del día de servicio anterior
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
    dates = {k: sorted(v) for k, v in sorted(dates.items())}

    heads, head_idx = [], {}
    def head_of(t):
        h = t.get("trip_headsign") or ""
        if h not in head_idx:
            head_idx[h] = len(heads)
            heads.append(h)
        return head_idx[h]

    stops_meta, stop_key = {}, {}
    for s in rows("stops.txt"):
        # location_type 1 y 2 son la estación madre y sus accesos, no paradas
        if s.get("location_type") not in ("", "0", None):
            continue
        clave = (stop_key_fn(s) or "").strip()
        if not clave:
            continue
        try:
            stops_meta[clave] = (s["stop_name"].strip(), round(float(s["stop_lat"]), 5),
                                 round(float(s["stop_lon"]), 5))
            stop_key[s["stop_id"]] = clave
        except (TypeError, ValueError):
            continue

    # viajes por frecuencia: en vez de una hora fija, "cada X minutos de A a B"
    freqs = collections.defaultdict(list)
    for f in rows("frequencies.txt"):
        ini, fin, cada = to_min(f["start_time"]), to_min(f["end_time"]), int(f["headway_secs"]) // 60
        if ini is not None and fin is not None and cada > 0:
            freqs[f["trip_id"]].append((ini, fin, cada))

    print("Recorriendo stop_times…", file=sys.stderr)
    by_stop = collections.defaultdict(list)
    lines_at = collections.defaultdict(set)
    trip_seq = collections.defaultdict(list)
    seg_times = collections.defaultdict(list)

    def volcar(trip_id, filas):
        """Cierra un viaje: interpola las paradas sin hora y reparte sus salidas.

        TMB solo publica la hora en los puntos de control (el 47 % de las filas
        viene vacío); el resto se saca repartiendo el tiempo entre la parada
        anterior y la siguiente que sí la tengan."""
        t = trips.get(trip_id)
        if not t or not filas:
            return
        filas.sort()
        anclas = [i for i, f in enumerate(filas) if f[2] is not None]
        if not anclas:
            return
        for i in range(len(filas)):
            if filas[i][2] is not None:
                continue
            antes = [a for a in anclas if a < i]
            despues = [a for a in anclas if a > i]
            if antes and despues:
                a, b = antes[-1], despues[0]
                ta, tb = filas[a][2], filas[b][2]
                filas[i][2] = ta + round((tb - ta) * (i - a) / (b - a))
            else:
                filas[i][2] = filas[anclas[-1] if antes else anclas[0]][2]

        li, hi, svc = line_idx[t["route_id"]], head_of(t), svc_idx[t["service_id"]]
        repeticiones = None
        if trip_id in freqs:
            base = filas[0][2]
            repeticiones = [(salida - base) for ini, fin, cada in freqs[trip_id]
                            for salida in range(ini, fin + 1, cada)]
        for _, sid, when in filas:
            if repeticiones is None:
                by_stop[sid].append([li, svc, hi, when])
            else:
                for delta in repeticiones:
                    by_stop[sid].append([li, svc, hi, when + delta])
            lines_at[sid].add(lines[li][0])
        trip_seq[trip_id] = [(f[0], f[1], li, hi) for f in filas]
        # tiempos entre paradas consecutivas: hacen falta para saber dónde está
        # un tren cuando solo sabes en cuántos minutos llega a cada estación
        for a, b in zip(filas, filas[1:]):
            seg_times[(li, hi, a[1], b[1])].append(max(0, b[2] - a[2]))

    trip_actual, buffer = None, []
    for st in rows("stop_times.txt"):
        sid = stop_key.get(st["stop_id"])
        if sid is None:
            continue
        t = trips.get(st["trip_id"])
        if not t or t["service_id"] not in svc_idx:
            continue
        if st["trip_id"] != trip_actual:
            volcar(trip_actual, buffer)
            trip_actual, buffer = st["trip_id"], []
        buffer.append([int(st["stop_sequence"]), sid,
                       to_min(st.get("departure_time") or st.get("arrival_time"))])
    volcar(trip_actual, buffer)

    patterns = {}
    for seq in trip_seq.values():
        seq.sort()
        key = (seq[0][2], seq[0][3])
        if key not in patterns or len(seq) > len(patterns[key]):
            patterns[key] = [x[1] for x in seq]

    def mediana(v):
        v = sorted(v)
        return v[len(v) // 2] if v else 1

    # minutos de una parada a la siguiente, en cada línea y sentido
    pattern_times = {}
    for (li, hi), pat in patterns.items():
        pattern_times[(li, hi)] = [mediana(seg_times.get((li, hi, a, b), [])) for a, b in zip(pat, pat[1:])]

    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    # Agrupadas por línea+destino+servicio: repetir los tres índices en cada una
    # de las cientos de salidas de una parada multiplica el tamaño por tres
    grouped = {}
    for sid, deps in by_stop.items():
        g = collections.defaultdict(set)
        for li, svc, hi, when in deps:
            g[(li, hi, svc)].add(when)
        grouped[sid] = [[li, hi, svc, sorted(mins)] for (li, hi, svc), mins in sorted(g.items())]

    raw_cells = collections.defaultdict(list)
    for sid in grouped:
        _, lat, lon = stops_meta[sid]
        raw_cells[cell_of(lat, lon)].append(sid)

    shard_of, shards = {}, collections.defaultdict(dict)
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
    with open(os.path.join(out_dir, "stops.json"), "w", encoding="utf-8") as f:
        json.dump({"v": version, "s": stop_list}, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(out_dir, "lines.json"), "w", encoding="utf-8") as f:
        json.dump({"v": version,
                   "r": [[lines[li][0], heads[hi], pat, pattern_times[(li, hi)]]
                         for (li, hi), pat in sorted(patterns.items())],
                   "c": {l[0]: [l[2], l[3]] for l in lines}},
                  f, ensure_ascii=False, separators=(",", ":"))

    total = 0
    for cell, stops in shards.items():
        payload = {"v": version, "lines": lines, "heads": heads, "dates": dates, "stops": stops}
        path = os.path.join(out_dir, f"{cell}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        total += os.path.getsize(path)

    sizes = sorted(os.path.getsize(os.path.join(out_dir, f)) for f in os.listdir(out_dir))
    print(f"{out_dir}/: {len(stop_list)} paradas · {len(lines)} líneas · {len(shards)} trozos · "
          f"{total / 1e6:.1f} MB en total · trozo mediano {sizes[len(sizes) // 2] / 1024:.0f} KB · "
          f"mayor {sizes[-1] / 1024:.0f} KB", file=sys.stderr)
    return {"paradas": len(stop_list), "lineas": len(lines), "trozos": len(shards)}
