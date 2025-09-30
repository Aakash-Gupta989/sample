import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import PracticeMode from './components/PracticeMode';
import InterviewSetup from './components/InterviewSetup';
import LoadingPage from './components/LoadingPage';
import InterviewSession from './components/InterviewSession';
import InterviewResults from './components/InterviewResults';
import './App.css';

const App = () => {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/setup" element={<InterviewSetup />} />
          <Route path="/loading" element={<LoadingPage />} />
          <Route path="/interview" element={<InterviewSession />} />
          <Route path="/results" element={<InterviewResults />} />
          <Route path="/practice" element={<PracticeMode />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;