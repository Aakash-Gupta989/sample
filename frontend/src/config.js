// Configuration for different environments
const config = {
  development: {
    API_BASE_URL: 'http://localhost:8000',
    WS_BASE_URL: 'ws://localhost:8000',
  },
  production: {
    API_BASE_URL: 'https://prepandhirebackend.onrender.com',
    WS_BASE_URL: 'wss://prepandhirebackend.onrender.com',
  }
};

// Determine environment - force production for Vercel deployment
const environment = (process.env.NODE_ENV === 'production' || process.env.VERCEL) ? 'production' : 'development';

// Debug logging
console.log('🔧 Environment detection:', {
  NODE_ENV: process.env.NODE_ENV,
  VERCEL: process.env.VERCEL,
  selectedEnvironment: environment,
  config: config[environment]
});

// Export current environment config
export default config[environment];
