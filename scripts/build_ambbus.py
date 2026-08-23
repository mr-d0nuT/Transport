#!/usr/bin/env python3
"""Horarios de toda la red de bus de AMB (metropolitanos B/L/M/SB… y NitBus).

Ni la API de paradas de TMB ni iBus conocen esta red: otro operador (Avanza,
Monbus, Soler i Sauret, TUSGSAL…) y códigos de parada de seis cifras. Sin esto,
en media área metropolitana la app no tenía llegadas que enseñar.

Formato y troceado: ver scripts/gtfs_shards.py
"""
import gtfs_shards

GTFS_URL = "https://www.ambmobilitat.cat/OpenData/google_transit.zip"
OUT_DIR = "amb-bus"


def main():
    # ámbar el metropolitano, azul el NitBus: los colores vienen en el propio GTFS
    gtfs_shards.build(GTFS_URL, OUT_DIR, color_default=("FFAA00", "343434"))


if __name__ == "__main__":
    main()
