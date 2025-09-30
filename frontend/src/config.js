// Configuration for different environments
const config = {
  development: {
    API_BASE_URL: 'http://localhost:8000',
    WS_BASE_URL: 'ws://localhost:8000',
  },
  production: {
    API_BASE_URL: 'https://prepandhire-backend.onrender.com',
    WS_BASE_URL: 'wss://prepandhire-backend.onrender.com',
  }
};

// Determine environment
const environment = process.env.NODE_ENV === 'production' ? 'production' : 'development';

// Export current environment config
export default config[environment];
