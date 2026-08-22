#!/usr/bin/env python3
"""Genera nitbus.json con los horarios del NitBus a partir del GTFS de AMB.

El NitBus lo opera AMB, no TMB: sus líneas (N0-N28) no están ni en la API de
paradas de TMB ni en iBus, así que de noche la app no tenía nada que enseñar
en paradas que sí tienen servicio. Con estos horarios sí.

Mismo formato que hispano-igualadina.json (ver scripts/gtfs_compact.py).
"""
import re
import gtfs_compact

GTFS_URL = "https://www.ambmobilitat.cat/OpenData/google_transit.zip"
OUT = "nitbus.json"
NIGHT_LINE = re.compile(r"^N\d", re.I)


def main():
    gtfs_compact.build(
        GTFS_URL,
        lambda route, agency: bool(NIGHT_LINE.match(route.get("route_short_name", ""))),
        OUT)


if __name__ == "__main__":
    main()
