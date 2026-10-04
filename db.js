// db.js - IndexedDB storage for massive JSONs to free up RAM
const DB_NAME = 'TransportDB';
const DB_VERSION = 1;

let db;
const dbPromise = new Promise((resolve, reject) => {
    if (!window.indexedDB) return resolve(null); // Silent fail
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onerror = () => resolve(null); // Silent fail on block
    request.onsuccess = () => { db = request.result; resolve(db); };
    request.onupgradeneeded = (e) => {
        const _db = e.target.result;
        if (!_db.objectStoreNames.contains('jsons')) {
            _db.createObjectStore('jsons');
        }
    };
}).catch(() => null);

async function setJSON(key, data) {
    const _db = await dbPromise;
    if (!_db) return; // DB not available, just ignore cache
    return new Promise((resolve) => {
        try {
            const tx = _db.transaction('jsons', 'readwrite');
            const store = tx.objectStore('jsons');
            const req = store.put(data, key);
            req.onsuccess = () => resolve();
            req.onerror = () => resolve(); // Ignore errors
        } catch(e) { resolve(); }
    });
}

async function getJSON(key) {
    const _db = await dbPromise;
    if (!_db) return null;
    return new Promise((resolve) => {
        try {
            const tx = _db.transaction('jsons', 'readonly');
            const store = tx.objectStore('jsons');
            const req = store.get(key);
            req.onsuccess = () => resolve(req.result);
            req.onerror = () => resolve(null);
        } catch(e) { resolve(null); }
    });
}

window.DB = { setJSON, getJSON };
