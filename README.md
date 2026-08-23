# 🚍 Transport BCN

**App web para consultar en tiempo real los próximos buses, metros, trams y trenes de la parada más cercana a tu ubicación en Barcelona y su área.**

### 👉 [mr-d0nut.github.io/TMB](https://mr-d0nut.github.io/TMB/)

Se abre en el navegador, detecta tu posición y muestra al instante qué llega y en cuántos minutos. Instalable como app (PWA) en móvil y escritorio.

---

## Qué hace

- **Paradas cercanas por GPS.** Al abrirla busca tu ubicación y lista las paradas de alrededor, con el mapa marcándolas.
- **Llegadas en tiempo real**, refrescadas cada 20 segundos:
  - 🚌 **Bus TMB** (iBus)
  - 🚇 **Metro TMB** (iMetro)
  - 🚊 **TRAM** (T1–T6)
  - 🚆 **Rodalies Renfe**
  - 🚞 **FGC**
  - 🌙 **NitBus** (N0-N28, horarios del GTFS de AMB: de noche no hay tiempo real, pero sí a qué hora pasa)
  - 🚍 **Hispano Igualadina** (horarios GTFS precompilados)
- **¿Cabeza o cola?** En cada tramo de metro te dice en qué parte del tren colocarte para bajar justo delante del transbordo o de la salida que te toca — y te nombra la salida ("al bajar en Espanya, la salida Exposició / Gran Via queda por ahí"). Sale de la geometría de los andenes, los accesos y las escaleras de OpenStreetMap, cruzada con el sentido de la marcha.
- **Correspondencias en cada parada.** Al desplegar el recorrido de una línea, cada parada muestra a la derecha con qué otras líneas enlaza ahí (metro, tram, Rodalies, FGC y bus), con sus colores oficiales.
- **Cuenta atrás y retrasos.** Cada tramo de la ruta dice cuánto falta para que salga ("sale en 6 min", actualizado solo) y, cuando la parada tiene tiempo real, si va con retraso, en hora o adelantado.
- **Margen de transbordo.** Cada enlace muestra los minutos que quedan entre bajarte del anterior y salir el siguiente, en ámbar si va justo.
- **Planificador de trayectos.** Escribe un destino (buscador sobre toda Cataluña vía Photon/OSM) y propone rutas combinando bus, metro, tram, tren, FGC y tramos a pie, ordenadas penalizando las caminatas largas. Cada ruta se dibuja sobre el mapa con el recorrido real, no en línea recta.
- **Modo navegación.** Sigue el trayecto en vivo con el GPS, avisa del siguiente paso y de la bajada, y permite pedir una **alternativa** o replanificar sin salir de la ruta.
- **Modo realidad aumentada.** Con la cámara y la brújula del móvil, superpone las paradas cercanas sobre lo que estás viendo, con sus próximas salidas.
- **Favoritos y recientes**, guardados en el navegador (`localStorage`), sin cuenta ni servidor.
- **Compartir parada** con enlace directo: `#p=bus:<código>`, `#p=metro:<id>`, `#p=tram:<ida>:<vuelta>`, `#p=train:<código>`, `#p=fgc:<código>`, `#p=hbus:<código>`.
- **Tema claro/oscuro** automático y funcionamiento offline de la interfaz gracias al service worker (los datos en tiempo real nunca se cachean).

## Cómo funciona

Es una **app estática de un solo archivo**: todo el HTML, CSS y JavaScript vive en [`index.html`](index.html), sin build ni dependencias que instalar. Se sirve tal cual desde GitHub Pages.

| Archivo | Para qué sirve |
|---|---|
| `index.html` | La app entera: interfaz, mapa, APIs, planificador, navegación y AR |
| `sw.js` | Service worker: cachea la carcasa para que arranque al instante |
| `manifest.webmanifest` + `icon-*` | Instalación como PWA |
| `hispano-igualadina.json` | Horarios de Hispano Igualadina precompilados desde el GTFS |
| `nitbus.json` | Horarios del NitBus precompilados desde el GTFS de AMB |
| `correspondencias.json` | Con qué líneas enlaza cada parada de bus |
| `andenes-metro.json` | Ejes de los andenes, accesos y escaleras del metro (para el consejo de vagón) |
| `scripts/gtfs_compact.py` | Compila un GTFS al JSON compacto que lee la app |
| `scripts/build_hispano.py` | Horarios de la Hispano desde el GTFS de la Generalitat |
| `scripts/build_nitbus.py` | Horarios del NitBus desde el GTFS de AMB |
| `scripts/build_corresp.py` | Correspondencias entre líneas desde la API de TMB |
| `scripts/build_andenes.py` | Andenes del metro desde OpenStreetMap (Overpass) |
| `.github/workflows/` | Los regeneran solos: Hispano los lunes, NitBus los martes, correspondencias los miércoles, andenes cada mes |

### Datos y servicios usados

- [API de TMB](https://developer.tmb.cat/) — bus, metro, paradas y planificador
- [Open Data TRAM](https://opendata.tram.cat/)
- GTFS de la red metropolitana de [AMB](https://www.amb.cat/es/web/area-metropolitana/dades-obertes) — el NitBus
- Horarios de Rodalies de [Renfe](https://horarios.renfe.com/)
- [Dades obertes FGC](https://dadesobertes.fgc.cat/)
- GTFS de buses interurbanos de la [Generalitat de Catalunya](https://analisi.transparenciacatalunya.cat/)
- [OpenStreetMap](https://www.openstreetmap.org/copyright) vía Overpass, geocodificación con [Photon](https://photon.komoot.io/), mapas con [Leaflet](https://leafletjs.com/) y teselas de [CARTO](https://carto.com/attributions)

Las APIs de TRAM y Renfe no envían cabeceras CORS, así que se consultan a través de proxies públicos (`corsproxy.io`, `allorigins.win`) con respaldo entre ellos.

## Uso en local

No hace falta compilar nada, solo servir la carpeta por HTTP (la geolocalización y el service worker no funcionan con `file://`):

```bash
python3 -m http.server 8000
```

Y abrir `http://localhost:8000`. Para la cámara del modo AR hace falta HTTPS o `localhost`.

Para regenerar a mano los datos precompilados:

```bash
python3 scripts/build_hispano.py
```

```bash
python3 scripts/build_nitbus.py
```

```bash
python3 scripts/build_corresp.py
```

```bash
python3 scripts/build_andenes.py
```

## Cómo se calcula el vagón

No hay ninguna fuente que publique "el vagón óptimo": se deduce de la geometría.
De OpenStreetMap salen el contorno de cada andén, sus accesos a la calle y sus
escaleras; del itinerario, el sentido en el que llega el tren (la parada anterior
manda). Proyectando el sitio al que vas —el andén de la línea del transbordo, o
el acceso más cercano a tu destino— sobre el eje del andén, sale si te conviene
cabeza, centro o cola. Cuando el tren entra casi perpendicular al andén o faltan
datos de esa estación, la app no dice nada en vez de arriesgarse.

Es una estimación a partir de datos abiertos, no un plano oficial de TMB: acierta
el extremo, no el número exacto de vagón. Los detalles están en
[docs/superpowers/specs](docs/superpowers/specs/2026-08-22-vagon-optimo-y-margen-de-transbordo.md).

## Aviso

Proyecto personal, sin relación oficial con TMB, TRAM, Renfe, FGC ni Hispano Igualadina. Los horarios en tiempo real son los que publican esos servicios; úsalos como orientación.
