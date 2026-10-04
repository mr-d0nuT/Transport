const fs = require('fs');
let app = fs.readFileSync('app.js', 'utf8');

const workerInit = `
/* --- WEB WORKER (Cálculos pesados y JSON) --- */
const dataWorker = new Worker('worker.js');
const workerCallbacks = {};
let workerMsgId = 0;

dataWorker.onmessage = function(e) {
    const { id, results, error } = e.data;
    if (workerCallbacks[id]) {
        if (error) workerCallbacks[id].reject(new Error('Worker error'));
        else workerCallbacks[id].resolve(results);
        delete workerCallbacks[id];
    }
};

function fetchShardWorker(name) {
    return new Promise((resolve, reject) => {
        const id = ++workerMsgId;
        workerCallbacks[id] = { resolve, reject };
        dataWorker.postMessage({ id, type: 'FETCH_SHARD', data: { name } });
    });
}
`;

app = app.replace('// --- 1B. IDIOMAS ---', workerInit + '\n        // --- 1B. IDIOMAS ---');

app = app.replace(
    /tmbShardReq\.set\(name, fetch\(\`\.\/tmb-sched\/\$\{name\}\.json\`\)\s*\n\s*\.then\(r => r\.ok \? r\.json\(\) : null\)\s*\n\s*\.catch\(\(\) => null\)\);/m,
    "tmbShardReq.set(name, fetchShardWorker(name).catch(() => null));"
);

fs.writeFileSync('app.js', app);
