import React, { useState, useEffect } from 'react';
import connectionPool from '../utils/connectionPool';
import './LoadBalancerStatus.css';

const LoadBalancerStatus = () => {
  const [status, setStatus] = useState(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const updateStatus = () => {
      const currentStatus = connectionPool.getStatus();
      setStatus(currentStatus);
    };

    // Update status immediately
    updateStatus();

    // Update every 10 seconds
    const interval = setInterval(updateStatus, 10000);

    return () => clearInterval(interval);
  }, []);

  if (!status) return null;

  const activeConnections = status.activeConnections;
  const maxConnections = status.maxConnections;
  const isHealthy = status.isHealthy;

  return (
    <div className="load-balancer-status">
      <button 
        className="status-toggle"
        onClick={() => setIsVisible(!isVisible)}
        title="Connection Pool Status"
      >
        🔄 CP: {activeConnections}/{maxConnections}
      </button>

      {isVisible && (
        <div className="status-panel">
          <div className="status-header">
            <h3>🔄 Connection Pool Status</h3>
            <button 
              className="close-btn"
              onClick={() => setIsVisible(false)}
            >
              ×
            </button>
          </div>

          <div className="status-summary">
            <div className={`status-indicator ${isHealthy ? 'healthy' : 'unhealthy'}`}>
              {isHealthy ? '✅' : '❌'} {activeConnections}/{maxConnections} Connections Active
            </div>
          </div>

          <div className="backend-list">
            <div className="backend-item healthy">
              <div className="backend-name">
                ✅ Backend Service
              </div>
              <div className="backend-url">
                {status.baseUrl}
              </div>
              <div className="backend-last-check">
                Active connections: {activeConnections}
              </div>
            </div>
          </div>

          <div className="status-actions">
            <button 
              className="refresh-btn"
              onClick={() => {
                setStatus(connectionPool.getStatus());
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
