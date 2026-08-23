# Diseño: cuánto falta para cada tramo, y si va con retraso

Fecha: 2026-08-23

## Petición

En el itinerario de una ruta, la cuenta atrás de lo que falta para que llegue el
transporte. Y los retrasos, si los hay.

## El problema de fondo

El planner de TMB **no da tiempo real**: sus tramos vienen con
`realTime: false` y `departureDelay: 0`. Las horas del itinerario son de
horario, no de lo que está pasando en la calle. Así que el retraso hay que
preguntárselo a la parada de subida, que es quien sí lo sabe:

| Modo | Fuente | Cruce |
|---|---|---|
| Bus | iBus, con `leg.from.stopCode` | línea + destino |
| Metro | iMetro, con `leg.from.stopCode` (es el mismo id) | línea + destino |
| TRAM | el proxy de siempre, con la parada más cercana (≤ 250 m) | línea + destino |
| FGC | `posicionament-dels-trens` | solo a nivel de línea: "retrasos en la línea" |

## El cuidado que hay que tener

**iBus dice cuándo pasa el próximo bus, no cuándo pasa *tu* bus.** Probado en la
parada 1235: el planner proponía el V25 de las 15:07 y iBus tenía un V25 a 0
minutos — no es un adelanto de 21 minutos, es otro coche. Si se resta sin más,
la app se inventa retrasos enormes.

Por eso:

- Solo se consulta lo que sale **dentro de 20 minutos**: más allá, ninguna de
  esas fuentes sabe nada todavía.
- Del paso en directo se coge el **más cercano al horario previsto**, filtrando
  antes por línea y por destino (en una parada con los dos sentidos, el destino
  decide).
- Si ese paso se va a **más de 8 minutos** del horario, se asume que es otro
  vehículo y **no se dice nada**: se deja la cuenta atrás del horario.

Comprobado sobre datos reales de iBus: mismo horario → "en hora"; horario 3
minutos antes del paso real → "+3 min tarde"; 25 minutos de diferencia → no lo
casa; salida a una hora vista → ni se consulta.

## Interfaz

Bajo cada tramo de transporte, una línea propia: **⏱ sale en 6 min**, en azul,
que se actualiza sola cada 5 segundos (mismo mecanismo que los tiempos de las
llegadas). Al lado, cuando hay tiempo real, la etiqueta: `+3 min tarde` (ámbar),
`en hora` (verde) o `1 min antes` (azul). Cuando hay tiempo real, la cuenta
atrás se calcula sobre el paso real, no sobre el horario.

La cuenta atrás del primer transporte sale también en la tarjeta plegada de cada
ruta, que es lo que se mira al comparar opciones. La cabecera de la tarjeta pasa
a poder envolver: en pantallas de 360 px la etiqueta "llega antes" baja de línea
en vez de desbordar.

Si la salida ya pasó, la cuenta atrás lo dice en gris ("salió hace 3 min") en
vez de mostrar un número que ya no sirve.

## Lo que queda fuera

- **Renfe**: sus tramos ya se componen con `tiempoReal: true`, así que la hora
  que se muestra es la real, pero la respuesta no trae el horario teórico con el
  que compararla para calcular el retraso.
- **L9/L10**: no publican tiempo real (la propia app ya lo avisa en la vista de
  llegadas), así que ahí solo hay cuenta atrás de horario.
- **Panel de navegación**: la cuenta atrás está en el itinerario; durante el
  trayecto en vivo manda la posición del GPS.
