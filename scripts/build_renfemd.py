#!/usr/bin/env python3
"""Genera renfe-md.json: los trenes de Renfe que la API de cercanías no ve.

La app pregunta los horarios en directo a horarios.renfe.com/cer, pero ese
servicio solo cubre Rodalies. Los Regionales, Media Distancia, Avant y AVE no
salen: por eso "Lleida → Barcelona" —cuarenta trenes al día— devolvía que no
hay transporte. Renfe publica ese horario en GTFS abierto (sin clave) y aquí se
compila, recortado a Catalunya.

Mismo formato que catbus.json (ver build_catbus.py), así que la app lo lee con
el mismo código; el cuarto campo de cada línea es "T" y por eso los tramos se
pintan como tren y no como autobús.
"""
import sys

import build_catbus as base

GTFS_URL = "https://ssl.renfe.com/gtransit/Fichero_AV_LD/google_transit.zip"
OUT = "renfe-md.json"
# Catalunya con un margen: incluye Vinaròs y la Franja, que dan servicio a las
# Terres de l'Ebre y al Segrià
BBOX = (40.45, 0.10, 42.95, 3.40)


def build(out_path=OUT):
    base.FUENTES = [{
        "tag": "RNF", "operador": "Renfe", "url": GTFS_URL,
        "bbox": BBOX, "modo": "T",
    }]
    return base.build(out_path=out_path)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else OUT)
