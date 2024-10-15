const express = require('express');
const rateLimit = require('express-rate-limit');
const dotenv = require('dotenv');
const lodash = require('lodash');

const { getServices } = require('./serviceDiscoveryGrpc');
const makeServiceCall = require('./circuitBreaker');


dotenv.config();

let services = {}


// Alert in case of critical load
const SERVICE_LOAD_LIMIT = 1;
function alertCriticalLoad() {
    for (const service in services) {
        if (!services[service]) return;
        for (const serviceData of services[service]) {
            const { serviceAddress, servicePort } = serviceData;
            const HOST = `${serviceAddress}:${servicePort}`;
            const load = serviceLoadData[HOST];
            if (load >= SERVICE_LOAD_LIMIT) {
                console.log(`ALERT: Service ${service} - ${HOST} is overloaded. Active requests: ${load}!`);
            }
        };
    };
};

// Check if there are new services
setInterval(async () => {
    const newServices = await getServices();
    if (!lodash.isEqual(newServices, services)){
        services = newServices;
    }
    console.log(services);
    alertCriticalLoad();
}, 1000 * 5)

// Load balancer
var roundRobinInd = {};
var serviceLoadData = {};
//var loadType = "roundRobin"; // serviceLoad
var loadType = "roundRobin";
function getServiceInfo(serviceName) {
    let serviceToReturn = null;
    if (loadType === "roundRobin") {
        if (!(serviceName in roundRobinInd)) {
            roundRobinInd[serviceName] = 0;
        }
        //console.log(roundRobinInd)
        for (let i = 0; i < services[serviceName].length; i++) {
            if (roundRobinInd[serviceName] == i) {
                serviceToReturn = services[serviceName][i];
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
        serviceToReturn = services[serviceName][minLoadService];
    }
    return serviceToReturn;
};

function addActiveReq(serviceAddress, servicePort) {
    const HOST = `${serviceAddress}:${servicePort}`;
    if (HOST in serviceLoadData) {
        serviceLoadData[HOST] += 1
    } else {
        serviceLoadData[HOST] = 1
    };
};

function subActiveReq(serviceAddress, servicePort) {
    if (serviceAddress && servicePort) {
        serviceLoadData[`${serviceAddress}:${servicePort}`] -= 1
    };
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
    let serviceAddress, servicePort;
    try {
        const serviceName = 'user-service';
        ({ serviceAddress, servicePort } = await getServiceInfo(serviceName));
        addActiveReq(serviceAddress, servicePort);

        const response = await makeServiceCall(
            serviceName, serviceAddress, 
            servicePort, "sign-up", 'post', req.body
        );
        res.status(201).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    } finally {
        subActiveReq(serviceAddress, servicePort);
    }
});

app.post('/login', async (req, res) => {
    let serviceAddress, servicePort;
    try {
        const serviceName = 'user-service';
        ({ serviceAddress, servicePort } = await getServiceInfo(serviceName));
        addActiveReq(serviceAddress, servicePort);
        console.log(serviceLoadData);

        const response = await makeServiceCall(
            serviceName, serviceAddress, 
            servicePort, "login", 'post', req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    } finally {
        subActiveReq(serviceAddress, servicePort);
        console.log(serviceLoadData);
    }
});

app.get('/get-subscriptions/:user_id', async (req, res) => {
    let serviceAddress, servicePort;
    try {
        const serviceName = 'user-service';
        ({ serviceAddress, servicePort } = await getServiceInfo(serviceName));
        addActiveReq(serviceAddress, servicePort);

        const response = await makeServiceCall(
            serviceName, serviceAddress, servicePort, 
            `get-subscriptions/${req.params.user_id}`, 'get', req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    } finally {
        subActiveReq(serviceAddress, servicePort);
    }
});

app.get('/find-jobs', async (req, res) => {
    let serviceAddress, servicePort;
    try {
        const serviceName = 'scraper-service';
        ({ serviceAddress, servicePort } = await getServiceInfo(serviceName));
        addActiveReq(serviceAddress, servicePort);
        const { title } = req.query;
        const response = await makeServiceCall(
            serviceName, serviceAddress, servicePort, 
            `find-jobs?title=${title}`, 
            'get', req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    } finally {
        subActiveReq(serviceAddress, servicePort);
    }
});

app.get('/generate-insight-skills-by-demand/:keywords', async (req, res) => {
    let serviceAddress, servicePort;
    try {
        const serviceName = 'scraper-service';
        ({ serviceAddress, servicePort } = await getServiceInfo(serviceName));
        addActiveReq(serviceAddress, servicePort);

        const response = await makeServiceCall(
            serviceName, serviceAddress, servicePort, 
            `generate-insight-skills-by-demand/${req.params.keywords}`, 
            'get', req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    } finally {
        subActiveReq(serviceAddress, servicePort);
    }
});

app.get('/all-skills-by-demand', async (req, res) => {
    let serviceAddress, servicePort;
    try {
        const serviceName = 'scraper-service';
        ({ serviceAddress, servicePort } = await getServiceInfo(serviceName));
        addActiveReq(serviceAddress, servicePort);

        const response = await makeServiceCall(
            serviceName, serviceAddress, servicePort, 
            'all-skills-by-demand', 'get', req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    } finally {
        subActiveReq(serviceAddress, servicePort);
    };
});

app.get('/skills-by-salary', async (req, res) => {
    let serviceAddress, servicePort;
    try {
        const serviceName = 'scraper-service';
        ({ serviceAddress, servicePort } = await getServiceInfo(serviceName));
        addActiveReq(serviceAddress, servicePort);

        const response = await makeServiceCall(
            serviceName, serviceAddress, servicePort, 
            `skills-by-salary`, 
            'get', req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    } finally {
        subActiveReq(serviceAddress, servicePort);
    };
});

app.get('/average-job-salary', async (req, res) => {
    let serviceAddress, servicePort;
    try {
        const serviceName = 'scraper-service';
        ({ serviceAddress, servicePort } = await getServiceInfo(serviceName));
        addActiveReq(serviceAddress, servicePort);

        const response = await makeServiceCall(
            serviceName, serviceAddress, servicePort, 
            `average-job-salary`, 
            'get', req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    } finally {
        subActiveReq(serviceAddress, servicePort);
    };
});

app.get('/generate-insight-average-experience/:keywords', async (req, res) => {
    let serviceAddress, servicePort;
    try {
        const serviceName = 'scraper-service';
        ({ serviceAddress, servicePort } = await getServiceInfo(serviceName));
        addActiveReq(serviceAddress, servicePort);

        const response = await makeServiceCall(
            serviceName, serviceAddress, servicePort, 
            `generate-insight-average-experience/${req.params.keywords}`, 
            'get', req.body
        );
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    } finally {
        subActiveReq(serviceAddress, servicePort);
    };
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