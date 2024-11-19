const client = require('prom-client')

function connectPrometheus(app) {
    // Create a Registry to register the metrics
    const register = new client.Registry();
    client.collectDefaultMetrics({
        app: 'gateway',
        timeout: 10000,
        gcDurationBuckets: [0.001, 0.01, 0.1, 1, 2, 5],
        register: register
    });

    // Create a histogram metric
    const httpRequestDurationMicroseconds = new client.Histogram({
        name: 'http_request_duration_seconds',
        help: 'Duration of HTTP requests in seconds',
        labelNames: ['method', 'route', 'code'],
        buckets: [0.1, 0.3, 0.5, 0.7, 1, 3, 5, 7, 10] // 0.1 to 10 seconds
    });
    register.registerMetric(httpRequestDurationMicroseconds);

    // Create a middleware to track request duration
    app.use((req, res, next) => {
        // Start the timer for each incoming request
        const end = httpRequestDurationMicroseconds.startTimer();
        // After the response is sent, record the request duration
        res.on('finish', () => {
        // Record the duration along with labels for method, route, and status code
        end({ route: req.route ? req.route.path : req.url, code: res.statusCode, method: req.method });
        });
        next(); // Continue processing the request
    });

    app.get('/metrics', async (req, res) => {
        res.setHeader('Content-Type', register.contentType);
        res.send(await register.metrics());
    });
};

module.exports = connectPrometheus;