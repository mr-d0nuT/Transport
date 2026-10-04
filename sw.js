// Service worker de Som-hi!: cachea la carcasa de la app para que
// arranque al instante y funcione la interfaz sin red. Los datos en tiempo
// real (TMB, TRAM, Overpass) y los tiles del mapa NUNCA se cachean.
const CACHE = 'transport-bcn-v90';
const SHELL = ['./', './index.html', './styles.css', './app.js', './worker.js', './db.js', './icon-192.png', './favicon-64.png', './manifest.webmanifest', './assets/mark-donut.png'];

self.addEventListener('install', e => {
    e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).catch(() => {}));
    self.skipWaiting();
});

self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
            .then(() => self.clients.claim())
    );
});

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
