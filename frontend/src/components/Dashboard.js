import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

const Dashboard = () => {
  const navigate = useNavigate();

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>AI Interview Assistant</h1>
        <p>Choose your preparation method</p>
      </div>
      
      <div className="dashboard-options">
        <div className="option-card practice-card" onClick={() => navigate('/practice')}>
          <h2>Practice Questions</h2>
          <p>184 curated engineering questions</p>
          <span className="card-arrow">→</span>
        </div>
        
        <div className="option-card interview-card" onClick={() => navigate('/setup')}>
          <h2>AI Interview</h2>
          <p>Personalized interview simulation</p>
          <span className="card-arrow">→</span>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
