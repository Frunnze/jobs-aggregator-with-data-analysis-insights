# Use the official Node.js image as the base image
FROM node:14

# Set the working directory in the container
WORKDIR /usr/src/app

# Initialize npm and install dependencies
RUN npm init -y
RUN npm install express axios dotenv @grpc/grpc-js @grpc/proto-loader

# Copy the rest of the application files
COPY . .

# Expose the port the app runs on
EXPOSE 3000

# Command to run the app
CMD ["node", "server.js"]