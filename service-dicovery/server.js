const express = require('express');
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const axios = require('axios');

const app = express();
app.use(express.json());

// Load the protobuf
const packageDefinition = protoLoader.loadSync('service_discovery.proto');
const serviceDiscoveryProto = grpc.loadPackageDefinition(packageDefinition);

// In-memory service registry (for simplicity)
const servicesRegistry = {}

function getServiceData(serviceName) {
  const instances = servicesRegistry[serviceName];
  if (instances.length > 0) {
    return instances[0];
  }
}

// gRPC implementation
function GetServiceInfo(call, callback) {
  const serviceName = call.request.serviceName;
  const service = getServiceData(serviceName);
  console.log("GOT SERVICE:", service);
  if (service) {
    callback(null, {
      serviceAddress: service.address,
      servicePort: service.port
    });
  } else {
    callback({
      code: grpc.status.NOT_FOUND,
      details: "Service not found"
    });
  }
}

// Start gRPC server
function startGRPCServer() {
  const server = new grpc.Server();
  server.addService(serviceDiscoveryProto.ServiceDiscovery.service, { GetServiceInfo });
  server.bindAsync('0.0.0.0:5000', grpc.ServerCredentials.createInsecure(), () => {
    console.log('Service Discovery gRPC Server running on port 5000');
  });
}


app.post('/add-service', (req, res) => {
  const { name, address, port } = req.body;

  // Validate the input
  if (!name || !address || !port) {
    return res.status(400).send('Service name, address, and port are required');
  }

  if (servicesRegistry[name]) {
    const exists = servicesRegistry[name].some(service => 
      service.address === address && service.port === port
    );
    if (!exists) {
      servicesRegistry[name].push({ address, port });
    }
  } else {
    servicesRegistry[name] = [{ address, port }];
  }
  console.log(servicesRegistry)
  res.status(201).send('Service added to the registry');
});


app.get("/status", async (req, res) => {
  try {
      res.status(200).json({msg: "Service discovery is running!"});
  } catch {
      res.status(500).json({ msg: "Service discovery is down!"});
  };
});


app.listen(3000, () => {
  console.log('Service Discovery HTTP Server running on port 3000');
  startGRPCServer();
});