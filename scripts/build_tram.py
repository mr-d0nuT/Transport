#!/usr/bin/env python3
"""Horario del TRAM de hoy (Trambaix T1-T3 y Trambesòs T4-T6) desde la API de AMB.

Por qué: el tiempo real del TRAM (opendata.tram.cat) no manda CORS, así que un
navegador solo lo lee a través del relé. Sin relé, la parada del TRAM se quedaba
en un error. El TRAM no publica GTFS abierto, pero la API de AMB tiene el
horario oficial de cada parada (/v2/gtfs/{red}/stops/{parada}/timetable) y
marca qué servicio aplica hoy (todayService). No basta con el día de la semana:
hay servicios especiales (La Mercè, festivos, obras) que solo la API conoce,
así que esto se compila cada madrugada con el servicio del día. El de ayer se
conserva para la madrugada (sus horas 24:xx-26:xx siguen vivas).

Salida: tram-sched.json
  {"v": "AAAA-MM-DD",
   "hoy":  {"fecha": "AAAAMMDD", "s": [[lat, lon, nombre, [[línea, destino, [minutos…]], …]], …]},
   "ayer": {…mismo formato, el día anterior…}}

La app casa cada parada por coordenadas, sin depender de ningún código.
Necesita la variable de entorno AMB_API_KEY (en CI, el secreto del repo).
"""
import json, os, sys, time, urllib.error, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

API = "https://api.ambmobilitat.cat/v2"
REDES = ("trambaix", "trambesos")
OUT = "tram-sched.json"
TZ = ZoneInfo("Europe/Madrid")


def get(path, key, intentos=5):
    req = urllib.request.Request(API + path, headers={"x-api-key": key, "Accept": "application/json",
                                                      "User-Agent": "transport-bcn-build/1.0"})
    for n in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and n < intentos - 1:
                time.sleep(2 + 3 * n)  # la API limita a ráfagas cortas
                continue
            raise


def a_minutos(hms):
    h, m, *_ = hms.split(":")
    return int(h) * 60 + int(m)


def main():
    key = os.environ.get("AMB_API_KEY", "").strip()
    if not key:
        sys.exit("Falta AMB_API_KEY")
    hoy = datetime.now(TZ)

    rs = get("/gtfs/routes-and-stops", key)
    paradas = []
    for red in REDES:
        # solo las estaciones (location_type 1): los andenes repiten el horario
        estaciones = [s for s in rs[red]["stops"] if s.get("location_type") == 1] or rs[red]["stops"]
        for s in estaciones:
            try:
                tabla = get(f"/gtfs/{red}/stops/{s['stop_id']}/timetable", key)
            except Exception as e:
                print(f"· {red} {s['stop_name']}: {e}", file=sys.stderr)
                continue
            salidas = []
            for ruta in tabla or []:
                linea = "T" + str(ruta["route_id"])
                for it in ruta.get("itineraries_timetables", []):
                    mins = sorted({a_minutos(x) for sv in it.get("services_timetables", [])
                                   if sv.get("todayService") for x in sv.get("timetable", [])})
                    if mins:
                        salidas.append([linea, it.get("trips_headsign", "").replace("|", " | "), mins])
            # también las que hoy no tienen servicio (obras, cortes): así la app
            # puede decir «hoy no pasa» al momento en vez de esperar al directo
            paradas.append([round(s["stop_lat"], 5), round(s["stop_lon"], 5), s["stop_name"], salidas])
            time.sleep(0.35)

    con_servicio = sum(1 for p in paradas if p[3])
    if len(paradas) < 50 or con_servicio < 25:  # 58 estaciones: bastante menos es una API a medias
        sys.exit(f"Solo {len(paradas)} paradas ({con_servicio} con servicio): no se escribe nada")

    anterior = None
    try:
        with open(OUT, encoding="utf-8") as f:
            anterior = json.load(f).get("hoy")
    except (OSError, ValueError):
        pass
    fecha = hoy.strftime("%Y%m%d")
    salida = {"v": hoy.date().isoformat(), "hoy": {"fecha": fecha, "s": paradas}}
    if anterior and anterior.get("fecha") != fecha:
        salida["ayer"] = anterior
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, separators=(",", ":"))
    n = sum(len(p[3]) for p in paradas)
    print(f"{OUT}: {len(paradas)} paradas ({con_servicio} con servicio hoy), {n} sentidos ({fecha})", file=sys.stderr)


if __name__ == "__main__":
    main()
