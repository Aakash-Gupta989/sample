import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft,
  Download,
  AlertCircle
} from 'lucide-react';
import pdfMake from 'pdfmake/build/pdfmake';
import pdfFonts from 'pdfmake/build/vfs_fonts';
import './InterviewResults.css';

// Set up pdfMake fonts (vfs_fonts exports { vfs })
pdfMake.vfs = pdfFonts.vfs;

const InterviewResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [resultsData, setResultsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Get session ID from location state or URL params
  const sessionId = location.state?.sessionId || new URLSearchParams(location.search).get('sessionId');
  
  // Debug logging
  console.log('🔍 Results page - location.state:', location.state);
  console.log('🔍 Results page - sessionId:', sessionId);

  useEffect(() => {
    if (sessionId) {
      fetchInterviewResults();
    } else {
      setError('No session ID provided');
      setLoading(false);
    }
  }, [sessionId]);

  const fetchInterviewResults = async () => {
    try {
      setLoading(true);
      console.log('🔍 Fetching results for session:', sessionId);
      const response = await fetch(`http://localhost:8000/interview/results/${sessionId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch results: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('🔍 Results data received:', data);
      setResultsData(data);
    } catch (err) {
      console.error('Error fetching results:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadResults = () => {
    if (!resultsData) return;
    
    const { session_info, performance_analysis, detailed_analysis, recommendations, sample_answers } = resultsData;
    
    // Build content array step by step for clean, professional layout
    const content = [];
    
    // 1. HEADER SECTION - Clean and centered
    content.push({
      text: 'INTERVIEW RESULTS',
      fontSize: 20,
      bold: true,
      alignment: 'center',
      margin: [0, 0, 0, 40]
    });
    
    // 2. CANDIDATE INFO - Simple and clean
    content.push({
      text: session_info.candidate_name,
      fontSize: 16,
      bold: true,
      margin: [0, 0, 0, 5]
    });
    
    content.push({
      text: session_info.position,
      fontSize: 12,
      margin: [0, 0, 0, 5]
    });
    
    content.push({
      text: `Interview Date: ${new Date(session_info.start_time).toLocaleDateString()}`,
      fontSize: 11,
      margin: [0, 0, 0, 30]
    });
    
    // 3. PERFORMANCE SECTION
    content.push({
      text: 'PERFORMANCE SUMMARY',
      fontSize: 14,
      bold: true,
      decoration: 'underline',
      margin: [0, 0, 0, 15]
    });
    
    content.push({
      text: `Overall Score: ${performance_analysis.overall_score.toFixed(1)}/100`,
      fontSize: 12,
      bold: true,
      margin: [0, 0, 0, 8]
    });
    
    content.push({
      text: `Performance Level: ${performance_analysis.performance_level}`,
      fontSize: 12,
      margin: [0, 0, 0, 30]
    });
    
    // 4. QUESTIONS & ANSWERS SECTION
    content.push({
      text: 'QUESTIONS & ANSWERS',
      fontSize: 14,
      bold: true,
      decoration: 'underline',
      margin: [0, 0, 0, 20]
    });
    
    // Add each Q&A pair with proper spacing
    detailed_analysis.forEach((item, index) => {
      const sampleAnswer = sample_answers?.find(
        sample => sample.question_number === item.question_number
      );
      
      let cleanSampleAnswer = 'Sample answer not available';
      if (sampleAnswer && sampleAnswer.sample_answer) {
        cleanSampleAnswer = sampleAnswer.sample_answer
          .replace(/\*\*/g, '')
          .replace(/\n\n/g, '\n')
          .trim();
      }
      
      // Question number and rating
      content.push({
        text: `Question ${item.question_number} (${item.answer_quality})`,
        fontSize: 12,
        bold: true,
        margin: [0, 15, 0, 8]
      });
      
      // Question text
      content.push({
        text: item.question_text,
        fontSize: 11,
        margin: [0, 0, 0, 12]
      });
      
      // Your answer label
      content.push({
        text: 'Your Answer:',
        fontSize: 11,
        bold: true,
        margin: [0, 0, 0, 5]
      });
      
      // Your answer text
      content.push({
        text: item.user_answer,
        fontSize: 10,
        margin: [15, 0, 0, 15],
        lineHeight: 1.3
      });
      
      // Optimal answer label
      content.push({
        text: 'Optimal Answer:',
        fontSize: 11,
        bold: true,
        margin: [0, 0, 0, 5]
      });
      
      // Optimal answer text
      content.push({
        text: cleanSampleAnswer,
        fontSize: 10,
        margin: [15, 0, 0, 20],
        lineHeight: 1.3
      });
    });
    
    // 5. RECOMMENDATIONS SECTION
    content.push({
      text: 'RECOMMENDATIONS',
      fontSize: 14,
      bold: true,
      decoration: 'underline',
      margin: [0, 10, 0, 15]
    });
    
    // Add recommendations
    recommendations.forEach((rec, index) => {
      content.push({
        text: `• ${rec}`,
        fontSize: 11,
        margin: [0, 0, 0, 8],
        lineHeight: 1.2
      });
    });
    
    // 6. FOOTER
    content.push({
      text: `Generated: ${new Date().toLocaleDateString()}`,
      fontSize: 9,
      alignment: 'center',
      margin: [0, 30, 0, 0]
    });
    
    // Create clean document definition
    const docDefinition = {
      pageSize: 'A4',
      pageMargins: [50, 50, 50, 50], // Clean, even margins
      content: content,
      defaultStyle: {
        font: 'Helvetica'
      }
    };
    
    // Generate and download
    const fileName = `interview-results-${session_info.candidate_name.replace(/\s+/g, '-').toLowerCase()}.pdf`;
    pdfMake.createPdf(docDefinition).download(fileName);
  };

  if (loading) {
    return (
      <div className="results-container">
        <div className="results-content">
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <h2>Loading Results...</h2>
            <p>Please wait while we analyze your performance.</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="results-container">
        <div className="results-content">
          <div className="error-state">
            <AlertCircle size={48} className="error-icon" />
            <h2>Unable to Load Results</h2>
            <p>{error}</p>
            <button onClick={() => navigate('/dashboard')} className="back-button">
              <ArrowLeft size={16} />
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!resultsData) {
    return (
      <div className="results-container">
        <div className="results-content">
          <div className="error-state">
            <AlertCircle size={48} className="error-icon" />
            <h2>No Results Available</h2>
            <p>Interview results could not be found.</p>
            <button onClick={() => navigate('/dashboard')} className="back-button">
              <ArrowLeft size={16} />
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  const { session_info, performance_analysis, detailed_analysis, recommendations } = resultsData;

  return (
    <div className="results-container">
      <div className="results-content">
        {/* Header */}
        <div className="results-header">
          <button onClick={() => navigate('/dashboard')} className="back-button">
            <ArrowLeft size={16} />
            Back to Dashboard
          </button>
          <h1>Interview Results</h1>
          <button onClick={downloadResults} className="download-button">
            <Download size={16} />
            Download Report
          </button>
        </div>

        {/* Score Section */}
        <div className="score-section">
          <div className="score-display">
            <div className="score-number">{Math.round(performance_analysis.overall_score)}</div>
            <div className="score-details">
              <h2>{performance_analysis.performance_level}</h2>
              <p>You answered {performance_analysis.questions_answered} out of {performance_analysis.total_questions} questions</p>
            </div>
          </div>
        </div>

        {/* Questions Section */}
        <div className="questions-section">
          <h3>Questions & Sample Answers</h3>
          <p className="section-description">
            Review each question with your answer and a sample STAR method response.
          </p>
          
          {detailed_analysis.length > 0 ? (
            <div className="questions-list">
              {detailed_analysis.map((item, index) => (
                <div key={index} className="question-item">
                  <div className="question-header">
                    <span className="question-number">Question {item.question_number}</span>
                    <span className={`quality-badge ${item.answer_quality.toLowerCase()}`}>
                      {item.answer_quality}
                    </span>
                  </div>
                  
                  <div className="question-content">
                    <div className="question-text">
                      <h4>Question:</h4>
                      <p>{item.question_text}</p>
                    </div>
                    
                    <div className="user-answer">
                      <h4>Your Answer:</h4>
                      <p>{item.user_answer}</p>
                      <div className="answer-stats">
                        <span>{item.word_count} words</span>
                        <span>{item.skill_focus}</span>
                      </div>
                    </div>
                    
                    <div className="sample-answer">
                      <h4>Optimal STAR Answer:</h4>
                      {(() => {
                        // Find the corresponding sample answer for this question
                        const sampleAnswer = resultsData.sample_answers?.find(
                          sample => sample.question_number === item.question_number
                        );
                        
                        if (sampleAnswer && sampleAnswer.sample_answer) {
                          // Parse the formatted STAR answer
                          const starSections = sampleAnswer.sample_answer.split('\n\n');
                          return (
                            <div className="star-method">
                              {starSections.map((section, idx) => {
                                const cleanSection = section.replace(/^\*\*|\*\*$/g, '');
                                const [label, ...contentParts] = cleanSection.split(':');
                                const content = contentParts.join(':').trim();
                                
                                if (content) {
                                  return (
                                    <div key={idx} className="star-item">
                                      <strong>{label}:</strong> {content}
                                    </div>
                                  );
                                }
                                return null;
                              })}
                            </div>
                          );
                        } else {
                          // Fallback generic STAR template
                          return (
                            <div className="star-method">
                              <div className="star-item">
                                <strong>Situation:</strong> Describe a specific engineering challenge or project context relevant to this question.
                              </div>
                              <div className="star-item">
                                <strong>Task:</strong> Explain your specific technical responsibility and what needed to be accomplished.
                              </div>
                              <div className="star-item">
                                <strong>Action:</strong> Detail your engineering approach, analysis methods, tools used, and collaboration with stakeholders.
                              </div>
                              <div className="star-item">
                                <strong>Result:</strong> Quantify the technical outcomes with measurable engineering impacts.
                              </div>
                            </div>
                          );
                        }
                      })()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-questions">
              <p>No questions found. Please complete an interview to see detailed results.</p>
            </div>
          )}
        </div>

        {/* Recommendations Section */}
        <div className="recommendations-section">
          <h3>Recommendations for Improvement</h3>
          <p className="section-description">
            Based on your performance, here's how you can improve for future interviews.
          </p>
          
          <div className="recommendations-list">
            {recommendations.map((recommendation, index) => (
              <div key={index} className="recommendation-item">
                <div className="recommendation-number">{index + 1}</div>
                <p>{recommendation}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default InterviewResults;
