# Diseño: horarios de TMB siempre disponibles, y "Ahora mismo"

Fecha: 2026-08-24

Dos mejoras que atacan las dos carencias que quedaban: que la app **dependía por
completo de la red y de que las APIs respondieran**, y que **nunca te decía nada
hasta que se lo pedías**.

---

## 1. Horarios de TMB compilados: la red de seguridad

**Hallazgo.** TMB publica su **GTFS estático completo** en
`api.tmb.cat/v1/static/datasets/gtfs.zip` (9,3 MB, con las mismas claves que ya
usa la app). Nunca se había usado.

Con eso, `scripts/build_tmb.py` genera `tmb-sched/`: **2.771 paradas, 117
líneas, 6 MB en 31 trozos** (mediano 83 KB), mismo formato y troceado que los
horarios de AMB.

Ahora la app responde en tres situaciones en las que antes se quedaba muda:

| Situación | Antes | Ahora |
|---|---|---|
| Sin cobertura (bajo tierra) | error | horario, del trozo ya cacheado |
| iBus/iMetro caídos | error | horario |
| **L9 y L10** (no publican tiempo real) | "esta estación no ofrece tiempos" | horario |

Comprobado apagando toda la red en el navegador: la parada 1235 sigue dando
V25 y N4, y Horta sigue dando la L5 en los dos sentidos. Y las estaciones del
aeropuerto (L9S), que nunca habían tenido horarios en esta app, ya los tienen.

**Detalles que costaron:**

- **El 47 % de los `stop_times` de TMB viene sin hora**: solo publican los
  puntos de control. Hay que **interpolar** el resto repartiendo el tiempo entre
  la parada anterior y la siguiente que sí la tengan. Sin eso salían 862 paradas
  en vez de 2.771.
- **Metro y bus numeran por separado y sus códigos chocan**: el 523 es a la vez
  la estación Sagrada Família y una parada de bus en Via Augusta. Las claves del
  metro llevan una `m` delante.
- Los viajes por frecuencia (`frequencies.txt`) se expanden a salidas concretas.
- Se **precarga en segundo plano** el trozo de la zona donde estás mirando
  cuando sí hay tiempo real, para que ya esté guardado cuando bajes al metro.

De paso, el compilador troceado se extrajo a `scripts/gtfs_shards.py`, que ahora
comparten AMB y TMB (se verificó que la salida de AMB no cambia).

---

## 2. "Ahora mismo": la app se adelanta

Antes, abrir la app era: esperar al GPS, mirar la lista de paradas cercanas,
tocar la tuya. Todos los días lo mismo.

Ahora, nada más abrirla, aparece un panel con **la parada que sueles usar a esta
hora** y sus próximas salidas ya cargadas. Un toque para abrirla del todo.

**Cómo decide.** Cada vez que abres una parada se anota en el móvil (nunca sale
de ahí): franja de dos horas, si era laborable o fin de semana, y cuántas veces.
La puntuación combina las veces que la abres **en esta franja**, si coincide el
tipo de día, si es favorita y si la has usado hace poco. Se guardan las 25
paradas más usadas, no todas.

Si no hay historial —la primera vez— el panel no aparece: no se inventa nada.

**Y de noche, lo que de verdad importa:** entre las 21:00 y las 5:00 el panel
avisa de **la hora del último servicio** si queda menos de dos horas. Esto sale
de los horarios compilados del punto 1, y mira **las dos redes**: preguntando
solo a TMB decía "último a las 22:39" con un NitBus a punto de pasar; ahora dice
05:11, que es la verdad.
