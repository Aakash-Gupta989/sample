import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './LoadingPage.css';

const LoadingPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [progress, setProgress] = useState(0);
  
  const formData = location.state?.formData;
  
  // If no form data, redirect to setup
  useEffect(() => {
    if (!formData) {
      navigate('/');
      return;
    }
  }, [formData, navigate]);

  useEffect(() => {
    // Simple progress animation
    const duration = 8000; // 8 seconds total
    const interval = 100; // Update every 100ms
    const increment = 100 / (duration / interval);
    
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + increment;
        if (newProgress >= 100) {
          clearInterval(progressInterval);
          // Navigate to interview after completion
          setTimeout(() => {
            navigate('/interview', { state: { formData } });
          }, 500);
          return 100;
        }
        return newProgress;
      });
    }, interval);
    
    return () => clearInterval(progressInterval);
  }, [navigate, formData]);

  if (!formData) {
    return null; // Will redirect
  }

  return (
    <div className="loading-container">
      <div className="loading-content">
        <h2>Preparing your interview...</h2>
        
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${progress}%` }}
          />
        </div>
        
        <div className="progress-text">
          {Math.round(progress)}%
        </div>
      </div>
    </div>
  );
};

export default LoadingPage;
