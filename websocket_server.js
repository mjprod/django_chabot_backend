const https = require('https');
const fs = require('fs');
const WebSocket = require('ws');

// Paths to your SSL certificate and private key
const SSL_CERT_PATH = '/home/ubuntu/certs/fullchain.pem';
const SSL_KEY_PATH = '/home/ubuntu/certs/privkey.pem';

// Create an HTTPS server with SSL credentials
const server = https.createServer({
  cert: fs.readFileSync(SSL_CERT_PATH), // Load SSL certificate
  key: fs.readFileSync(SSL_KEY_PATH), // Load private key
});

// Create a WebSocket server attached to the HTTPS server
const wss = new WebSocket.Server({ server });

// Function to broadcast a message to all connected clients
const broadcastMessage = (message, senderSocket) => {
  wss.clients.forEach((client) => {
    if (client !== senderSocket && client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(message)); // Broadcast the JSON message
    }
  });
};

// Handle WebSocket connections
wss.on('connection', (socket) => {
  console.log('New client connected');

  // Handle messages from clients
  socket.on('message', (data) => {
    try {
      // Parse the received data as JSON
      const message = JSON.parse(data);
      console.log('Received:', message);

      // Broadcast the message to all other clients
      broadcastMessage(message, socket);
    } catch (error) {
      console.error('Failed to parse message as JSON:', error);

      // Send an error response to the sender
      socket.send(
        JSON.stringify({
          error: 'Invalid message format. Expected JSON.',
        })
      );
    }
  });

  // Handle client disconnection
  socket.on('close', () => {
    console.log('Client disconnected');
  });

  // Handle connection errors
  socket.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
});

// Start the HTTPS server and WebSocket server
const PORT = 8081; // Define the port to listen on
server.listen(PORT, () => {
  console.log(
    `Secure WebSocket server running at wss://api.mjproapps.com:${PORT}`
  );
});
