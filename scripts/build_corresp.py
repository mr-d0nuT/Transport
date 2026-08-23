#!/usr/bin/env python3
"""Genera correspondencias.json: qué líneas enlazan en cada parada de bus.

La API de TMB lo publica de golpe (transit/parades/corresp, ~6,5 MB), pero eso
es demasiado para pedirlo desde el móvil cada vez: aquí se queda en lo justo
para pintar los distintivos junto a cada parada del recorrido.

Formato:
{
  "v": "YYYY-MM-DD",
  "s": {
    "839": [41.39557, 2.16694, [["L5","005A97","M"], ["47","DA291C","B"], ...]],
    ...
  }
}

El tercer campo de cada línea es el tipo: M metro, T tram, F FGC, R Rodalies,
B bus. La app lo usa para ordenar y para el icono.
"""
import json, re, sys, urllib.parse, urllib.request
from datetime import date

BASE = "https://api.tmb.cat/v1/transit"
OUT = "correspondencias.json"

# Familias de la API → tipo compacto. Las que no salen aquí (BusTuristic,
# Llançadores…) no se publican: no son enlaces útiles de transporte regular.
FAMILY_KIND = {
    "Metro": "M", "Metro-Funicular": "M",
    "TRAM": "T",
    "FGC": "F",
    "Rodalies-BCN": "R", "Rodalies-Regionals": "R",
    "Convencionals": "B", "Proximitat": "B", "Verticals": "B",
    "Horitzontals": "B", "Diagonals": "B", "XPRESBus": "B",
}


def credentials():
    """Las claves de la API viven en index.html (es una app de cliente: son
    públicas de todos modos). Las leemos de ahí para no tener dos copias."""
    src = open("index.html", encoding="utf-8").read()
    app_id = re.search(r"const APP_ID = '([^']+)'", src)
    app_key = re.search(r"const APP_KEY = '([^']+)'", src)
    if not app_id or not app_key:
        sys.exit("No encuentro APP_ID/APP_KEY en index.html")
    return app_id.group(1), app_key.group(1)


def get(path, auth):
    url = f"{BASE}/{path}?{auth}"
    req = urllib.request.Request(url, headers={"User-Agent": "transport-bcn-build/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def main():
    app_id, app_key = credentials()
    auth = urllib.parse.urlencode({"app_id": app_id, "app_key": app_key})

    print("Descargando paradas…", file=sys.stderr)
    coords = {}
    for f in get("parades", auth)["features"]:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"][:2]
        coords[int(p["CODI_PARADA"])] = [round(lat, 5), round(lon, 5)]
    print(f"  {len(coords)} paradas", file=sys.stderr)

    print("Descargando correspondencias…", file=sys.stderr)
    raw = get("parades/corresp", auth)["features"]
    print(f"  {len(raw)} enlaces", file=sys.stderr)

    by_stop = {}
    for f in raw:
        p = f["properties"]
        kind = FAMILY_KIND.get(p.get("NOM_FAMILIA"))
        if not kind:
            continue
        code = int(p["CODI_PARADA"])
        name = (p.get("NOM_LINIA") or "").strip()
        if not name:
            continue
        color = (p.get("COLOR_LINIA") or "DA291C").strip().upper()
        by_stop.setdefault(code, {})[name] = [name, color, kind]

    # Metro y tren primero, luego tranvía y bus; dentro de cada grupo, por nombre
    order = {"M": 0, "F": 1, "R": 2, "T": 3, "B": 4}
    def line_sort(l):
        n = l[0]
        num = int(re.sub(r"\D", "", n) or 0)
        return (order[l[2]], num, n)

    out = {}
    for code, lines in by_stop.items():
        if code not in coords:
            continue        # correspondencia de una parada que ya no existe
        out[str(code)] = coords[code] + [sorted(lines.values(), key=line_sort)]

    data = {"v": date.today().isoformat(), "s": out}
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    total = sum(len(v[2]) for v in out.values())
    print(f"{OUT}: {len(text)} bytes · {len(out)} paradas con enlaces · {total} enlaces",
          file=sys.stderr)


if __name__ == "__main__":
    main()
