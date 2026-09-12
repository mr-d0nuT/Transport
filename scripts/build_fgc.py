#!/usr/bin/env python3
"""Genera fgc-sched.json: el horario oficial de FGC (Vallès y Llobregat-Anoia).

Por qué: el open data "viajes-de-hoy" da las salidas de cada estación, pero no
dice a qué viaje pertenece cada una. La app emparejaba salidas y llegadas por
orden y le salían trenes fantasma: Sant Cugat → Pl. Catalunya en 10 minutos,
cuando son 29, y con un enlace que no se podía coger. El GTFS oficial sí trae
cada viaje entero, con sus horas parada a parada y su calendario.

Mismo formato que catbus.json y renfe-md.json, así que la app lo lee con el
mismo código (el cuarto campo de la línea es "T": se pinta como tren).

FGC publica el GTFS como ficheros sueltos en su portal de datos abiertos y sus
URLs cambian en cada actualización: aquí se resuelven y se empaquetan al vuelo.
"""
import io
import json
import sys
import urllib.request
import zipfile

import build_catbus as base

PORTAL = "https://dadesobertes.fgc.cat/api/explore/v2.1/catalog/datasets/gtfs_zip/records?limit=20"
OUT = "fgc-sched.json"
# FGC no sale de Catalunya central (Barcelona, Vallès, Bages, Anoia, Berguedà)
BBOX = (41.0, 1.2, 42.4, 2.6)
NECESARIOS = {"agency.txt", "routes.txt", "trips.txt", "stop_times.txt", "stops.txt",
              "calendar.txt", "calendar_dates.txt"}


def gtfs_del_portal():
    req = urllib.request.Request(PORTAL, headers={"User-Agent": "transport-bcn-build/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        datos = json.load(r)
    buf = io.BytesIO()
    metidos = []
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for item in datos.get("results", []):
            f = item.get("file") or {}
            nombre = f.get("filename", "")
            if nombre not in NECESARIOS:
                continue
            with urllib.request.urlopen(urllib.request.Request(
                    f["url"], headers={"User-Agent": "transport-bcn-build/1.0"}), timeout=600) as fr:
                z.writestr(nombre, fr.read())
            metidos.append(nombre)
    faltan = {"routes.txt", "trips.txt", "stop_times.txt", "stops.txt"} - set(metidos)
    if faltan:
        sys.exit(f"El portal de FGC no da {', '.join(sorted(faltan))}: no se escribe nada")
    print("GTFS de FGC: " + ", ".join(metidos), file=sys.stderr)
    return zipfile.ZipFile(buf)


def build(out_path=OUT):
    base.FUENTES = [{"tag": "FGC", "operador": "FGC", "zf": gtfs_del_portal(),
                     "bbox": BBOX, "modo": "T", "por_estacion": True}]
    return base.build(out_path=out_path)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else OUT)
