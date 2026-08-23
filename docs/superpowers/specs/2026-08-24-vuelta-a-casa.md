# Diseño: "Vuelta a casa" — hasta cuándo puedes quedarte

Fecha: 2026-08-24

## La pregunta que ninguna app responde

Todas las apps de transporte contestan "¿cómo voy de A a B **ahora**?". La
pregunta real de cualquier noche fuera es otra: **"¿cuánto me queda de metro?"**
Nadie quiere consultar rutas cada media hora para descubrir, a la una, que ya
solo hay NitBus y una hora de viaje.

## Qué enseña

Una tarjeta, de 19:00 a 06:00, con tu casa como destino y tu posición como
origen:

| | |
|---|---|
| **Ahora** | la mejor ruta en este momento (34 min · L4 + L5) |
| **Último sin NitBus** | la última salida que te lleva a casa sin nocturnos, con **cuenta atrás en vivo** |
| **Primer metro** | solo si ya ha cerrado: a qué hora vuelve a haber (04:51 · L4+L5+V23) |

La cuenta atrás cambia de color: verde con margen, ámbar por debajo de 30
minutos ("si lo pierdes, toca NitBus") y rojo por debajo de 10.

Con el metro cerrado, en vez de un número imposible dice lo que hay: *"El metro
y el bus de día ya han cerrado · vuelves en NitBus"*, con la ruta nocturna real
y la hora del primer metro de la mañana.

## Cómo se calcula

El planner de TMB no tiene "dame la última salida", así que se **bisecciona**:
se le pregunta a distintas horas y se busca el punto en el que dejan de existir
rutas sin líneas N. Seis peticiones dan una precisión de unos cinco minutos, y
después se usa la hora exacta del itinerario encontrado, no la del sondeo.

- La tarjeta se pinta **en cuanto se sabe la ruta de ahora** (una petición) y las
  búsquedas rellenan las otras filas cuando terminan: nadie espera mirando un
  spinner doce segundos.
- Todo se cachea diez minutos por posición.
- Si ya ha cerrado, la segunda búsqueda cambia de sentido: en vez de la última
  salida, la **primera** del día siguiente.

## Definir la casa

En la pestaña "Ir a…", una fila invita a marcarla: se puede buscar la dirección
(y elegirla guarda la casa en vez de calcular una ruta) o usar la ubicación
actual. Se guarda solo en el móvil, como el resto de preferencias.

## Lo que queda fuera

- **Avisar solo**, sin abrir la app, cuando se acerque la hora límite: haría
  falta notificación push y un servidor, y esta app no tiene ninguno de los dos.
- El cálculo depende del planner de TMB. Sin red, la tarjeta no aparece; para
  eso están los horarios compilados de la vista de parada.
