import React, { useState, useRef, useEffect } from 'react';
import config from '../config';
import { 
  MessageCircle, 
  Mic, 
  Send, 
  ArrowLeft,
  HelpCircle,
  Info,
  Timer,
  ThumbsUp,
  ThumbsDown,
  AlertTriangle
} from 'lucide-react';
import { 
  Canvas, 
  PencilBrush
} from 'fabric';
import Toolbar from './Toolbar';
import WidgetPanel from './WidgetPanel';
import { setupShapeCreation } from '../utils/canvasShapes';
import { createWidget } from '../utils/canvasWidgets';
import '../App.css';

const PracticeMode = () => {
  // State
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [fabricCanvas, setFabricCanvas] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [completedQuestions, setCompletedQuestions] = useState([]);
  const [showModelAnswer, setShowModelAnswer] = useState(false);
  const [practiceStarted, setPracticeStarted] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [selectedTool, setSelectedTool] = useState('select');
  const [isWidgetPanelOpen, setIsWidgetPanelOpen] = useState(false);
  
  // Simple markdown formatter with styling
  const formatText = (text) => {
    if (!text) return text;
    
    return text
      // Bold text **text** -> <strong>text</strong>
      .replace(/\*\*(.*?)\*\*/g, '<strong style="color: #1f2937; font-weight: 600;">$1</strong>')
      // Headers ### text -> <h3>text</h3>
      .replace(/^### (.*$)/gm, '<h3 style="font-size: 1.1em; font-weight: 600; margin: 12px 0 8px 0; color: #374151;">$1</h3>')
      // Headers ## text -> <h2>text</h2>
      .replace(/^## (.*$)/gm, '<h2 style="font-size: 1.2em; font-weight: 600; margin: 16px 0 10px 0; color: #374151;">$1</h2>')
      // Headers # text -> <h1>text</h1>
      .replace(/^# (.*$)/gm, '<h1 style="font-size: 1.3em; font-weight: 600; margin: 20px 0 12px 0; color: #374151;">$1</h1>')
      // Numbered lists 1. text -> <ol><li>text</li></ol>
      .replace(/^\d+\.\s+(.*)$/gm, '<div style="margin: 8px 0; padding-left: 16px;"><span style="font-weight: 500; color: #6366f1;">•</span> $1</div>')
      // Horizontal rules --- -> <hr>
      .replace(/^---$/gm, '<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 16px 0;">')
      // Line breaks
      .replace(/\n/g, '<br/>');
  };
  
  // Refs
  const canvasRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Canvas initialization - Basic whiteboard only
  useEffect(() => {
    const initCanvas = () => {
      if (!canvasRef.current) {
        console.log('❌ Canvas ref not available');
        return;
      }

      try {
        const container = canvasRef.current.parentElement;
        if (!container) {
          console.log('❌ Canvas container not found');
          return;
        }
        
        const rect = container.getBoundingClientRect();
        console.log('📐 Canvas container size:', rect.width, 'x', rect.height);
        
        // Create new canvas instance
        const newCanvas = new Canvas(canvasRef.current, {
          width: rect.width,
          height: rect.height,
          backgroundColor: 'white',
          selection: true,
          isDrawingMode: false // Start in select mode
        });

        // Initialize brush for when needed
        if (newCanvas.freeDrawingBrush) {
          newCanvas.freeDrawingBrush.width = 2;
          newCanvas.freeDrawingBrush.color = '#000000';
          console.log('🖌️ Brush configured:', newCanvas.freeDrawingBrush.width, newCanvas.freeDrawingBrush.color);
        }
        
        // Add event listeners
        newCanvas.on('path:created', function(e) {
          // Drawing created
        });

        // Store canvas
        setFabricCanvas(newCanvas);
        window.globalCanvas = newCanvas; // Global access for debugging
        
        // Resize handler
        const resizeCanvas = () => {
          const newRect = container.getBoundingClientRect();
          newCanvas.setDimensions({
            width: newRect.width,
            height: newRect.height
          });
        };

        window.addEventListener('resize', resizeCanvas);

        return () => {
          window.removeEventListener('resize', resizeCanvas);
          newCanvas.dispose();
        };
      } catch (error) {
        console.error('❌ Canvas initialization error:', error);
      }
    };

    // Wait for DOM to be ready
    const timer = setTimeout(initCanvas, 1000);
    return () => clearTimeout(timer);
  }, []);

  // Show welcome message on mount
  useEffect(() => {
    showWelcomeMessage();
  }, []);

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const showWelcomeMessage = () => {
    const welcomeMessage = {
      id: Date.now(),
      role: 'assistant',
      content: 'Welcome to Practice Mode! 🎯\n\nI have 184 engineering questions ready for you. Each question comes from real interviews at top companies.\n\nReady to start practicing?',
      timestamp: new Date()
    };
    setMessages([welcomeMessage]);
  };

  const loadFirstQuestion = async () => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/practice/session`);
      const data = await response.json();
      
      if (data.success && data.currentQuestion) {
        setCurrentQuestion(data.currentQuestion);
        setQuestionIndex(data.questionIndex);
        setCompletedQuestions(data.completedQuestions || []);
        setPracticeStarted(true);
        
        // Show the question
        const questionMessage = {
          id: Date.now(),
          role: 'assistant',
          content: `🏢 ${data.currentQuestion.company}\n\nQuestion:\n${data.currentQuestion.question}`,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, questionMessage]);
      }
    } catch (error) {
      console.error('Failed to load first question:', error);
      // Fallback question
      const fallbackMessage = {
        id: Date.now(),
        role: 'assistant',
        content: 'Sorry, I had trouble loading questions. Please refresh the page and try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, fallbackMessage]);
    }
  };

  const loadNextQuestion = async () => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/practice/next-question`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completedQuestions })
      });
      
      const data = await response.json();
      
      if (data.success && data.question) {
        setCurrentQuestion(data.question);
        setQuestionIndex(data.questionIndex);
        setShowModelAnswer(false);
        
        const questionMessage = {
          id: Date.now(),
          role: 'assistant',
          content: `🏢 ${data.question.company}\n\nQuestion:\n${data.question.question}`,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, questionMessage]);
      } else {
        // All questions completed
        const completionMessage = {
          id: Date.now(),
          role: 'assistant',
          content: '🎉 Congratulations! You have completed all 184 practice questions!',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, completionMessage]);
      }
    } catch (error) {
      console.error('Failed to load next question:', error);
    }
  };

  // Voice recording - Fixed to properly collect audio chunks
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Check supported MIME types and use the best one
      let mimeType = 'audio/webm';
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4';
      } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
        mimeType = 'audio/ogg;codecs=opus';
      }
      
      const recorder = new MediaRecorder(stream, { mimeType });
      const chunks = []; // Use local array to avoid state closure issues
      
      recorder.ondataavailable = (event) => {
        console.log('Audio data available:', event.data.size, 'bytes');
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      recorder.onstop = async () => {
        console.log('Recording stopped. Total chunks:', chunks.length);
        const audioBlob = new Blob(chunks, { type: mimeType });
        console.log('Created audio blob:', audioBlob.size, 'bytes, type:', audioBlob.type);
        
        if (audioBlob.size > 0) {
          await transcribeAndFillInput(audioBlob);
        } else {
          console.error('No audio data captured');
          alert('No audio was recorded. Please try again.');
        }
        
        stream.getTracks().forEach(track => track.stop());
      };
      
      recorder.start(1000); // Collect data every 1 second
      setMediaRecorder(recorder);
      setIsRecording(true);
      setAudioChunks([]); // Reset state for UI purposes
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      setIsRecording(false);
      setMediaRecorder(null);
    }
  };

  const transcribeAndFillInput = async (audioBlob) => {
    try {
      console.log('Starting transcription for blob:', audioBlob.size, 'bytes, type:', audioBlob.type);
      
      const formData = new FormData();
      
      // Use proper filename based on blob type
      let filename = 'audio.webm';
      if (audioBlob.type.includes('mp4')) {
        filename = 'audio.mp4';
      } else if (audioBlob.type.includes('ogg')) {
        filename = 'audio.ogg';
      }
      
      formData.append('file', audioBlob, filename);
      
      console.log('Sending transcription request...');
      const response = await fetch(`${config.API_BASE_URL}/transcribe`, {
        method: 'POST',
        body: formData,
      });
      
      const result = await response.json();
      console.log('Transcription result:', result);
      
      if (result.success && result.transcription) {
        // Fill the input field with transcribed text
        setInputText(result.transcription);
        console.log('✅ Transcription successful:', result.transcription);
      } else {
        console.error('Transcription failed:', result.error);
        alert(`Failed to transcribe audio: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error transcribing audio:', error);
      alert('Failed to transcribe audio. Please try typing instead.');
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // Handle submit answer
  const handleAnalyze = async () => {
    const userResponse = inputText.trim();
    
    if (!userResponse) {
      alert('Please provide a text answer.');
      return;
    }

    // Add user message to chat
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: userResponse,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setInputText('');

    // Analyze with text only
    await handleAnalyzeWithImage(userResponse, '');
  };

  // Separate function to handle analysis with or without image
  const handleAnalyzeWithImage = async (userAnswer, imageData = '') => {
    if (!currentQuestion) return;

    setIsAnalyzing(true);

    try {
      const response = await fetch(`${config.API_BASE_URL}/practice/analyze-answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          questionId: currentQuestion.id,
          userAnswer: userAnswer,
          imageData: imageData,
          modelAnswer: currentQuestion.answer
        })
      });

      const result = await response.json();
      
      if (result.success) {
        // Different response handling based on which model was used
        const usedModel = result.usedModel || 'unknown';
        let feedbackContent = '';
        
        if (usedModel === 'openai') {
          // GPT-4o provided complete analysis - don't show model answer separately
          feedbackContent = `${result.feedback}\n\n---\n\n🔄 Ready for the next question? Type "next" or ask me anything about this question!`;
        } else {
          // Groq provided simple feedback - show model answer as well
          feedbackContent = `**Analysis Result:** ${result.feedback}\n\n💡 **Model Answer:**\n${currentQuestion.answer}\n\n---\n\n🔄 Ready for the next question? Type "next" or ask me anything about this question!`;
        }
        
        const feedbackMessage = {
          id: Date.now(),
          role: 'assistant',
          content: feedbackContent,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, feedbackMessage]);
        setShowModelAnswer(true);
      } else {
        throw new Error(result.error || 'Analysis failed');
      }
    } catch (error) {
      console.error('Failed to analyze answer:', error);
      const errorMessage = {
        id: Date.now(),
        role: 'assistant',
        content: 'Sorry, I had trouble analyzing your answer. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
    
    setIsAnalyzing(false);
  };

  // Handle chat (for follow-ups or next question)
  const handleSendMessage = async () => {
    const userMessage = inputText.trim();
    if (!userMessage) return;

    // Check if user wants to start practice
    if (!practiceStarted && (userMessage.toLowerCase().includes('yes') || userMessage.toLowerCase().includes('ready') || userMessage.toLowerCase().includes('start'))) {
      const userMsg = {
        id: Date.now(),
        role: 'user',
        content: userMessage,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMsg]);
      setInputText('');
      loadFirstQuestion();
      return;
    }

    // Check if user wants next question
    if (userMessage.toLowerCase() === 'next' && showModelAnswer) {
      setCompletedQuestions(prev => [...prev, currentQuestion.id]);
      loadNextQuestion();
      setInputText('');
      return;
    }

    // Add user message
    const chatMessage = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, chatMessage]);
    setInputText('');

    // Get AI response for follow-up
    try {
      const response = await fetch(`${config.API_BASE_URL}/practice/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          currentQuestion: currentQuestion
        })
      });

      const result = await response.json();
      
      if (result.success) {
        const aiMessage = {
          id: Date.now(),
          role: 'assistant',
          content: result.response,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error('Failed to get chat response:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      if (!practiceStarted || showModelAnswer) {
        handleSendMessage();
      } else {
        handleAnalyze();
      }
    }
  };

  // Insert whiteboard screenshot directly into chat with text
  const insertWhiteboardToChat = () => {
    if (!fabricCanvas) {
      alert('Whiteboard not available');
      return;
    }

    try {
      // Check if canvas has any content
      if (fabricCanvas.isEmpty()) {
        alert('Please draw something on the whiteboard first');
        return;
      }

      // Get current input text
      const currentText = inputText.trim();
      if (!currentText) {
        alert('Please write some text explanation before inserting the whiteboard');
        return;
      }

      // Get canvas dimensions
      const canvasWidth = fabricCanvas.getWidth();
      const canvasHeight = fabricCanvas.getHeight();
      
      console.log(`📐 Canvas dimensions: ${canvasWidth}x${canvasHeight}`);
      
      // Ensure minimum size for better quality (at least 600x400 for better analysis)
      const minWidth = 600;
      const minHeight = 400;
      
      let scaleFactor = 1;
      if (canvasWidth < minWidth || canvasHeight < minHeight) {
        scaleFactor = Math.max(minWidth / canvasWidth, minHeight / canvasHeight);
        console.log(`🔍 Scaling canvas by factor: ${scaleFactor}`);
      }

      // Get high-quality canvas screenshot with proper scaling
      const imageData = fabricCanvas.toDataURL({
        format: 'png',
        quality: 1.0, // Maximum quality
        multiplier: scaleFactor, // Scale up if needed
        enableRetinaScaling: true
      });
      
      // Validate the image data
      if (!imageData || imageData.length < 1000) {
        throw new Error('Invalid image data captured');
      }
      
      console.log(`📸 Captured image size: ${Math.round(imageData.length / 1024)}KB`);
      
      // Create a combined message with text + image
      const combinedMessage = {
        id: Date.now(),
        role: 'user',
        content: currentText,
        image: imageData, // Store the image with the message
        timestamp: new Date()
      };

      // Add the message to chat
      setMessages(prev => [...prev, combinedMessage]);
      
      // Clear the input
      setInputText('');
      
      // Show confirmation
      alert('✅ Message with whiteboard sent! GPT-4o will analyze both your text and diagram.');
      
      // Automatically analyze the answer
      setTimeout(() => {
        handleAnalyzeWithImage(currentText, imageData);
      }, 500);
      
    } catch (error) {
      console.error('Error capturing whiteboard:', error);
      alert(`Failed to capture whiteboard: ${error.message}`);
    }
  };

  // Toolbar handler
  const handleToolSelect = (toolId) => {
    console.log('🔧 Tool selected:', toolId);
    setSelectedTool(toolId);
    if (fabricCanvas) {
      setupShapeCreation(fabricCanvas, toolId, () => {
        // Auto-switch back to select after creating a shape
        console.log('🔄 Auto-switching to select tool');
        setSelectedTool('select');
      });
    }
  };

  // Library toggle handler
  const handleLibraryToggle = () => {
    setIsWidgetPanelOpen(!isWidgetPanelOpen);
  };

  // Widget selection handler
  const handleWidgetSelect = (widget) => {
    console.log('🎯 Widget selected:', widget);
    console.log('🎯 Canvas available:', !!fabricCanvas);
    
    if (fabricCanvas) {
      // Use a simple center position for now - much more reliable
      const canvasCenter = fabricCanvas.getCenter();
      const position = {
        x: canvasCenter.left + (Math.random() - 0.5) * 200, // Add some randomness
        y: canvasCenter.top + (Math.random() - 0.5) * 200
      };
      
      console.log('🎯 Creating widget at position:', position);
      const result = createWidget(widget, fabricCanvas, position);
      console.log('🎯 Widget creation result:', !!result);
    } else {
      console.error('❌ Canvas not available for widget creation');
    }
    
    // Close the panel after selection
    setIsWidgetPanelOpen(false);
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <button className="icon-btn" onClick={() => window.history.back()}>
            <ArrowLeft size={20} />
          </button>
          <h1 className="topic">Practice Mode</h1>
          <div className="connection-status">
            <div className="status-dot connected"></div>
            <span>Question {questionIndex + 1}/184</span>
          </div>
        </div>
        <div className="header-right">
          <div className="timer">
            <Timer size={16} />
            <span>Practice</span>
          </div>
          <button className="icon-btn">
            <HelpCircle size={20} />
          </button>
          <button className="primary-btn" onClick={() => window.location.href = '/'}>Exit Practice</button>
          <button className="icon-btn">
            <Info size={20} />
          </button>
        </div>
      </header>

      {/* Main Content - Identical layout to interview page */}
      <main className="main">
        {/* Left Panel - Chat */}
        <section className="chat-section">
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="empty-state">
                <MessageCircle size={48} className="empty-icon" />
                <h3>Loading Question</h3>
                <p>Please wait while I load your first practice question...</p>
              </div>
            ) : (
              <>
                {messages.map(message => (
                  <div key={message.id} className={`message ${message.role}`}>
                    <div className="message-content">
                      <div className="message-header">
                        <span className="sender">{message.role === 'user' ? 'You' : 'Practice Assistant'}</span>
                        <span className="timestamp">
                          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <div 
                        className="message-text" 
                        dangerouslySetInnerHTML={{ __html: formatText(message.content) }}
                        style={{ 
                          lineHeight: '1.6',
                          fontSize: '14px',
                          color: '#374151',
                          wordWrap: 'break-word'
                        }}
                      />
                      {message.image && (
                        <div className="message-image">
                          <img 
                            src={message.image} 
                            alt="Whiteboard screenshot" 
                            style={{
                              maxWidth: '300px',
                              maxHeight: '200px',
                              borderRadius: '8px',
                              border: '1px solid #e5e7eb',
                              marginTop: '8px'
                            }}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isAnalyzing && (
                  <div className="message assistant analyzing">
                    <div className="message-content">
                      <div className="message-header">
                        <span className="sender">Practice Assistant</span>
                        <span className="timestamp">now</span>
                      </div>
                      <div className="message-text">
                        <div className="typing-indicator">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                        Analyzing your answer...
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          <div className="input-section">
            <div className="response-info">
              <span className="response-count">Question {questionIndex + 1}/184</span>
            </div>
            
            <div className="input-area">
              <textarea
                id="practiceMessage"
                name="practiceMessage"
                className="message-input"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder={
                  !practiceStarted 
                    ? "Type 'yes' or 'ready' to start practicing..." 
                    : showModelAnswer 
                      ? "Ask follow-up questions or type 'next' for next question..." 
                      : "Type your answer here..."
                }
                rows={4}
                aria-label="Practice answer input"
              />
              <div className="input-actions">
                <button 
                  className={`record-btn ${isRecording ? 'recording' : ''}`}
                  onClick={toggleRecording}
                  title={isRecording ? 'Stop recording' : 'Click to speak (fills text field)'}
                >
                  <Mic size={20} />
                  {isRecording && <div className="recording-indicator-dot"></div>}
                </button>
                <button 
                  className="send-btn"
                  onClick={
                    !practiceStarted || showModelAnswer 
                      ? handleSendMessage 
                      : handleAnalyze
                  }
                  disabled={!inputText.trim() && (!fabricCanvas || fabricCanvas.isEmpty())}
                  title={
                    !practiceStarted 
                      ? "Send message" 
                      : showModelAnswer 
                        ? "Send message" 
                        : "Submit answer to AI"
                  }
                >
                  <Send size={20} />
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Right Panel - Canvas */}
        <section className="canvas-section">
          <div className="canvas-area">
            <canvas ref={canvasRef} />
            <Toolbar 
              onToolSelect={handleToolSelect}
              selectedTool={selectedTool}
              fabricCanvas={fabricCanvas}
              onLibraryToggle={handleLibraryToggle}
            />
            <WidgetPanel 
              isOpen={isWidgetPanelOpen}
              onWidgetSelect={handleWidgetSelect}
            />
          </div>

          <div className="canvas-footer">
            <button 
              className="analyze-button"
              onClick={insertWhiteboardToChat}
              disabled={!fabricCanvas}
              title="Send text + whiteboard to GPT-4o for analysis"
            >
              Send with Whiteboard
            </button>

            <div className="feedback-section">
              <span>Helpful?</span>
              <button className="feedback-btn">
                <ThumbsUp size={16} />
              </button>
              <button className="feedback-btn">
                <ThumbsDown size={16} />
              </button>
              <button className="feedback-btn">
                <AlertTriangle size={16} />
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default PracticeMode;