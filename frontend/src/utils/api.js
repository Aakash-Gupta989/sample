import config from '../config';
import connectionPool from './connectionPool';

// API utility functions with connection pooling
export const apiCall = async (endpoint, options = {}) => {
  console.log('🌐 Making API call to:', endpoint);
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  try {
    // Use connection pool for better reliability
    const response = await connectionPool.makeRequest(endpoint, { ...defaultOptions, ...options });
    return response;
  } catch (error) {
    console.error('❌ Connection pool failed, falling back to direct connection');
    
    // Fallback to direct connection
    const url = `${config.API_BASE_URL}${endpoint}`;
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
      throw new Error(`API call failed: ${response.status} ${response.statusText}`);
    }
    
    return response;
  }
};

// Specific API functions
export const startInterview = (data) => 
  apiCall('/interview/start', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getNextQuestion = (sessionId) => 
  apiCall(`/interview/next-question?session_id=${encodeURIComponent(sessionId)}`);

export const submitAnswer = (data) => 
  apiCall('/interview/answer', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const submitIntroduction = (data) => 
  apiCall('/interview/introduce', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const submitBriefIntroduction = (data) => 
  apiCall('/interview/brief-introduce', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getInterviewResults = (sessionId) => 
  apiCall(`/interview/results/${sessionId}`);

export const startCompanyQnA = (data) => 
  apiCall('/interview/start-company-qna', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const submitCompanyQuestion = (data) => 
  apiCall('/interview/submit-company-question', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getNextCodingProblem = (sessionId) => 
  apiCall(`/interview/next-coding-problem?session_id=${sessionId}`);

export const submitCode = (data) => 
  apiCall('/coding/submit', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const askClarification = (data) => 
  apiCall('/coding/clarify', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const submitFollowup = (data) => 
  apiCall('/coding/followup', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const runCode = (data) => 
  apiCall('/code/run', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const transcribeAudio = (formData) => 
  apiCall('/transcribe', {
    method: 'POST',
    body: formData,
  });

// Practice mode APIs
export const getPracticeSession = () => 
  apiCall('/practice/session');

export const getNextPracticeQuestion = (data) => 
  apiCall('/practice/next-question', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const analyzePracticeAnswer = (data) => 
  apiCall('/practice/analyze-answer', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const practiceChat = (data) => 
  apiCall('/practice/chat', {
    method: 'POST',
    body: JSON.stringify(data),
  });
