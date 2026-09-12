# 🚍 Transport BCN

**App web para consultar en tiempo real los próximos buses, metros, trams y trenes de la parada más cercana a tu ubicación en Barcelona y su área.**

### 👉 [mr-d0nut.github.io/Transport](https://mr-d0nut.github.io/Transport/)

Se abre en el navegador, detecta tu posición y muestra al instante qué llega y en cuántos minutos. Instalable como app (PWA) en móvil y escritorio.

---

## Qué hace

- **Línea de tiempo de llegadas.** Los próximos minutos dibujados: cada salida en su sitio, y la franja rayada de lo que tardas en llegar a la parada, para ver de un golpe cuáles no coges.
- **Cinta del viaje a escala.** Cada ruta se dibuja proporcional al tiempo, con las caminatas y las esperas marcadas: se ve la forma del trayecto sin leer un número.
- **Metro en vivo.** La línea entera dibujada con **los trenes moviéndose por ella**, reconstruidos cruzando las llegadas en tiempo real de cada estación con los tiempos entre paradas del horario oficial. Nadie publica dónde están los trenes: se deducen.
- **Vuelta a casa.** Un botón 🏠 junto a las pestañas: un toque te da la ruta a casa y mantenerlo pulsado la cambia. De noche, la app te dice hasta cuándo puedes quedarte: la última salida que te lleva a casa **sin NitBus**, con cuenta atrás en vivo. Si el metro ya ha cerrado, te dice la ruta nocturna y a qué hora vuelve a haber metro.
- **Funciona sin cobertura.** Los horarios oficiales de TMB van compilados en la app: bajo tierra, con las APIs caídas o en la L9 y la L10 —que no dan tiempo real— sigue diciendo a qué hora pasa el siguiente.
- **Paradas cercanas por GPS, sin tocar nada.** Al abrirla (y al volver a ella si te has movido) busca tu ubicación —una persona dentro del círculo azul—, marca en el mapa todas las paradas de alrededor y abre las llegadas de la más cercana con servicio, enmarcadas como «Parada seleccionada».
- **Un solo buscador.** «Parada o destino…»: un número es el código del poste de una parada; lo demás, un destino. Junto a él, el botón 🏠.
- **Llegadas en tiempo real**, refrescadas cada 20 segundos:
  - 🚌 **Bus TMB** (iBus)
  - 🚇 **Metro TMB** (iMetro)
  - 🚊 **TRAM** (T1–T6), y cuando el directo no llega, su horario oficial del día —compilado cada madrugada desde la API de AMB, que sabe de obras y servicios especiales—; si una parada está cortada, lo dice
  - 🚆 **Rodalies y Media Distancia de Renfe**, con el horario oficial de Renfe de toda Catalunya: el directo de Renfe no lo puede leer ninguna web (no manda CORS y su CDN bloquea los servidores en la nube), así que la estación nunca se queda en blanco
  - 🚞 **FGC**
  - 🚏 **Bus metropolitano de AMB** (B, L, M, SB, EP… 138 líneas que TMB no conoce) y 🌙 **NitBus** (N0-N28), **en tiempo real** con la API oficial de AMB a través del [relé](relay/README.md) —el mismo dato que su app, con destino y minutos—, más las alteraciones del servicio (desvíos, obras) en cada línea. Sin relé, tira del GTFS-RT público y, si tampoco llega, del horario oficial compilado
  - 🚍 **Hispano Igualadina** (horarios GTFS precompilados)
- **¿Cabeza o cola?** En cada tramo de metro te dice en qué parte del tren colocarte para bajar justo delante del transbordo o de la salida que te toca — y te nombra la salida ("al bajar en Espanya, la salida Exposició / Gran Via queda por ahí"). Sale de la geometría de los andenes, los accesos y las escaleras de OpenStreetMap, cruzada con el sentido de la marcha.
- **El último kilómetro, en transporte.** Si una ruta acaba con más de 450 m a pie, la app busca el bus o el metro que te acerca desde donde bajas y, si lo hay, ya no te propone ir andando: de Passeig de Gràcia a Diagonal 335, el L4 hasta Verdaguer o el H10, el 47 y el 39 desde Roger de Llúria. En trayectos cortos por la ciudad compone también esos saltos directos de una sola línea, que el planner oficial ignora. Nada es inventado: el recorrido y los minutos entre paradas salen del GTFS de TMB, la hora de paso del horario oficial y, si pasa en menos de media hora, del tiempo real de iBus/iMetro; sin datos, la opción no se enseña. Si la línea que te acerca es la misma en la que ya ibas, te dice que sigas en ella.
- **Caminatas medidas por la calle.** Cada tramo a pie de las rutas compuestas se mide con el enrutador a pie de OpenStreetMap (Valhalla de FOSSGIS, una sola petición por búsqueda) y las horas de la ruta se rehacen con esa medida: de Passeig de Gràcia a Diagonal 335 son 993 m, no los 749 m de la línea recta. Si el servidor no contesta, la caminata sale marcada con «≈».
- **Lo que hoy no funciona.** La app lee los avisos oficiales de TMB, parada a parada y estación a estación: si una parada está anulada (obras, fiesta mayor, manifestación) sale apagada en el mapa, la ficha lo dice con un botón a la parada alternativa oficial, sus horarios dejan de mostrarse y ninguna ruta te manda allí. Igual con los enlaces de metro cerrados entre líneas, y los accesos, ascensores y escaleras fuera de servicio.
- **Un tren, una tarjeta.** Renfe publica el mismo tren en el horario de Rodalies y en el de Media Distancia (a veces dos veces): la app lo enseña una sola vez y con el nombre de las pantallas de la estación (R16, no REG.EXP.).
- **Sin caminatas absurdas.** Ninguna ruta con un tramo a pie de más de 12 minutos: si todas lo tienen, la app avisa y solo las enseña si dices que sí. El listón se mide sobre la ruta más rápida y nunca castiga una caminata que ninguna alternativa evita (la estación queda a 1,3 km y punto).
- **Las dos redes de FGC.** Para ir a la línea Llobregat-Anoia (Santa Coloma de Cervelló, Sant Boi, Martorell, Igualada, Manresa) desde el centro, la app busca la estación que de verdad enlaza —Pl. Espanya— aunque las más cercanas sean las del Vallès.
- **Correspondencias en cada parada.** Al desplegar el recorrido de una línea, cada parada muestra a la derecha con qué otras líneas enlaza ahí (metro, tram, Rodalies, FGC y bus), con sus colores oficiales. Pulsando el "+N" se despliegan las que faltan, y pulsando una línea se abre su recorrido entero.
- **Cuenta atrás y retrasos.** Cada tramo de la ruta dice cuánto falta para que salga ("sale en 6 min", actualizado solo) y, cuando la parada tiene tiempo real, si va con retraso, en hora o adelantado.
- **Margen de transbordo.** Cada enlace muestra los minutos que quedan entre bajarte del anterior y salir el siguiente, en ámbar si va justo.
- **Planificador de trayectos.** Escribe un destino (buscador sobre toda Cataluña vía Photon/OSM) y propone rutas combinando bus, metro, tram, tren, FGC y tramos a pie, ordenadas por hora de llegada pero con cada metro a pie por encima de 400 m pesando: la primera tarjeta dice si es la que llega antes o la que menos te hace andar. Las rutas aparecen en cuanto hay alguna («Buscando más opciones…») y la lista se completa sola cuando contesta el planner de TMB, que tarda de 3 a 5 s; las respuestas del planner se reutilizan durante un minuto. Todo va enmarcado como «Destino seleccionado», y solo hay una tarjeta desplegada a la vez. Cada ruta se dibuja sobre el mapa con el recorrido real, no en línea recta.
- **Modo navegación.** Sigue el trayecto en vivo con el GPS, avisa del siguiente paso y de la bajada, y permite replanificar sin salir de la ruta. El panel del viaje va arriba, pegado a la cabecera y siempre a mano, con el mapa justo debajo.
- **Botón rojo "Alternativa".** En pleno viaje busca rutas más rápidas bajándote no solo en la próxima parada sino en los **intercambiadores que quedan por el camino** —en un regional de Altafulla a Pg. de Gràcia, bajarse en Sants y coger el metro—, con la hora exacta de paso por cada parada y el retraso que lleve tu tren. Solo propone lo que ahorra de verdad (2 min o más) y un toque cambia la ruta.
- **Modo realidad aumentada.** Con la cámara y la brújula del móvil, superpone las paradas cercanas sobre lo que estás viendo, con sus próximas salidas.
- **Favoritos**, guardados en el navegador (`localStorage`), sin cuenta ni servidor.
- **Compartir parada** con enlace directo: `#p=bus:<código>`, `#p=metro:<id>`, `#p=tram:<ida>:<vuelta>`, `#p=train:<código>`, `#p=fgc:<código>`, `#p=hbus:<código>`.
- **Catalán, castellano e inglés**, con selector de banderas en la cabecera: cambia la interfaz al vuelo, sin recargar. Los nombres de paradas y estaciones se quedan como los publica cada operador.
- **Tema claro/oscuro** automático y funcionamiento offline de la interfaz gracias al service worker (los datos en tiempo real nunca se cachean).

## Cómo funciona

Es una **app estática de un solo archivo**: todo el HTML, CSS y JavaScript vive en [`index.html`](index.html), sin build ni dependencias que instalar. Se sirve tal cual desde GitHub Pages.

| Archivo | Para qué sirve |
|---|---|
| `index.html` | La app entera: interfaz, mapa, APIs, planificador, navegación y AR |
| `sw.js` | Service worker: cachea la carcasa para que arranque al instante |
| `manifest.webmanifest` + `icon-*` | Instalación como PWA |
| `hispano-igualadina.json` | Horarios de Hispano Igualadina precompilados desde el GTFS |
| `amb-bus/` | Horarios del bus de AMB (metropolitano y NitBus), troceados por zonas; `routes.json` casa el tiempo real con cada línea |
| `relay/` | El relé (Cloudflare Worker): tiempo real de AMB con la clave guardada en secreto, y pasarela para TRAM y Renfe. [Cómo desplegarlo](relay/README.md) |
| `tmb-sched/` | Horarios de metro y bus de TMB, troceados por zonas |
| `correspondencias.json` | Con qué líneas enlaza cada parada de bus |
| `andenes-metro.json` | Ejes de los andenes, accesos y escaleras del metro (para el consejo de vagón) |
| `scripts/gtfs_compact.py` | Compila un GTFS al JSON compacto que lee la app |
| `scripts/build_hispano.py` | Horarios de la Hispano desde el GTFS de la Generalitat |
| `scripts/gtfs_shards.py` | Compila un GTFS grande a horarios por parada, troceados |
| `scripts/build_ambbus.py` | Horarios del bus de AMB desde su GTFS |
| `scripts/build_tmb.py` | Horarios de metro y bus desde el GTFS oficial de TMB |
| `tram-sched.json` + `scripts/build_tram.py` | Horario del TRAM de hoy (API de AMB, cada madrugada; necesita el secreto `AMB_API_KEY`) |
| `scripts/build_corresp.py` | Correspondencias entre líneas desde la API de TMB |
| `scripts/build_andenes.py` | Andenes del metro desde OpenStreetMap (Overpass) |
| `.github/workflows/` | Los regeneran solos: Hispano los lunes, AMB los martes, correspondencias los miércoles, TMB los jueves, andenes cada mes |

### Datos y servicios usados

- [API de TMB](https://developer.tmb.cat/) — bus, metro, paradas y planificador
- [Open Data TRAM](https://opendata.tram.cat/)
- GTFS de la red metropolitana de [AMB](https://www.amb.cat/es/web/area-metropolitana/dades-obertes) — bus metropolitano y NitBus
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
python3 scripts/build_ambbus.py
```

```bash
python3 scripts/build_tmb.py
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
