# Diseño: en qué vagón ir (cabeza / centro / cola) y margen de transbordo

Fecha: 2026-08-22

## Problema

Al hacer transbordo o al salir a la calle, el sitio donde te has colocado dentro
del tren decide si sales del andén el primero o si te comes 80 metros de pasillo
detrás de todo el mundo. Esa información no la da ninguna app de la casa: hay que
haber hecho el trayecto muchas veces para saber que en Sagrada Família la salida
a la Plaça queda en la cola, o que en Passeig de Gràcia el paso a la L4 está en
un extremo.

## Idea

Nadie publica "el vagón óptimo", pero sí está publicada la **geometría** de la
que se deduce: OpenStreetMap tiene dibujados los andenes del metro de Barcelona
(polígonos), los accesos a la calle (`railway=subway_entrance`) y buena parte de
las escaleras y ascensores del interior (`highway=steps|elevator`).

Con eso, el consejo sale de tres cosas:

1. **El eje del andén** donde te bajas (extremo a extremo).
2. **El sentido de la marcha**, que da el rumbo de la parada anterior a la de
   bajada: la cabeza del tren queda en el extremo hacia el que avanza.
3. **A dónde vas al bajar**: el andén de la línea del siguiente tramo si hay
   transbordo, o el acceso a la calle más cercano a lo que viene después.

Proyectando (3) sobre (1) orientado por (2) sale una fracción de 0 (cola) a 1
(cabeza), y de ahí `cola` (≤ 0,38), `centro` o `cabeza` (≥ 0,62).

## Datos: `andenes-metro.json`

Lo genera `scripts/build_andenes.py` desde Overpass y lo refresca el workflow
`.github/workflows/andenes.yml` el día 1 de cada mes. 65 KB, 160 estaciones,
197 andenes, 158 estaciones con accesos mapeados.

Decisiones del generador:

- **Un eje por estación y línea**, sin orientar. Los dos andenes de un mismo
  punto son paralelos y ocupan lo mismo a lo largo, así que no hace falta
  guardarlos por separado; el sentido lo pone la app en tiempo de uso. Esto
  evita además tener que casar el `headsign` del planner con el `to` de la
  relación de OSM.
- **Andenes que OSM no dibuja** (unos 200 de 369 puntos de parada): se deduce el
  eje siguiendo la vía que pasa por el `stop_position`, con la longitud típica de
  un andén (±45 m). Con esto no se queda ninguna estación fuera.
- **Andenes desmesurados**: algún polígono abarca la estación entera (Arc de
  Triomf salía de 198 m). Se recortan a 130 m centrados en el punto de parada;
  si no, todo cae en el centro y el consejo pierde valor. Los cortos no se tocan:
  un eje corto solo hace que la respuesta sea más tajante, no que se equivoque
  de extremo (y en la L11 los andenes son de verdad de 40 m).
- **Se validan los datos antes de commitear**: por debajo de 140 estaciones o
  170 andenes se asume que Overpass respondió a medias y no se publica.

## Cálculo en la app (`wagonTip`)

- La estación se localiza **por coordenadas** (la más cercana a menos de 500 m
  que tenga esa línea), no por nombre: los nombres de TMB y de OSM no siempre
  coinciden y las coordenadas no fallan.
- El **sentido** se saca de la última parada intermedia antes de la bajada
  (`intermediateStops`, que ya pedimos con `showIntermediateStops=true`). Si el
  tren entra casi perpendicular al eje (|cos| < 0,35, andén en curva o datos
  raros), **no se dice nada**: mejor callar que mandar al vagón equivocado.
- **Transbordo**: se toma el punto del andén de bajada más cercano al andén de la
  otra línea y, si hay escaleras o ascensores dibujados sobre el andén, se afina
  con la que cae más cerca de ese destino (es por donde se sale de verdad).
- **Salida a la calle**: se elige el acceso más cercano a lo que viene después
  (el siguiente tramo o el destino final) y se nombra en el consejo, así que de
  paso resuelve el "¿por qué salida salgo?".
- Sin dataset, sin datos de esa estación o con el tramo sin coordenadas,
  `wagonTip` devuelve `null` y la app se comporta como antes.

Cobertura medida sobre 25 tramos de metro de 12 trayectos distintos: **23 con
consejo (92 %)**, repartidos 8 cabeza / 4 centro / 11 cola.

## Interfaz

- En el detalle de cada ruta, bajo el tramo de metro: un tren de cinco vagones
  con la zona recomendada marcada, el morro a la derecha marcando el sentido, y
  el motivo ("al bajar en Sants Estació, el paso al L3 queda por ahí").
- Durante la navegación, junto a "Baja en X", una pastilla `🚇 cabeza`.

## Margen de transbordo

De paso, y sin datos nuevos: cada tramo de transporte muestra los minutos que
quedan entre bajarse del anterior (descontando la caminata) y salir este.
Verde si hay colchón, ámbar si el enlace va justo. Se calcula sobre el tramo de
transporte, no sobre la caminata, para que también aparezca cuando el planner
encadena dos líneas sin tramo a pie entre medias.

## Lo que queda fuera

- **Renfe y FGC**: sus andenes también están en OSM, pero sus tramos no siempre
  traen paradas intermedias con coordenadas y sin eso no se puede orientar el
  sentido. El código ya está preparado (`isMetroLine` es el único filtro).
- **Pasillos reales**: OSM tiene corredores interiores en las estaciones
  grandes. Enrutar por ellos daría el punto exacto de salida en vez de una
  aproximación por cercanía, pero es un proyecto aparte.
