// db.js - IndexedDB storage for massive JSONs to free up RAM
const DB_NAME = 'TransportDB';
const DB_VERSION = 1;

let db;
const dbPromise = new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => { db = request.result; resolve(db); };
    request.onupgradeneeded = (e) => {
        const _db = e.target.result;
        if (!_db.objectStoreNames.contains('jsons')) {
            _db.createObjectStore('jsons');
        }
    };
});

async function setJSON(key, data) {
    const _db = await dbPromise;
    return new Promise((resolve, reject) => {
        const tx = _db.transaction('jsons', 'readwrite');
        const store = tx.objectStore('jsons');
        const req = store.put(data, key);
        req.onsuccess = () => resolve();
        req.onerror = () => reject(req.error);
    });
}

async function getJSON(key) {
    const _db = await dbPromise;
    return new Promise((resolve, reject) => {
        const tx = _db.transaction('jsons', 'readonly');
        const store = tx.objectStore('jsons');
        const req = store.get(key);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
    });
}

window.DB = { setJSON, getJSON };
