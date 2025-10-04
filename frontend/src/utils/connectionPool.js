/**
 * Connection Pool for Better Reliability
 * Implements connection pooling and retry logic for the single backend
 */

class ConnectionPool {
  constructor() {
    this.baseUrl = 'https://prepandhirebackend.onrender.com';
    this.maxRetries = 3;
    this.retryDelay = 1000;
    this.timeout = 15000;
    this.connectionCount = 0;
    this.maxConnections = 5;
  }

  /**
   * Make a request with connection pooling and retry logic
   */
  async makeRequest(endpoint, options = {}) {
    // Check connection limit
    if (this.connectionCount >= this.maxConnections) {
      console.log('🔄 Connection pool full, queuing request...');
      await this.waitForConnection();
    }

    this.connectionCount++;
    
    try {
      return await this.executeRequest(endpoint, options);
    } finally {
      this.connectionCount--;
    }
  }

  /**
   * Execute the actual request with retry logic
   */
  async executeRequest(endpoint, options = {}) {
    let lastError;

    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        const url = `${this.baseUrl}${endpoint}`;
        
        console.log(`🔄 Connection Pool: Attempt ${attempt + 1}/${this.maxRetries} to ${url}`);
        
        // Create AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        const response = await fetch(url, {
          ...options,
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        if (response.ok) {
          console.log(`✅ Connection Pool: Success on attempt ${attempt + 1}`);
          return response;
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
      } catch (error) {
        console.warn(`⚠️ Connection Pool: Attempt ${attempt + 1} failed:`, error.message);
        lastError = error;
        
        // Wait before retry with exponential backoff
        if (attempt < this.maxRetries - 1) {
          const delay = this.retryDelay * Math.pow(2, attempt);
          console.log(`⏳ Retrying in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    throw new Error(`All retry attempts failed. Last error: ${lastError?.message}`);
  }

  /**
   * Wait for a connection to become available
   */
  async waitForConnection() {
    return new Promise((resolve) => {
      const checkConnection = () => {
        if (this.connectionCount < this.maxConnections) {
          resolve();
        } else {
          setTimeout(checkConnection, 100);
        }
      };
      checkConnection();
    });
  }

  /**
   * Get connection pool status
   */
  getStatus() {
    return {
      activeConnections: this.connectionCount,
      maxConnections: this.maxConnections,
      baseUrl: this.baseUrl,
      isHealthy: this.connectionCount < this.maxConnections
    };
  }
}

// Create singleton instance
const connectionPool = new ConnectionPool();

export default connectionPool;
