#!/usr/bin/env python3
"""Horarios de metro y bus de TMB a partir de su GTFS estático oficial.

Con esto la app deja de depender de que haya cobertura y de que iBus/iMetro
respondan: bajo tierra, con la API caída o en las líneas automáticas L9 y L10
—que no publican tiempo real— siempre puede decir a qué hora pasa el siguiente,
y hasta qué hora hay servicio.

Las paradas se guardan por stop_code, que es el número que usan la API de TMB y
la propia app ("523"), no por el stop_id del GTFS ("1.523"). El metro lleva una
"m" delante porque los dos numeran desde el 1 y chocan: el 523 es a la vez la
estación Sagrada Família y una parada de bus en Via Augusta.

Formato y troceado: ver scripts/gtfs_shards.py
"""
import re, sys

import gtfs_shards

BASE = "https://api.tmb.cat/v1/static/datasets/gtfs.zip"
OUT_DIR = "tmb-sched"


def credentials():
    """Las claves viven en index.html (app de cliente: son públicas igualmente)."""
    src = open("index.html", encoding="utf-8").read()
    app_id = re.search(r"const APP_ID = '([^']+)'", src)
    app_key = re.search(r"const APP_KEY = '([^']+)'", src)
    if not app_id or not app_key:
        sys.exit("No encuentro APP_ID/APP_KEY en index.html")
    return app_id.group(1), app_key.group(1)


def clave_parada(fila):
    """Metro y bus numeran por separado y sus códigos chocan: el metro se marca."""
    code = (fila.get("stop_code") or "").strip()
    return ("m" + code) if fila["stop_id"].startswith("1.") else code


def main():
    app_id, app_key = credentials()
    gtfs_shards.build(f"{BASE}?app_id={app_id}&app_key={app_key}", OUT_DIR,
                      color_default=("DA291C", "FFFFFF"), stop_key_fn=clave_parada)


if __name__ == "__main__":
    main()
