# Diseño: Metro en vivo — dónde está cada tren, ahora

Fecha: 2026-08-24

## La idea

Nadie publica la posición de los trenes del metro de Barcelona. TMB publica otra
cosa: **en cuántos segundos llega el próximo tren a cada estación** (iMetro).
Y nosotros, desde el GTFS, sabemos **cuánto se tarda de una estación a la
siguiente**.

Con las dos cosas juntas, la posición sale sola:

> Si al próximo tren le faltan 40 segundos para llegar a Verdaguer y el tramo
> Diagonal→Verdaguer dura 2 minutos, ese tren va por el 67 % del tramo.

Formalmente: para cada estación `i`, si el próximo tren llega en `e_i` y el
tramo anterior dura `T_i`, hay un tren dentro de ese tramo en la posición
`1 − e_i/T_i`, siempre que `e_i ≤ T_i`. Si tarda más, el tren aún no ha llegado
al tramo y ya lo dibuja la estación de más atrás. **Sale exactamente un tren por
tramo ocupado, sin duplicados.**

## Cómo se ve

Una hoja a pantalla completa con la línea entera dibujada en vertical, con su
color oficial: las estaciones a un lado y **los trenes moviéndose**, uno por
sentido a cada lado del raíl, con la flecha de dirección y los minutos que le
faltan para la próxima estación. Se refresca cada 30 segundos y los trenes
**se deslizan** al nuevo sitio (transición CSS de 1,2 s), no saltan.

Tocar una estación abre sus llegadas.

Se entra desde dos sitios: los distintivos de correspondencia (ventana de
recorrido → botón "🔴 En vivo") y, sobre todo, desde la tarjeta de cualquier
estación de metro, que ahora ofrece "L3 en vivo · L5 en vivo" con el color de
cada línea.

## Coste

**27 peticiones a iMetro, una por estación, en paralelo: 117 ms medidos.** Es
más rápido que muchas pantallas de la propia app. Solo se piden mientras la
vista está abierta.

## Precisión, dicha en voz alta

- Los tiempos entre estaciones son la **mediana del horario**, no el tiempo real
  del tren concreto: con retrasos, la posición se desvía unos segundos.
- Solo se ven los trenes **a punto de llegar a una estación**; un tren parado en
  un andén o entre dos con mucho retraso puede no aparecer.
- No es telemetría: es una reconstrucción. Por eso la etiqueta dice los minutos
  que faltan, que sí es dato puro, y no una velocidad inventada.

## Lo que hizo falta en el compilador

`gtfs_shards.py` ahora guarda, además del recorrido de cada línea y sentido, la
**mediana de minutos entre paradas consecutivas** (`lines.json`, cuarto campo).
Sin eso no hay forma de convertir "llega en 40 s" en una posición.
