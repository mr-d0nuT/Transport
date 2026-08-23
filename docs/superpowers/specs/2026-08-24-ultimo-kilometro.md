# Diseño: el último kilómetro también es transporte

Fecha: 2026-08-24

## Problema

Llegando en tren a Passeig de Gràcia con destino en Diagonal, la app decía
"Camina 749 m · 10 min" y se quedaba tan ancha. Por Passeig de Gràcia suben
varios autobuses que dejan en Diagonal: esas opciones no aparecían.

**Causa.** Los itinerarios compuestos por la app (Renfe, Hispano Igualadina,
FGC) ya encadenaban el **acceso** al origen con metro o bus cuando la estación
quedaba lejos (`chainAccess`, marcando `_oStop`), pero **la salida al destino no
se encadenaba nunca**: siempre acababa en una caminata en línea recta.

## Solución

Simétrica: los tres compositores marcan ahora también `_dStop` (la estación de
bajada) y `chainEgress` mira si algo te acerca al destino, **a la hora a la que
llegas**, no a la de ahora.

Dos fuentes, porque una sola no basta:

1. **El planner de TMB** con `date`/`time` en la hora de llegada.
2. **La topología de líneas** (`busHopTopology`), porque el planner es flojo en
   trayectos cortos: para Passeig de Gràcia → Diagonal proponía metro más 12
   minutos a pie e ignoraba los buses de Passeig de Gràcia. Se cruzan las líneas
   que pasan por una parada cercana a la estación (del dataset de
   correspondencias) con las paradas cercanas al destino, y se estima la espera
   (7 min) y el trayecto (1,5 min por parada). **Los tramos estimados se marcan
   como tales** y la app los pinta con "llegada ≈".

## El criterio de aceptación, que es lo importante

No es "llega antes": el bus suele llegar unos minutos **más tarde** que andando
600 metros, y aun así es lo que quiere la mayoría de la gente. La regla es:

- ahorra **al menos 300 m** a pie, **y**
- no llega **más de 6 minutos** más tarde que andando, **y**
- no cambia una caminata larga por otra (sigue valiendo el máximo de 12 min).

Entre 450 m y 1,2 km se ofrecen **las dos**: la de andar y la de acercarse en
bus. Por encima de 1,2 km solo la de transporte.

## Resultado en el caso del usuario

Altafulla-Tamarit → Avinguda Diagonal:

| | antes | ahora |
|---|---|---|
| 85 min | 🚶9' · R16 · **🚶8'** | igual (se mantiene) |
| 89 min | — | 🚶9' · R16 · **bus 7** · 🚶2' |
| 89 min | — | 🚶9' · R16 · **V15** · 🚶2' |

De 1.243 m a pie a 780 m, por cuatro minutos más.

## De paso

`busLineStops` solo aceptaba el código numérico de la línea: con "V15" fallaba
(es la 215) y esas líneas se caían en silencio de los saltos compuestos y de la
ventana de recorrido. Ahora se traduce el nombre con el listado de líneas.
