// Relé de Transport BCN — Cloudflare Worker (gratis hasta 100.000 peticiones/día)
//
// Por qué existe: la app es una web estática y hay fuentes que un navegador no
// puede leer directamente.
//   · API de AMB (tiempo real del bus metropolitano): el preflight da CORS pero
//     la respuesta del GET no lleva la cabecera, así que el navegador la bloquea.
//     Además necesita la clave, que no debe ir en una web pública: aquí vive
//     como secreto del worker (AMB_API_KEY) y nunca sale hacia el móvil.
//   · Ficheros GTFS-RT de AMB, open data del TRAM y horarios de Renfe: sin CORS.
//     Hasta ahora pasaban por proxies públicos que se van muriendo.
//
// Rutas:
//   GET  /amb/stops/{código}/realtimes  → próximos buses de una parada de AMB
//   GET  /?url={https://…}              → pasarela GET a un host de la lista
//   POST /?url={https://…}              → pasarela POST (horarios de Renfe)
//
// Despliegue: ver relay/README.md

const AMB_API = 'https://api.ambmobilitat.cat/v1';

// Quién puede usar el relé desde un navegador. Sin esta lista cualquier web
// podría gastar la cuota de la clave.
const ORIGENES = [
    /^https:\/\/mr-d0nut\.github\.io$/i,
    /^http:\/\/localhost(:\d+)?$/,
    /^http:\/\/127\.0\.0\.1(:\d+)?$/
];

// A dónde se puede ir por la pasarela: solo lo que usa la app, para que esto
// no sea un proxy abierto.
const HOSTS = new Set([
    'www.ambmobilitat.cat',
    'opendata.tram.cat',
    'horarios.renfe.com',
    'gtfsrt.renfe.com'
]);

const TTL = { realtimes: 15, paso: 20 }; // segundos

function cabecerasCors(origen) {
    const ok = origen && ORIGENES.some(r => r.test(origen));
    return {
        'Access-Control-Allow-Origin': ok ? origen : 'https://mr-d0nut.github.io',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '86400',
        'Vary': 'Origin'
    };
}

function json(obj, status, cors) {
    return new Response(JSON.stringify(obj), {
        status, headers: { ...cors, 'Content-Type': 'application/json; charset=utf-8' }
    });
}

// Caché en memoria del propio worker: con varios usuarios mirando la misma
// parada, AMB recibe una petición cada 15 s y no una por persona. (La Cache API
// de Cloudflare no guarda nada en los subdominios workers.dev.)
const MEM = new Map();
async function cacheado(clave, ttl, producir) {
    const hit = MEM.get(clave);
    if (hit && hit.exp > Date.now()) {
        return new Response(hit.cuerpo, { status: hit.status, headers: hit.cabeceras });
    }
    const res = await producir();
    const cuerpo = await res.arrayBuffer();
    const cabeceras = { 'Content-Type': res.headers.get('Content-Type') || 'application/octet-stream' };
    if (res.ok) {
        MEM.set(clave, { exp: Date.now() + ttl * 1000, status: res.status, cabeceras, cuerpo });
        if (MEM.size > 800) MEM.delete(MEM.keys().next().value);
    }
    return new Response(cuerpo, { status: res.status, headers: cabeceras });
}

async function ambRealtimes(codigo, env) {
    const r = await fetch(`${AMB_API}/stops/${codigo}/realtimes`, {
        headers: { 'x-api-key': env.AMB_API_KEY, 'Accept': 'application/json' }
    });
    // 204: la parada no tiene buses previstos ahora mismo
    if (r.status === 204) {
        return new Response('{"times":[]}', { status: 200, headers: { 'Content-Type': 'application/json' } });
    }
    return r;
}

export default {
    async fetch(request, env, ctx) {
        const cors = cabecerasCors(request.headers.get('Origin') || '');
        if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
        if (request.method !== 'GET' && request.method !== 'POST') return json({ error: 'método no permitido' }, 405, cors);

        const url = new URL(request.url);
        let res;
        try {
            const m = url.pathname.match(/^\/amb\/stops\/(\d{1,7})\/realtimes$/);
            if (m) {
                if (!env.AMB_API_KEY) return json({ error: 'falta el secreto AMB_API_KEY' }, 500, cors);
                const codigo = String(parseInt(m[1], 10)); // la API usa el código sin ceros delante
                res = await cacheado('rt:' + codigo, TTL.realtimes, () => ambRealtimes(codigo, env));
            } else if (url.searchParams.has('url')) {
                let destino;
                try { destino = new URL(url.searchParams.get('url')); } catch { return json({ error: 'url no válida' }, 400, cors); }
                if (destino.protocol !== 'https:' || !HOSTS.has(destino.hostname)) {
                    return json({ error: 'destino no permitido' }, 403, cors);
                }
                if (request.method === 'POST') {
                    res = await fetch(destino.href, {
                        method: 'POST', body: await request.text(),
                        headers: { 'Content-Type': request.headers.get('Content-Type') || 'application/json' }
                    });
                } else {
                    res = await cacheado('paso:' + destino.href, TTL.paso,
                        () => fetch(destino.href, { headers: { 'User-Agent': 'transport-bcn-relay/1.0' } }));
                }
            } else {
                return json({ ok: true, servicio: 'Relé de Transport BCN', clave: !!env.AMB_API_KEY }, 200, cors);
            }
        } catch (e) {
            return json({ error: 'origen caído: ' + e.message }, 502, cors);
        }

        const out = new Response(res.body, res);
        Object.entries(cors).forEach(([k, v]) => out.headers.set(k, v));
        out.headers.set('Cache-Control', 'no-store'); // la frescura la manda la app
        return out;
    }
};
