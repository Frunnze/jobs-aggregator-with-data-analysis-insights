const express = require('express');
const rateLimit = require('express-rate-limit');
const dotenv = require('dotenv');
const lodash = require('lodash');

const { getServices } = require('./serviceDiscoveryGrpc');
const makeServiceCall = require('./circuitBreaker');
const connectPrometheus = require('./connectPrometheus');


const app = express();
app.use(express.json());

// Middleware to handle concurrent tasks limit
const limiter = rateLimit({
    windowMs: 5 * 1000, // 1 second
    max: 2,
    message: 'Too many requests!',
});
app.use(limiter);

// Connect prometheus
connectPrometheus(app);

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


// Wrapper for the makeServiceCall, which if the requests (3) fail
// it will send the requests again to N number of other service of the 
// same type
async function makePersistentServiceCall(serviceName, api, method, data = null, serviceCheckLimit = 2) {
    var serviceAddress, servicePort;
    var response;
    var firstRes;
    for (let i = 0; i < serviceCheckLimit; i++) {
        ({ serviceAddress, servicePort } = getServiceInfo(serviceName));
        if (i == 0) {
            addActiveReq(serviceAddress, servicePort);
        }
        response = await makeServiceCall(
            serviceName, serviceAddress, 
            servicePort, api, method, data
        );
        console.log("Checked service", i)

        // Check the response status
        // if 500 then try another service
        // otherwise you return the response
        if (response && response.status < 500) {
            console.log("Out service", i)
            subActiveReq(serviceAddress, servicePort);
            return response;
        };

        if (i == 0) {
            firstRes = response;
        };
    };
    subActiveReq(serviceAddress, servicePort);
    console.log("Circuit breaker tripped!");
    const error = new Error("Circuit breaker tripped!");
    error.details = {response: firstRes}
    throw error;
};

// Gateway routes
app.post('/sign-up', async (req, res) => {
    try {
        const response = await makePersistentServiceCall(
            "user-service",  "sign-up", "post", req.body
        );
        console.log("Received response:", response); // Log the response to see if it is truly a "user already exists" error
        res.status(response.status).json(response.data);
    } catch (error) {
        console.log("Error occurred:", error); // Log the error
        res.status(error.response?.status || 500).json({ msg: error.message });
    };
});

app.post('/login', async (req, res) => {
    try {
        const response = await makePersistentServiceCall(
            "user-service",  "login", "post", req.body
        );
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/get-subscriptions/:user_id', async (req, res) => {
    try {
        const response = await makePersistentServiceCall(
            "user-service",  `get-subscriptions/${req.params.user_id}`, 
            "get", req.body
        );
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/find-jobs', async (req, res) => {
    try {
        const response = await makePersistentServiceCall(
            "scraper-service",  `find-jobs?title=${req.query.title}`, 
            "get", req.body
        );
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/generate-insight-skills-by-demand/:keywords', async (req, res) => {
    try {
        const response = await makePersistentServiceCall(
            "scraper-service",  `generate-insight-skills-by-demand/${req.params.keywords}`, 
            'get', req.body
        );
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/all-skills-by-demand', async (req, res) => {
    try {
        const response = await makePersistentServiceCall(
            "scraper-service",  'all-skills-by-demand', 'get', req.body
        );
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    };
});

app.get('/skills-by-salary', async (req, res) => {
    try {
        const response = await makePersistentServiceCall(
            "scraper-service",  "skills-by-salary", 
            "get", req.body
        );
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    };
});

app.get('/average-job-salary', async (req, res) => {
    try {
        const response = await makePersistentServiceCall(
            "scraper-service",  "average-job-salary", 
            "get", req.body
        );
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    };
});

app.get('/generate-insight-average-experience/:keywords', async (req, res) => {
    try {
        const response = await makePersistentServiceCall(
            "scraper-service",  `generate-insight-average-experience/${req.params.keywords}`, 
            "get", req.body
        );
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    };
});

app.get("/status", async (req, res) => {
    try {
        res.status(200).json({msg: "Gateway is running!"});
    } catch {
        res.status(500).json({ msg: "Gateway is down!"});
    };
});


// Saga
app.post('/add-new-skill', async (req, res) => {
    const { user_id, skill_name } = req.body;

    if (!user_id || !skill_name) {
        return res.status(400).json({ error: "user_id and skill_name are required" });
    }

    let subscriptionId;
    let skillId;

    try {
        // Step 1: Add new subscription (user-service)
        const response = await makePersistentServiceCall(
            "user-service",  "add-new-subscription-skill", 
            "post", {user_id, skill_name}
        );
        subscriptionId = response.data.subscription_id;

        // Step 2: Add skill to the list (scraper-service)
        const skillResponse = await makePersistentServiceCall(
            "scraper-service",  "add-skill-to-list", 
            "post", {skill_name}
        );
        skillId = skillResponse.data.skill_id;

        return res.status(201).json({
            message: "Skill and subscription added successfully",
            subscription_id: subscriptionId,
            skill_id: skillId
        });
    } catch (error) {
        console.error("Saga failure: ", error.message);

        // Compensating transactions if any step fails
        if (!subscriptionId) {
            subscriptionId = error.details.response.data.subscriptionId;
        }
        if (subscriptionId) {
            try {
                await makePersistentServiceCall(
                    "user-service",  `delete-new-subscription-skill/${subscriptionId}`, 
                    "delete", null
                );
                console.log("Subscription compensating transaction executed successfully.");
            } catch (deleteError) {
                console.error("Failed to undo subscription: ", deleteError.message);
            }
        }

        if (!skillId) {
            skillId = error.details.response.data.skill_id;
        }
        if (skillId) {
            try {
                await makePersistentServiceCall(
                    "scraper-service",  `delete-skill-from-list/${skillId}`, 
                    "delete", null
                );
                console.log("Skill compensating transaction executed successfully.");
            } catch (deleteError) {
                console.error("Failed to undo skill addition: ", deleteError.message);
            }
        }

        return res.status(500).json({ error: "Saga transaction failed", details: error.message });
    }
});

// Start the server
const PORT = process.env.GATEWAY_PORT;
app.listen(PORT, async () => {
    console.log(`Gateway server running on port ${PORT}`);
    services = await getServices();
    console.log(services)
});