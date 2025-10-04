import React, { useState, useEffect } from 'react';
import loadBalancer from '../utils/loadBalancer';
import './LoadBalancerStatus.css';

const LoadBalancerStatus = () => {
  const [status, setStatus] = useState(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const updateStatus = () => {
      const currentStatus = loadBalancer.getStatus();
      setStatus(currentStatus);
    };

    // Update status immediately
    updateStatus();

    // Update every 10 seconds
    const interval = setInterval(updateStatus, 10000);

    return () => clearInterval(interval);
  }, []);

  if (!status) return null;

  const healthyCount = status.healthyCount;
  const totalCount = status.totalCount;
  const isHealthy = healthyCount > 0;

  return (
    <div className="load-balancer-status">
      <button 
        className="status-toggle"
        onClick={() => setIsVisible(!isVisible)}
        title="Load Balancer Status"
      >
        🔄 LB: {healthyCount}/{totalCount}
      </button>

      {isVisible && (
        <div className="status-panel">
          <div className="status-header">
            <h3>🔄 Load Balancer Status</h3>
            <button 
              className="close-btn"
              onClick={() => setIsVisible(false)}
            >
              ×
            </button>
          </div>

          <div className="status-summary">
            <div className={`status-indicator ${isHealthy ? 'healthy' : 'unhealthy'}`}>
              {isHealthy ? '✅' : '❌'} {healthyCount}/{totalCount} Backends Healthy
            </div>
          </div>

          <div className="backend-list">
            {status.backends.map((backend, index) => (
              <div key={index} className={`backend-item ${backend.healthy ? 'healthy' : 'unhealthy'}`}>
                <div className="backend-name">
                  {backend.healthy ? '✅' : '❌'} {backend.name}
                </div>
                <div className="backend-url">
                  {backend.url}
                </div>
                <div className="backend-last-check">
                  Last check: {new Date(backend.lastCheck).toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>

          <div className="status-actions">
            <button 
              className="refresh-btn"
              onClick={() => {
                loadBalancer.checkAllBackends();
                setTimeout(() => setStatus(loadBalancer.getStatus()), 2000);
              }}
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default LoadBalancerStatus;
