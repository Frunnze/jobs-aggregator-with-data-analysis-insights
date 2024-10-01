const express = require('express');
const axios = require('axios');
const rateLimit = require('express-rate-limit');

const app = express();
app.use(express.json());

// Configuration
const SERVICE1_URL = process.env.USER_SERVICE_URL;
const SERVICE2_URL =  process.env.SCRAPER_SERVICE_URL;

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
        const { data } = await axios.post(`${SERVICE1_URL}/sign-up`, req.body);
        res.status(201).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.post('/login', async (req, res) => {
    try {
        const { data } = await axios.post(`${SERVICE1_URL}/login`, req.body);
        res.status(200).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/get-subscriptions/:user_id', async (req, res) => {
    try {
        const { data } = await axios.get(`${SERVICE1_URL}/get-subscriptions/${req.params.user_id}`);
        res.status(200).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/find-jobs', async (req, res) => {
    try {
        const { title } = req.query;
        const { data } = await axios.get(`${SERVICE2_URL}/find-jobs?title=${title}`);
        res.status(200).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/generate-insight-skills-by-demand/:keywords', async (req, res) => {
    try {
        const { data } = await axios.get(`${SERVICE2_URL}/generate-insight-skills-by-demand/${req.params.keywords}`);
        res.status(200).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/all-skills-by-demand', async (req, res) => {
    try {
        const { data } = await axios.get(`${SERVICE2_URL}/all-skills-by-demand`);
        res.status(200).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/generate-insight-average-experience/:keywords', async (req, res) => {
    try {
        const { data } = await axios.get(`${SERVICE2_URL}/generate-insight-average-experience/${req.params.keywords}`);
        res.status(200).json(data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ msg: error.message });
    }
});

app.get('/status', async (req, res) => {
    try {
        const service1Status = await axios.get(`${SERVICE1_URL}/status`);
        const service2Status = await axios.get(`${SERVICE2_URL}/status`);
        res.status(200).json({
            service1: service1Status.data,
            service2: service2Status.data,
        });
    } catch (error) {
        res.status(500).json({ msg: 'One or more services are down.' });
    }
});

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Gateway server running on port ${PORT}`);
});