const express = require('express');
const axios = require('axios');
const rateLimit = require('express-rate-limit');
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');


// gRPC client setup for service discovery
const packageDefinition = protoLoader.loadSync('service_discovery.proto');
const serviceDiscoveryProto = grpc.loadPackageDefinition(packageDefinition);

// Adjust the client initialization
const client = new serviceDiscoveryProto.ServiceDiscovery('localhost:5000', grpc.credentials.createInsecure());

// Function to get service info dynamically
async function getServiceInfo(serviceName) {
  return new Promise((resolve, reject) => {
    client.GetServiceInfo({ serviceName }, (err, response) => {
      if (err) {
        return reject(err.details);
      }
      resolve(response);
    });
  });
}

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
        const { data } = await axios.post(`${serviceAddress}:${servicePort}/sign-up`, req.body);
        res.status(201).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.post('/login', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('user-service');
        console.log(serviceAddress, servicePort);
        const { data } = await axios.post(`${serviceAddress}:${servicePort}/login`, req.body);
        res.status(200).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/get-subscriptions/:user_id', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('user-service');
        const { data } = await axios.get(`${serviceAddress}:${servicePort}/get-subscriptions/${req.params.user_id}`);
        res.status(200).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/find-jobs', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('scraper-service');
        const { title } = req.query;
        const { data } = await axios.get(`${serviceAddress}:${servicePort}/find-jobs?title=${title}`);
        res.status(200).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/generate-insight-skills-by-demand/:keywords', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('scraper-service');
        const { data } = await axios.get(`${serviceAddress}:${servicePort}/generate-insight-skills-by-demand/${req.params.keywords}`);
        res.status(200).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/all-skills-by-demand', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('scraper-service');
        const { data } = await axios.get(`${serviceAddress}:${servicePort}/all-skills-by-demand`);
        res.status(200).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/skills-by-salary', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('scraper-service');
        const { data } = await axios.get(`${serviceAddress}:${servicePort}/skills-by-salary`);
        res.status(200).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/average-job-salary', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('scraper-service');
        const { data } = await axios.get(`${serviceAddress}:${servicePort}/average-job-salary`);
        res.status(200).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/generate-insight-average-experience/:keywords', async (req, res) => {
    try {
        const { serviceAddress, servicePort } = await getServiceInfo('scraper-service');
        const { data } = await axios.get(`${serviceAddress}:${servicePort}/generate-insight-average-experience/${req.params.keywords}`);
        res.status(200).json(data);
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
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
    console.log(`Gateway server running on port ${PORT}`);
});