const http = require('http');
const https = require('https');

function httpRequest({ method, url, data = null, timeout }) {
    return new Promise((resolve, reject) => {
        const parsed = new URL(url);
        const lib = parsed.protocol === 'https:' ? https : http;
        const payload = data != null ? JSON.stringify(data) : null;
        const options = { method: (method || 'get').toUpperCase(), headers: {} };
        if (payload != null) {
            options.headers['Content-Type'] = 'application/json';
            options.headers['Content-Length'] = Buffer.byteLength(payload);
        }
        const req = lib.request(parsed, options, (res) => {
            let chunks = '';
            res.on('data', (c) => { chunks += c; });
            res.on('end', () => {
                let body = chunks;
                try { body = chunks ? JSON.parse(chunks) : null; } catch (_) {}
                const result = { status: res.statusCode, data: body, headers: res.headers };
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    resolve(result);
                } else {
                    const error = new Error(`Request failed with status ${res.statusCode}`);
                    error.response = result;
                    reject(error);
                }
            });
        });
        if (timeout) {
            req.setTimeout(timeout, () => req.destroy(new Error(`timeout of ${timeout}ms exceeded`)));
        }
        req.on('error', reject);
        if (payload != null) req.write(payload);
        req.end();
    });
}


const TASK_TIMEOUT_LIMIT = 2000;
const RETRY_WINDOW = 3.5 * TASK_TIMEOUT_LIMIT;
async function makeServiceCall(url, method, data, retries = 3, delay = RETRY_WINDOW / 3 ) {
    for (let attempt = 0; attempt < retries; attempt++) {
        try {
            const response = await httpRequest({ method, url, data, timeout: TASK_TIMEOUT_LIMIT });
            return response; // If the request is successful, return the response
        } catch (error) {
            // Check if the error is a 5xx status code
            console.log(`Attempt ${attempt + 1} failed. Retrying...`);
            if (attempt < retries - 1) {
                await new Promise((resolve) => setTimeout(resolve, delay));
            }
        }
    }
    console.log("Circuit breaker tripped!");
    //throw new Error('Circuit breaker tripped!');
}

module.exports = makeServiceCall;