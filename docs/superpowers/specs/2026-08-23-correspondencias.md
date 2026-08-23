# Diseño: correspondencias en el listado de paradas

Fecha: 2026-08-23

## Petición

Al desplegar el recorrido de una línea, cada parada donde hay enlace con otra
línea o con otro modo debería indicarlo a la derecha.

## Fuente

La API de TMB lo publica en `transit/parades/{codi}/corresp`, y también entero
en **`transit/parades/corresp`** (8718 enlaces, ~6,5 MB). Pedir 40 paradas de
una en una al abrir cada recorrido es inviable en el móvil, y 6,5 MB tampoco,
así que se precompila como los demás datasets.

`scripts/build_corresp.py` → **`correspondencias.json`** (232 KB, 36 KB
comprimidos): por código de parada, sus coordenadas y la lista de líneas con
nombre, color oficial y tipo (M metro, F FGC, R Rodalies, T tram, B bus).

- Se descartan las familias que no son transporte regular (BusTuristic,
  Llançadores).
- Se ordenan metro → FGC → Rodalies → tram → bus, para que en las paradas con
  muchos enlaces (hay una con 20) los cuatro que caben sean los útiles.
- Se descartan los 318 códigos que ya no existen en el listado de paradas.
- Las claves de la API se leen de `index.html`, que es donde ya viven: una app
  de cliente las expone igualmente, y así no hay dos copias que mantener.

## Dónde se pintan

| Sitio | De dónde salen las líneas |
|---|---|
| Recorrido de una línea de bus (al desplegar una llegada) | del dataset, por código de parada |
| Recorrido de una línea de metro | de `PICTO_GRUP`, que ya venía en la respuesta de la línea |
| Paradas de un tramo de bus en el detalle de una ruta | del dataset, por cercanía (≤ 50 m) |
| Paradas de un tramo de metro en el detalle de una ruta | del listado de estaciones, ya cacheado |

Siempre se quita la línea en la que ya vas. Se muestran hasta 4 distintivos (3
en el detalle de rutas, que es más estrecho) y el resto como "+N".

En el recorrido de bus el cruce va por código de parada, que es exacto. Donde no
hay código —los tramos de una ruta solo traen nombre y coordenadas— se cruza por
cercanía, con un filtro previo de caja para no recorrer 2676 paradas con
trigonometría por cada punto.

## Detalle de forma

Los distintivos de tren y metro llevan la esquina cuadrada y los de bus
redondeada, como en la señalética de TMB, para distinguirlos de un vistazo
además de por el color.
