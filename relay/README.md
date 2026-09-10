# Relé de Transport BCN

Un Cloudflare Worker de 150 líneas que hace dos cosas que la app, al ser una web estática, no puede hacer sola:

1. **Tiempo real del bus de AMB.** La API de AMB (`/v1/stops/{parada}/realtimes`) da los próximos buses con destino y segundos hasta la llegada —el mismo dato que su app oficial—, pero tiene mal configurado el CORS: el preflight lo permite y la respuesta no lleva la cabecera, así que un navegador la bloquea. Además necesita una clave, que en una web pública quedaría a la vista de todos. El relé la guarda como **secreto** y nunca la envía al móvil.
2. **Pasarela para lo que no tiene CORS**: los ficheros GTFS-RT de AMB, el open data del TRAM y los horarios de Renfe. Hasta ahora pasaban por proxies públicos que se van muriendo.

Solo acepta peticiones desde `mr-d0nut.github.io` (y `localhost` para desarrollar) y solo reenvía a los hosts que usa la app: no es un proxy abierto. Guarda en caché 15 s cada parada, así que por mucha gente que mire la misma parada AMB recibe una petición cada 15 s.

Plan gratuito de Cloudflare: 100.000 peticiones al día. Una persona con la app abierta hace unas 3 por minuto.

## Desplegarlo (5 minutos, una sola vez)

### Opción A — desde el navegador, sin instalar nada

1. Entra en [dash.cloudflare.com](https://dash.cloudflare.com) (la cuenta gratuita basta).
2. **Workers & Pages → Create → Create Worker**. Nombre: `transport-bcn-relay`. **Deploy**.
3. **Edit code**: borra lo que hay, pega el contenido de [`worker.js`](worker.js) y **Deploy**.
4. En el worker: **Settings → Variables and Secrets → Add** → tipo **Secret**, nombre `AMB_API_KEY`, valor: tu clave de la API de AMB. **Deploy**.
5. Copia la URL del worker (algo como `https://transport-bcn-relay.TU-USUARIO.workers.dev`) y ponla en `index.html`:

   ```js
   const RELAY = … return 'https://transport-bcn-relay.TU-USUARIO.workers.dev';
   ```

### Opción B — desde la terminal

```bash
cd relay
npx wrangler login
npx wrangler deploy
npx wrangler secret put AMB_API_KEY
```

## Comprobar que funciona

Abre en el navegador `https://…workers.dev/` → debe decir `"clave": true`.

`https://…workers.dev/amb/stops/108741/realtimes` → los próximos buses del Hospital Esperit Sant (B2, B5, B14, B24, B81, M30).

## Probar la app contra un relé sin tocar el código

En la consola del navegador, sobre la app:

```js
localStorage.setItem('busbcn_relay', 'https://…workers.dev'); location.reload();
```

`localStorage.removeItem('busbcn_relay')` lo deshace.
