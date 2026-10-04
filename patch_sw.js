const fs = require('fs');
let sw = fs.readFileSync('sw.js', 'utf8');

// Replace the simple fetch handler with a SWR handler
const fetchHandler = `
self.addEventListener('fetch', e => {
    const url = new URL(e.request.url);
    
    // Si es una llamada a las APIs (TMB, TRAM, Overpass), aplicamos Stale-While-Revalidate
    if (url.hostname.includes('api.tmb.cat') || url.hostname.includes('overpass-api.de') || url.hostname.includes('tram.cat')) {
        e.respondWith(
            caches.open('transport-bcn-api-cache').then(cache => {
                return cache.match(e.request).then(cachedResponse => {
                    const fetchPromise = fetch(e.request).then(networkResponse => {
                        cache.put(e.request, networkResponse.clone());
                        return networkResponse;
                    }).catch(() => {
                        // Si falla la red, ya devolvimos caché (si había)
                    });
                    
                    // Devuelve caché al instante si existe, si no, espera a la red
                    return cachedResponse || fetchPromise;
                });
            })
        );
        return;
    }

    // Para estáticos locales (HTML, CSS, JS, etc), Cache First estándar
    e.respondWith(
        caches.match(e.request).then(r => r || fetch(e.request))
    );
});
`;

sw = sw.replace(/self\.addEventListener\('fetch'[\s\S]*\}\);/, fetchHandler.trim());
fs.writeFileSync('sw.js', sw);
