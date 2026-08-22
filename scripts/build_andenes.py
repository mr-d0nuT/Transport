#!/usr/bin/env python3
"""Genera andenes-metro.json: la geometría de los andenes del metro de
Barcelona, sus accesos a la calle y sus escaleras, a partir de OpenStreetMap.

Con esto la app puede decir en qué parte del tren conviene ir (cabeza, centro
o cola) para salir justo delante del transbordo o de la salida a la calle.

Formato:
{
  "v": "YYYY-MM-DD",
  "s": [                              # estaciones
    {
      "n": "Diagonal",
      "c": [lat, lon],
      "p": {"L3": [[lat,lon],[lat,lon]], "L5": [...]},   # eje del andén, extremo a extremo
      "e": [[lat, lon, "Rambla Catalunya"], ...],        # accesos a la calle
      "x": [[lat, lon], ...]                             # escaleras y ascensores del interior
    }, ...
  ]
}

El eje del andén se guarda sin orientar: la app deduce dónde queda la cabeza
del tren con el sentido de la marcha (parada anterior -> parada de bajada).
"""
import hashlib, json, math, os, sys, time, urllib.parse, urllib.request
from datetime import date

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
RETRIES = 4
CACHE_DIR = os.environ.get("OVERPASS_CACHE")   # opcional: acelera reejecuciones
NETWORK = "Metro de Barcelona"
BBOX = "41.28,1.95,41.52,2.35"          # área metropolitana
PLATFORM_FALLBACK_HALF = 45             # medio andén (m) cuando OSM no lo dibuja
PLATFORM_MAX_LEN = 130                  # algún andén está dibujado con toda la estación
ENTRANCE_RADIUS = 250                   # m alrededor de la estación
INDOOR_RADIUS = 160                     # m alrededor de la estación
OUT = "andenes-metro.json"


def overpass(query):
    """Consulta a Overpass rotando espejos: los públicos caen y limitan a menudo."""
    cache = None
    if CACHE_DIR:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache = os.path.join(CACHE_DIR, hashlib.sha1(query.encode()).hexdigest() + ".json")
        if os.path.exists(cache):
            with open(cache, encoding="utf-8") as f:
                return json.load(f)
    last = None
    for intento in range(RETRIES):
        for ep in ENDPOINTS:
            try:
                req = urllib.request.Request(
                    ep, urllib.parse.urlencode({"data": query}).encode(),
                    headers={"User-Agent": "transport-bcn-build/1.0 (+https://github.com/mr-d0nuT/TMB)"})
                with urllib.request.urlopen(req, timeout=300) as r:
                    els = json.load(r)["elements"]
                if not els:
                    raise ValueError("respuesta vacía (¿espejo con extracto parcial?)")
                if cache:
                    with open(cache, "w", encoding="utf-8") as f:
                        json.dump(els, f)
                return els
            except Exception as e:      # noqa: BLE001 - probamos el siguiente espejo
                print(f"  {ep} falló: {e}", file=sys.stderr)
                last = e
        if intento < RETRIES - 1:
            espera = 60 * (intento + 1)
            print(f"  todos los espejos fallan, reintento en {espera}s…", file=sys.stderr)
            time.sleep(espera)
    raise SystemExit(f"Overpass no responde: {last}")


def dist(a, b):
    """Metros entre dos (lat, lon)."""
    la = math.radians((a[0] + b[0]) / 2)
    dx = (b[1] - a[1]) * 111320 * math.cos(la)
    dy = (b[0] - a[0]) * 110540
    return math.hypot(dx, dy)


def long_axis(points):
    """Los dos vértices más separados de un polígono: el eje largo del andén."""
    best, pair = 0, None
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = dist(points[i], points[j])
            if d > best:
                best, pair = d, (points[i], points[j])
    return pair, best


def extend(center, bearing_pt, half):
    """Eje de `half` metros a cada lado de `center` en la dirección de `bearing_pt`."""
    la = math.radians(center[0])
    dx = (bearing_pt[1] - center[1]) * 111320 * math.cos(la)
    dy = (bearing_pt[0] - center[0]) * 110540
    n = math.hypot(dx, dy)
    if n < 1:
        return None
    ux, uy = dx / n, dy / n
    dlon = half * ux / (111320 * math.cos(la))
    dlat = half * uy / 110540
    return ([center[0] - dlat, center[1] - dlon], [center[0] + dlat, center[1] + dlon])


def clamp_axis(axis, center, max_len=PLATFORM_MAX_LEN):
    """Recorta ejes desmesurados (polígonos que abarcan la estación entera)
    dejando `max_len` metros centrados en el punto de parada."""
    total = dist(axis[0], axis[1])
    if total <= max_len:
        return axis
    # proyecta el punto de parada sobre el eje y recorta a su alrededor
    t = max(0.0, min(1.0, project_fraction(center, axis)))
    mid = [axis[0][0] + (axis[1][0] - axis[0][0]) * t,
           axis[0][1] + (axis[1][1] - axis[0][1]) * t]
    trimmed = extend(mid, axis[1], max_len / 2)
    return trimmed or axis


def project_fraction(p, axis):
    """Posición de `p` sobre el eje: 0 en un extremo, 1 en el otro."""
    la = math.radians(axis[0][0])
    ax = (axis[1][1] - axis[0][1]) * 111320 * math.cos(la)
    ay = (axis[1][0] - axis[0][0]) * 110540
    px = (p[1] - axis[0][1]) * 111320 * math.cos(la)
    py = (p[0] - axis[0][0]) * 110540
    n2 = ax * ax + ay * ay
    return 0.5 if n2 == 0 else (px * ax + py * ay) / n2


def norm_name(s):
    return " ".join((s or "").replace("Barcelona-", "").split())


def r5(v):
    return round(v, 5)


def main():
    print("Descargando líneas de metro…", file=sys.stderr)
    rels = overpass(f'[out:json][timeout:300];'
                    f'rel["route"="subway"]["network"~"{NETWORK}",i]({BBOX});out body;')
    print(f"  {len(rels)} relaciones de línea", file=sys.stderr)

    print("Descargando andenes…", file=sys.stderr)
    plats = {w["id"]: w for w in overpass(
        f'[out:json][timeout:300];rel["route"="subway"]["network"~"{NETWORK}",i]({BBOX})->.r;'
        f'way(r.r:"platform");out geom;')}
    stops = {n["id"]: n for n in overpass(
        f'[out:json][timeout:300];rel["route"="subway"]["network"~"{NETWORK}",i]({BBOX})->.r;'
        f'node(r.r:"stop");out;')}
    print(f"  {len(plats)} andenes dibujados, {len(stops)} puntos de parada", file=sys.stderr)

    print("Descargando vías, accesos y escaleras…", file=sys.stderr)
    tracks = overpass(f'[out:json][timeout:300];'
                      f'way["railway"~"^(subway|light_rail|narrow_gauge)$"]({BBOX});out geom;')
    entrances = overpass(f'[out:json][timeout:300];'
                         f'node["railway"="subway_entrance"]({BBOX});out;')
    indoor = overpass(f'[out:json][timeout:300];('
                      f'way["highway"~"^(steps|elevator)$"]({BBOX});'
                      f'node["highway"="elevator"]({BBOX});'
                      f');out center;')
    print(f"  {len(tracks)} vías, {len(entrances)} accesos, {len(indoor)} escaleras/ascensores",
          file=sys.stderr)

    # --- estaciones: agrupamos por nombre normalizado, uniendo los andenes de
    #     todas las líneas y sentidos que paran ahí ---
    stations = {}   # nombre -> {n, pts:[], lines:{ref: [ejes]}}
    no_geom = 0

    for rel in rels:
        line = rel.get("tags", {}).get("ref")
        if not line:
            continue
        # PTv2 ordena los miembros: parada, andén, parada, andén…
        groups, cur = [], None
        for m in rel.get("members", []):
            role = m.get("role", "")
            if role.startswith("stop") and m["type"] == "node":
                cur = {"stop": stops.get(m["ref"]), "plats": []}
                groups.append(cur)
            elif role.startswith("platform") and cur is not None and m["type"] == "way":
                if m["ref"] in plats:
                    cur["plats"].append(plats[m["ref"]])

        for g in groups:
            node = g["stop"]
            if not node:
                continue
            name = norm_name(node.get("tags", {}).get("name"))
            if not name:
                continue
            center = [node["lat"], node["lon"]]
            axis = None
            for w in g["plats"]:
                geom = [[p["lat"], p["lon"]] for p in w.get("geometry", [])]
                if len(geom) < 2:
                    continue
                pair, length = long_axis(geom)
                if pair and length >= 25:      # descarta andenes de tranvía/bus mal etiquetados
                    axis = pair
                    break
            if axis is None:
                # OSM no dibuja este andén: lo deducimos de la vía que pasa por
                # el punto de parada, con la longitud típica de un andén
                axis = axis_from_track(center, tracks)
                if axis is None:
                    no_geom += 1
                    continue
            st = stations.setdefault(name, {"n": name, "pts": [], "lines": {}})
            st["pts"].append(center)
            st["lines"].setdefault(line, []).append(axis)

    print(f"  {len(stations)} estaciones, {no_geom} andenes sin geometría utilizable",
          file=sys.stderr)

    # --- ensamblado final ---
    out = []
    for st in stations.values():
        lat = sum(p[0] for p in st["pts"]) / len(st["pts"])
        lon = sum(p[1] for p in st["pts"]) / len(st["pts"])
        center = [lat, lon]

        lines = {}
        for line, axes in st["lines"].items():
            # los dos sentidos comparten el eje longitudinal: nos quedamos con
            # el andén más largo, que es el que mejor describe la extensión real
            best = clamp_axis(max(axes, key=lambda a: dist(a[0], a[1])), center)
            lines[line] = [[r5(best[0][0]), r5(best[0][1])], [r5(best[1][0]), r5(best[1][1])]]

        ent = []
        for n in entrances:
            if dist(center, [n["lat"], n["lon"]]) <= ENTRANCE_RADIUS:
                nm = norm_name(n.get("tags", {}).get("name"))
                ent.append([r5(n["lat"]), r5(n["lon"])] + ([nm] if nm else []))

        stairs = []
        for e in indoor:
            c = e.get("center") or ({"lat": e.get("lat"), "lon": e.get("lon")}
                                    if e.get("lat") is not None else None)
            if not c:
                continue
            if dist(center, [c["lat"], c["lon"]]) <= INDOOR_RADIUS:
                stairs.append([r5(c["lat"]), r5(c["lon"])])

        out.append({"n": st["n"], "c": [r5(lat), r5(lon)], "p": lines,
                    "e": ent[:14], "x": stairs[:40]})

    out.sort(key=lambda s: s["n"])
    data = {"v": date.today().isoformat(), "s": out}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    con_acceso = sum(1 for s in out if s["e"])
    print(f"{OUT}: {len(out)} estaciones, "
          f"{sum(len(s['p']) for s in out)} andenes, "
          f"{con_acceso} con accesos mapeados", file=sys.stderr)


def axis_from_track(center, tracks):
    """Eje aproximado del andén siguiendo la vía que pasa por el punto de parada."""
    best = None
    for w in tracks:
        geom = w.get("geometry") or []
        for i in range(len(geom) - 1):
            a, b = [geom[i]["lat"], geom[i]["lon"]], [geom[i + 1]["lat"], geom[i + 1]["lon"]]
            d = min(dist(center, a), dist(center, b))
            if best is None or d < best[0]:
                best = (d, a, b)
    if not best or best[0] > 30:
        return None
    _, a, b = best
    return extend(center, b if dist(center, b) > dist(center, a) else a, PLATFORM_FALLBACK_HALF)


if __name__ == "__main__":
    main()
