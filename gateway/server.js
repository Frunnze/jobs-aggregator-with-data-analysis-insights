const express = require('express');
const rateLimit = require('express-rate-limit');
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const dotenv = require('dotenv');
const lodash = require('lodash');

const makeServiceCall = require('./circuitBreaker');


dotenv.config();

let services = {}

// gRPC client setup for service discovery
const packageDefinition = protoLoader.loadSync('service_discovery.proto');
const serviceDiscoveryProto = grpc.loadPackageDefinition(packageDefinition);

// Adjust the client initialization
const client = new serviceDiscoveryProto.ServiceInfo(
    process.env.SERVICE_DISCOVERY_HOST, 
    grpc.credentials.createInsecure()
);

// Function to get service info dynamically
async function getServices() {
    return new Promise((resolve, reject) => {
        client.GetServices({}, (error, response) => {
            if (error) {
                console.error("gRPC Error:", error);
                return reject(error);
            }
            // Map response to service info
            if (response && response.services) {
                const serviceMap = response.services.reduce((acc, serviceEntry) => {
                    acc[serviceEntry.serviceName] = serviceEntry.serviceDetails;
                    return acc;
                }, {});

                resolve(serviceMap);
            } else {
                reject(new Error("No services found in response."));
            }
        });
    });
}

// Check if there are new services
setInterval(async () => {
    const newServices = await getServices();
    if (!lodash.isEqual(newServices, services)){
        services = newServices;
    }
    //console.log(services);
}, 1000 * 5)

// Load balancer
var roundRobinInd = {};
var serviceLoadData = {};
//var loadType = "roundRobin"; // serviceLoad
var loadType = "serviceLoad";
function getServiceInfo(serviceName) {
    if (loadType === "roundRobin") {
        if (!(serviceName in roundRobinInd)) {
            roundRobinInd[serviceName] = 0;
        }
        //console.log(roundRobinInd)
        for (let i = 0; i < services[serviceName].length; i++) {
            if (roundRobinInd[serviceName] == i) {
                return services[serviceName][i];
            };
        };
        roundRobinInd[serviceName] += 1;
        if (roundRobinInd[serviceName] == services[serviceName].length) {
            roundRobinInd[serviceName] = 0;
        };
    } else 
    if (loadType === "serviceLoad") {
        let minLoadService = 0;
        let minLoad = Infinity;
        for (let i = 0; i < services[serviceName].length; i++) {
            const { serviceAddress, servicePort } = services[serviceName][i];
            const host = `${serviceAddress}:${servicePort}`
            if (!(host in serviceLoadData)) {
                serviceLoadData[host] = 0;
            };
            if (serviceLoadData[host] < minLoad) {
                minLoad = serviceLoadData[host];
                minLoadService = i;
            }
        }
        return services[serviceName][minLoadService];
    }
};

const app = express();
app.use(express.json());

// Middleware to handle concurrent tasks limit
const limiter = rateLimit({
    windowMs: 5 * 1000, // 1 second
    max: 2,
    message: 'Too many requests!',
});

// Apply the rate limit middleware to all requests
app.use(limiter);

// Gateway routes
app.post('/sign-up', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('user-service');
        const response = await makeServiceCall(`${serviceAddress}:${servicePort}/sign-up`, 'post', req.body);
        res.status(201).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.post('/login', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('user-service');
        console.log(serviceAddress, servicePort);
        const response = await makeServiceCall(`${serviceAddress}:${servicePort}/login`, 'post', req.body);
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/get-subscriptions/:user_id', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('user-service');
        const response = await makeServiceCall(
            `${serviceAddress}:${servicePort}/get-subscriptions/${req.params.user_id}`, 
            'get', 
            req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/find-jobs', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('scraper-service');
        const { title } = req.query;
        const response = await makeServiceCall(
            `${serviceAddress}:${servicePort}/find-jobs?title=${title}`, 
            'get', 
            req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/generate-insight-skills-by-demand/:keywords', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('scraper-service');
        const response = await makeServiceCall(
            `${serviceAddress}:${servicePort}/generate-insight-skills-by-demand/${req.params.keywords}`, 
            'get', 
            req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/all-skills-by-demand', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('scraper-service');
        const response = await makeServiceCall(
            `${serviceAddress}:${servicePort}/all-skills-by-demand`, 
            'get', 
            req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/skills-by-salary', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('scraper-service');
        const response = await makeServiceCall(
            `${serviceAddress}:${servicePort}/skills-by-salary`, 
            'get', 
            req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/average-job-salary', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('scraper-service');
        const response = await makeServiceCall(
            `${serviceAddress}:${servicePort}/average-job-salary`, 
            'get', 
            req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/generate-insight-average-experience/:keywords', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('scraper-service');
        const response = await makeServiceCall(
            `${serviceAddress}:${servicePort}/generate-insight-average-experience/${req.params.keywords}`, 
            'get', 
            req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get("/status", async (req, res) => {
    try {
        res.status(200).json({msg: "Gateway is running!"});
    } catch {
        res.status(500).json({ msg: "Gateway is down!"});
    };
});

// Start the server
const PORT = process.env.GATEWAY_PORT;
app.listen(PORT, async () => {
    console.log(`Gateway server running on port ${PORT}`);
    services = await getServices();
    console.log(services)
});