/**
 * Load Balancer Utility for Multiple Backend Instances
 * Provides automatic failover and load distribution
 */

class LoadBalancer {
  constructor() {
    this.backends = [
      {
        name: 'backend-1',
        url: 'https://prepandhirebackend.onrender.com',
        healthy: true,
        lastCheck: Date.now(),
        weight: 1
      },
      {
        name: 'backend-2', 
        url: 'https://sample.onrender.com',
        healthy: true,
        lastCheck: Date.now(),
        weight: 1
      },
      {
        name: 'backend-3',
        url: 'https://sample1.onrender.com',
        healthy: true,
        lastCheck: Date.now(),
        weight: 1
      }
    ];
    
    this.currentIndex = 0;
    this.healthCheckInterval = 30000; // 30 seconds
    this.startHealthChecks();
  }

  /**
   * Get the next healthy backend using round-robin
   */
  getNextBackend() {
    const healthyBackends = this.backends.filter(backend => backend.healthy);
    
    if (healthyBackends.length === 0) {
      throw new Error('No healthy backends available');
    }

    // Round-robin selection
    const backend = healthyBackends[this.currentIndex % healthyBackends.length];
    this.currentIndex++;
    
    return backend;
  }

  /**
   * Make an API call with automatic failover
   */
  async makeRequest(endpoint, options = {}) {
    const maxRetries = this.backends.length;
    let lastError;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const backend = this.getNextBackend();
        const url = `${backend.url}${endpoint}`;
        
        console.log(`🔄 Load Balancer: Attempting request to ${backend.name} (${url})`);
        
        const response = await fetch(url, {
          ...options,
          timeout: 10000 // 10 second timeout
        });

        if (response.ok) {
          console.log(`✅ Load Balancer: Success with ${backend.name}`);
          return response;
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
      } catch (error) {
        console.warn(`⚠️ Load Balancer: Failed with ${this.backends[attempt % this.backends.length].name}:`, error.message);
        lastError = error;
        
        // Mark backend as unhealthy
        this.backends[attempt % this.backends.length].healthy = false;
        
        // Wait before retry
        if (attempt < maxRetries - 1) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
    }

    throw new Error(`All backends failed. Last error: ${lastError?.message}`);
  }

  /**
   * Start periodic health checks
   */
  startHealthChecks() {
    setInterval(() => {
      this.checkAllBackends();
    }, this.healthCheckInterval);
  }

  /**
   * Check health of all backends
   */
  async checkAllBackends() {
    console.log('🏥 Load Balancer: Running health checks...');
    
    const healthPromises = this.backends.map(async (backend) => {
      try {
        const response = await fetch(`${backend.url}/health`, {
          method: 'GET',
          timeout: 5000
        });
        
        if (response.ok) {
          backend.healthy = true;
          backend.lastCheck = Date.now();
          console.log(`✅ ${backend.name} is healthy`);
        } else {
          backend.healthy = false;
          console.warn(`❌ ${backend.name} health check failed: ${response.status}`);
        }
      } catch (error) {
        backend.healthy = false;
        console.warn(`❌ ${backend.name} health check failed:`, error.message);
      }
    });

    await Promise.all(healthPromises);
  }

  /**
   * Get status of all backends
   */
  getStatus() {
    return {
      backends: this.backends.map(backend => ({
        name: backend.name,
        url: backend.url,
        healthy: backend.healthy,
        lastCheck: new Date(backend.lastCheck).toISOString()
      })),
      healthyCount: this.backends.filter(b => b.healthy).length,
      totalCount: this.backends.length
    };
  }
}

// Create singleton instance
const loadBalancer = new LoadBalancer();

export default loadBalancer;
