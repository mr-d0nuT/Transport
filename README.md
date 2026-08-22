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
  - 🚍 **Hispano Igualadina** (horarios GTFS precompilados)
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
| `scripts/build_hispano.py` | Genera ese JSON a partir del GTFS oficial de la Generalitat |
| `.github/workflows/hispano.yml` | Lo regenera y commitea automáticamente cada lunes |

### Datos y servicios usados

- [API de TMB](https://developer.tmb.cat/) — bus, metro, paradas y planificador
- [Open Data TRAM](https://opendata.tram.cat/)
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

Para regenerar los horarios de Hispano Igualadina a mano:

```bash
python3 scripts/build_hispano.py
```

## Aviso

Proyecto personal, sin relación oficial con TMB, TRAM, Renfe, FGC ni Hispano Igualadina. Los horarios en tiempo real son los que publican esos servicios; úsalos como orientación.
