#!/usr/bin/env python3
"""Genera hispano-igualadina.json a partir del GTFS oficial de buses
interurbanos de la Generalitat (analisi.transparenciacatalunya.cat).

Mismo formato que nitbus.json (ver scripts/gtfs_compact.py).
"""
import gtfs_compact

GTFS_URL = "https://analisi.transparenciacatalunya.cat/download/bca2-b4i3/application/zip"
AGENCY_MATCH = "igualadina"
OUT = "hispano-igualadina.json"


def main():
    gtfs_compact.build(
        GTFS_URL,
        lambda route, agency: AGENCY_MATCH in agency.lower(),
        OUT)


if __name__ == "__main__":
    main()
