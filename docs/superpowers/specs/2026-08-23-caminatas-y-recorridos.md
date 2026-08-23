# Diseño: caminatas largas fuera, y el recorrido de cada correspondencia

Fecha: 2026-08-23

## 1. Rutas con caminatas largas

**Problema.** El planner de TMB proponía rutas que empiezan con 16 minutos a
pie, y encima las ponía primero porque "llega antes". Una ruta así no es una
ruta útil.

**Lo primero que se probó y no sirve.** El planner **ignora
`maxWalkDistance`**: comprobado pidiendo la misma ruta con `maxWalkDistance=800`
y con `maxWalkDistance=600&walkReluctance=8`, y devuelve exactamente los mismos
cuatro itinerarios, con sus 16 minutos a pie. Así que el filtro tiene que ser
nuestro.

**Regla.** Ningún tramo a pie de más de **12 minutos**. Si alguna ruta cumple,
se enseñan solo esas. Si **ninguna** cumple, no se enseña nada: aparece un aviso
—"Todas las rutas obligan a caminar mucho. La que menos, N min a pie de una
tirada."— y solo al aceptarlo se muestran.

El límite va por **tramo**, no por total: tres caminatas de 5 minutos son
llevaderas; una de 16 es la que fastidia el viaje.

Ejemplo real (Horta → Fira Espanya): antes salía primero una ruta con 16 min a
pie; ahora sale la de "19 + L3" con caminatas de 6, 3 y 5 min, que el planner
ponía tercera.

La misma regla se aplica a las alternativas que se ofrecen en pleno trayecto.

## 2. Correspondencias desplegables y recorrido de la línea

En el listado de paradas de un recorrido, cada parada muestra hasta 4
distintivos y un `+N`:

- **Pulsar el `+N`** despliega el resto ahí mismo (la fila envuelve a varias
  líneas), sin abrir nada.
- **Pulsar un distintivo** abre una ventana inferior con el **recorrido entero
  de esa línea**. Cada parada de la lista es pulsable y lleva a sus llegadas.

De dónde salen las paradas de cada red:

| Red | Fuente |
|---|---|
| Metro | `transit/linies/metro/{codi}/estacions`, resolviendo el código por el nombre |
| Bus TMB | `transit/linies/bus/{línia}/parades`, un sentido |
| Bus AMB | `amb-bus/lines.json`, el recorrido compilado |
| TRAM | la tabla `TRAM_LINES` que ya lleva la app |
| Rodalies | `RENFE_STATIONS`, encadenando de terminal a terminal con `renfeChain` |
| FGC | los trenes de hoy del open data, agregando sus paradas |

**El caso de FGC es el flojo y se avisa.** Su open data no publica el trazado de
la línea: solo los trenes en circulación y las paradas que les quedan. A las
20:30 la L6 aparecía con tres paradas (Catalunya, Provença, Gràcia) porque es lo
que le quedaba al tren de turno. Como no hay forma de saber si la lista está
completa, la ventana lo dice: "15 paradas · según los trenes de hoy". La
alternativa buena sería compilar el GTFS de FGC como se hizo con AMB.

## Un fallo que costó encontrar

Al traducir la app quedó un `t('Siguiente: {m} min')` dentro de una función donde
había una variable local llamada `t` (`const t = via.propers_trens`). La variable
tapaba a la función de traducción y el metro dejó de dar llegadas con
`t is not a function`. Renombrada a `trens`. Conviene no volver a usar `t` como
nombre de variable en este fichero.
