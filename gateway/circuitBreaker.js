const axios = require('axios');

const TASK_TIMEOUT_LIMIT = 2000;
const RETRY_WINDOW = 3.5 * TASK_TIMEOUT_LIMIT;
async function makeServiceCall(url, method, data, retries = 3, delay = RETRY_WINDOW / 3 ) {
    for (let attempt = 0; attempt < retries; attempt++) {
        try {
            const response = await axios({ method, url, data, timeout: TASK_TIMEOUT_LIMIT });
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
    throw new Error('Circuit breaker tripped!');
}

module.exports = makeServiceCall;