# Diseño: la línea de tiempo de llegadas y la cinta del viaje

Fecha: 2026-08-24

Dos vistas nuevas que no son adorno: enseñan algo que la lista de tarjetas
escondía.

## 1. Línea de tiempo de llegadas

Una lista dice *cuándo* pasa cada bus. Lo que no dice es la **forma** de la
espera: que hay tres en siete minutos y luego media hora en blanco, o que el
primero no lo pillas ni corriendo.

Sobre una regla de tiempo, cada salida es una pastilla del color de su línea
colocada en su minuto:

- **La escala se ajusta sola** a 15, 30 o 60 minutos según lo que haya.
- Las pastillas se reparten en **filas** para no pisarse (hasta donde haga falta).
- Si la app sabe a qué distancia estás (parada abierta desde "cerca de mí"), la
  franja inicial va **rayada**: es lo que tardas en llegar andando. Las salidas
  que caen dentro se ven apagadas y con un 🏃: **esas no las coges**.
- Tocar una pastilla despliega el recorrido de esa línea, igual que la tarjeta.

Solo aparece con dos o más salidas: con una, la propia tarjeta ya lo dice todo.

## 2. Cinta del viaje, a escala

La tira de iconos (`🚶6' › 87 › 🚶3' › L3 › 🚶5'`) dice el orden, pero no las
proporciones, y **escondía las esperas**: un enlace de 8 minutos parado en la
parada no se veía por ningún sitio.

La cinta dibuja el viaje entero **a escala de tiempo**: cada tramo ocupa lo que
dura, con el color oficial de la línea, las caminatas rayadas en gris y **las
esperas rayadas en ámbar**. Debajo, la hora de salida, la de llegada y los
totales: 🚶 22' a pie · ⏳ 3' esperando.

De un vistazo se distingue una ruta que es "5 minutos de metro y 20 andando" de
otra que es "todo en bus", sin leer un número.

Se mantiene la tira de iconos encima porque en los tramos estrechos la cinta no
puede escribir el nombre de la línea; las dos juntas se complementan.
