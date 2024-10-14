const express = require('express');
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const makeServiceCall = require('./circuitBreaker');

const app = express();
app.use(express.json());

// Load the protobuf
const packageDefinition = protoLoader.loadSync('service_discovery.proto');
const serviceDiscoveryProto = grpc.loadPackageDefinition(packageDefinition);

const servicesRegistry = {}

const getServices = (call, callback) => {
  const serviceEntries = Object.entries(servicesRegistry).map(([serviceName, instances]) => ({
      serviceName,
      serviceDetails: instances.map(instance => ({
          serviceAddress: instance.serviceAddress,
          servicePort: instance.servicePort
      }))
  }));
  const response = { services: serviceEntries };
  callback(null, response);
};

// Start gRPC server
function startGRPCServer() {
  const server = new grpc.Server();
  server.addService(serviceDiscoveryProto.ServiceInfo.service, { GetServices: getServices });
  server.bindAsync('0.0.0.0:5000', grpc.ServerCredentials.createInsecure(), () => {
    console.log('Service Discovery gRPC Server running on port 5000');
  });
};

app.post('/add-service', (req, res) => {
  try {
    const { name, address, port } = req.body;
    // Validate the input
    if (!name || !address || !port) {
      return res.status(400).send('Service name, address, and port are required');
    }

    if (servicesRegistry[name]) {
      const exists = servicesRegistry[name].some(service => 
        service.serviceAddress === address && service.servicePort === port
      );
      if (!exists) {
        servicesRegistry[name].push({ serviceAddress: address, servicePort: port });
      }
    } else {
      servicesRegistry[name] = [{ serviceAddress: address, servicePort: port }];
    }
    res.status(201).send('Service added to the registry');
  } catch(error) {
    console.log(error);
  }
});


app.get("/status", async (req, res) => {
  try {
      res.status(200).json({msg: "Service discovery is running!"});
  } catch {
      res.status(500).json({ msg: "Service discovery is down!"});
  };
});


// Health monitoring
setInterval(async () => {
  // Check each service
  for (const service in servicesRegistry) {
    for (let i = 0; i < servicesRegistry[service].length; i++) {
      const { serviceAddress, servicePort } = servicesRegistry[service][i];
      const response = await makeServiceCall(`${serviceAddress}:${servicePort}/status`, 'get');
      if (!response || response.status >= 300) {
        // Eliminate the server
        servicesRegistry[service].splice(i, 1)
        console.log(servicesRegistry)
        i--;
      }
    }
  }
}, 1000 * 5)


app.listen(3000, () => {
  console.log('Service Discovery HTTP Server running on port 3000');
  startGRPCServer();
});