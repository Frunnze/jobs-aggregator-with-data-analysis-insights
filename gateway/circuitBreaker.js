const { deleteService } = require('./serviceDiscoveryGrpc');
const { response } = require('express');

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


const TASK_TIMEOUT_LIMIT = 5000;
const RETRY_WINDOW = 3.5 * TASK_TIMEOUT_LIMIT;
async function makeServiceCall(serviceName, serviceAddress, servicePort, api, method, data = null, retries = 3, delay = RETRY_WINDOW / 3 ) {
    const url = `${serviceAddress}:${servicePort}/${api}`; 
    let response;

    for (let attempt = 0; attempt < retries; attempt++) {
        try {
            response = await httpRequest({
                method: method,
                url: url,
                data: data,
                //timeout: TASK_TIMEOUT_LIMIT
            });
            return response;  // Return the response if the call is successful
        }
        catch (error) {
            //console.log("FAIL", error)
            // Check if the error has a response and its status
            if (error.response && error.response.status < 500) {
                return error.response;
            } else {
                // Log the error and prepare to retry
                console.log("Response, ", error.response.data)
                console.log(`Attempt ${attempt + 1} failed with status ${error.response ? error.response.status : 'unknown'}. Retrying...`);
                await new Promise((resolve) => setTimeout(resolve, delay));
            };
            if (attempt == 0) {
                response = error.response;
            }
            if (attempt + 1 == retries) {
                return response;
            };
        }
    }
    //console.log("Circuit breaker tripped!");
    //await deleteService(serviceName, serviceAddress, servicePort);
    //throw new Error('Circuit breaker tripped!');
};

module.exports = makeServiceCall;