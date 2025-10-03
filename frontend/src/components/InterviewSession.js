import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import config from '../config';
import { 
  MessageCircle, 
  Mic, 
  Send, 
  ArrowLeft,
  HelpCircle,
  Info,
  Timer,
  Square,
  ThumbsUp,
  ThumbsDown,
  AlertTriangle,
  Code
} from 'lucide-react';
import { 
  Canvas, 
  PencilBrush
} from 'fabric';
import { v4 as uuidv4 } from 'uuid';
import WebSocketService from '../services/WebSocketService';
import Toolbar from './Toolbar';
import WidgetPanel from './WidgetPanel';
import CodeEditor from './CodeEditor';
import { setupShapeCreation } from '../utils/canvasShapes';
import { createWidget } from '../utils/canvasWidgets';
import '../App.css';

const InterviewSession = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const formData = location.state?.formData || {
    // Fallback data if no formData is passed
    username: 'Aakash Gupta',
    position: 'Software Engineer',
    jobDescription: 'Design and develop scalable web applications using modern technologies. Requirements: React, Node.js, API development.',
    resumeText: 'Aakash Gupta - Software Engineer with experience in full-stack development. Skills: React, Node.js, JavaScript, API development.',
    interviewType: 'technical_behavioral',
    duration: 60,
  };
  
  // Get topic from form data or URL
  const urlParams = new URLSearchParams(window.location.search);
  const topic = formData?.position || urlParams.get('topic') || 'Interview Session';
  
  // State
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [fabricCanvas, setFabricCanvas] = useState(null);
  const [interviewStarted, setInterviewStarted] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [interviewPhase, setInterviewPhase] = useState('not_started'); // not_started | awaiting_introduction | brief_introduction | questioning
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [selectedTool, setSelectedTool] = useState('select');
  const [isWidgetPanelOpen, setIsWidgetPanelOpen] = useState(false);
  const [showCodeEditor, setShowCodeEditor] = useState(formData.interviewType === 'coding');
  const [codeTemplate, setCodeTemplate] = useState('');
  const [currentCode, setCurrentCode] = useState(''); // Store current code from editor
  const [isInFollowUp, setIsInFollowUp] = useState(false); // Track if we're in a coding follow-up conversation
  // Input mode: 'text' | 'voice' - default to voice for interview
  const [inputMode, setInputMode] = useState(() => {
    try {
      return localStorage.getItem('interviewInputMode') || 'voice';
    } catch (e) {
      return 'voice';
    }
  });
  
  // TTS state
  const [currentAudio, setCurrentAudio] = useState(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  
  
  // Refs
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  // WebSocket connection - More resilient
  useEffect(() => {
    const sessionId = uuidv4();
    
    const wsService = new WebSocketService(sessionId);
    
    wsService.onConnect = () => {
      setIsConnected(true);
    };
    
    wsService.onDisconnect = () => {
      setIsConnected(false);
    };
    
    wsService.onMessage = (data) => {
      // Backend sends { type: 'ai_response', ai_response: string }
      // Support legacy 'whiteboard_analysis' too
      if (data && (data.type === 'ai_response' || data.type === 'whiteboard_analysis')) {
        const aiMessage = {
          id: `ai_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          role: 'assistant',
          content: data.ai_response || data.message || '',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiMessage]);
        setIsAnalyzing(false);
        
        // Note: TTS will be triggered by useEffect watching messages
      } else if (data && data.type === 'error') {
        const errMsg = {
          id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          role: 'assistant',
          content: data.message || 'Sorry, I encountered an error analyzing your whiteboard.',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errMsg]);
        setIsAnalyzing(false);
      }
    };
    
    wsService.onError = (error) => {
      setIsConnected(false);
    };
    
    // Delay connection to ensure backend is ready
    setTimeout(() => {
      wsService.connect();
      wsRef.current = wsService;
    }, 1000);
    
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
    };
  }, []);

  // Persist input mode selection and handle TTS interruption
  useEffect(() => {
    try {
      localStorage.setItem('interviewInputMode', inputMode);
      
      // Stop TTS when switching to text mode
      if (inputMode === 'text') {
        stopTTS();
      }
    } catch (e) {}
  }, [inputMode]);

  // Helper to create Fabric canvas (reusable for toggling)
  const createFabricCanvas = () => {
    if (!canvasRef.current) {
      console.log('❌ Canvas ref not available');
      return () => {};
    }

    try {
      const container = canvasRef.current.parentElement;
      if (!container) {
        console.log('❌ Canvas container not found');
        return () => {};
      }

      const rect = container.getBoundingClientRect();
      const newCanvas = new Canvas(canvasRef.current, {
        width: rect.width,
        height: rect.height,
        backgroundColor: 'white',
        selection: true,
        isDrawingMode: false
      });

      if (newCanvas.freeDrawingBrush) {
        newCanvas.freeDrawingBrush.width = 2;
        newCanvas.freeDrawingBrush.color = '#000000';
      }

      setFabricCanvas(newCanvas);
      window.globalCanvas = newCanvas;

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
      return () => {};
    }
  };

  // Canvas initialization on mount
  useEffect(() => {
    const timer = setTimeout(() => {
      const cleanup = createFabricCanvas();
      // store cleanup to dispose on unmount
      canvasRef.current && (canvasRef.current.__cleanup = cleanup);
    }, 500);
    return () => {
      clearTimeout(timer);
      if (canvasRef.current && canvasRef.current.__cleanup) {
        canvasRef.current.__cleanup();
      }
    };
  }, []);

  // Auto-scroll messages and debug state changes
  useEffect(() => {
    console.log('📝 Messages state changed! New length:', messages.length);
    console.log('📝 Messages content:', messages);
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // TTS for new AI messages
  useEffect(() => {
    if (inputMode === 'voice' && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role === 'assistant' && lastMessage.content) {
        // Skip TTS for silent messages (clarifications) and coding problems
        if (lastMessage.silent) {
          console.log('🔇 Skipping TTS for silent message (clarification)');
        } else if (lastMessage.isCodingProblem) {
          console.log('🔇 Skipping TTS for coding problem');
        } else {
          console.log('🎤 Triggering TTS for new AI message:', lastMessage.content.substring(0, 50) + '...');
          playTTS(lastMessage.content, lastMessage);
        }
      }
    }
  }, [messages, inputMode]);

  // Helper function to get voices with proper loading
  const getVoicesWithFallback = () => {
    return new Promise((resolve) => {
      let voices = window.speechSynthesis.getVoices();
      
      if (voices.length > 0) {
        resolve(voices);
        return;
      }
      
      // If no voices initially, wait for them to load
      const handleVoicesChanged = () => {
        voices = window.speechSynthesis.getVoices();
        if (voices.length > 0) {
          window.speechSynthesis.removeEventListener('voiceschanged', handleVoicesChanged);
          resolve(voices);
        }
      };
      
      window.speechSynthesis.addEventListener('voiceschanged', handleVoicesChanged);
      
      // Fallback timeout
      setTimeout(() => {
        window.speechSynthesis.removeEventListener('voiceschanged', handleVoicesChanged);
        resolve(window.speechSynthesis.getVoices());
      }, 1000);
    });
  };

  // TTS functions with browser fallback
  const playTTS = async (text, message = null) => {
    if (inputMode !== 'voice' || !text.trim()) {
      return;
    }
    
    try {
      // Stop any current audio and recording
      if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
      }
      
      // Stop any ongoing recording when TTS starts
      if (isRecording) {
        stopRecording();
      }
      
      setIsSpeaking(true);
      
      // Skip backend TTS (always returns 503) and use browser TTS directly for instant response
      console.log('🎤 Using browser TTS directly for instant narration');
      
      // Fallback to browser Speech Synthesis API
      if ('speechSynthesis' in window) {
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Wait for voices to load properly
        const voices = await getVoicesWithFallback();
        
        // Priority order for UK female voices
        const ukVoice = voices.find(voice => 
          voice.name.toLowerCase().includes('google uk english female')
        ) || voices.find(voice => 
          voice.name.toLowerCase().includes('kate') && voice.lang.includes('en-GB')
        ) || voices.find(voice => 
          voice.name.toLowerCase().includes('serena') && voice.lang.includes('en-GB')
        ) || voices.find(voice => 
          voice.name.toLowerCase().includes('shelley') && voice.lang.includes('en-GB')
        ) || voices.find(voice => 
          voice.name.toLowerCase().includes('susan') && voice.lang.includes('en-GB')
        ) || voices.find(voice => 
          voice.lang.includes('en-GB') && voice.name.toLowerCase().includes('female')
        ) || voices.find(voice => 
          voice.lang.includes('en-GB')
        ) || voices.find(voice => 
          voice.name.toLowerCase().includes('uk') ||
          voice.name.toLowerCase().includes('british')
        ) || voices.find(voice => voice.lang.includes('en-'));
        
        if (ukVoice) {
          utterance.voice = ukVoice;
          console.log('🎤 Using voice:', ukVoice.name, ukVoice.lang);
        } else {
          console.log('⚠️ No UK voice found, using default. Available voices:', voices.length);
        }
        
        // Configure for more natural female voice
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        utterance.volume = 0.8;
        
        utterance.onend = () => {
          setIsSpeaking(false);
          setCurrentAudio(null);
          
          // Check if we need to navigate after TTS completion
          if (message && message.navigateOnTTSComplete) {
            console.log('🎉 Interview completed! Navigating to results after browser TTS...');
            setTimeout(() => {
              navigate('/results', { state: { sessionId } });
            }, 500);
            return;
          }
          
          // Auto-start recording when TTS finishes
          if (inputMode === 'voice') {
            setTimeout(() => startRecording(), 500); // Small delay for smooth transition
          }
        };
        
        utterance.onerror = () => {
          setIsSpeaking(false);
          setCurrentAudio(null);
          
          // Check if we need to navigate after TTS completion (even on error)
          if (message && message.navigateOnTTSComplete) {
            console.log('🎉 Interview completed! Navigating to results after browser TTS error...');
            setTimeout(() => {
              navigate('/results', { state: { sessionId } });
            }, 500);
            return;
          }
          
          // Auto-start recording even on error
          if (inputMode === 'voice') {
            setTimeout(() => startRecording(), 500);
          }
        };
        
        setCurrentAudio({ pause: () => window.speechSynthesis.cancel() });
        
        window.speechSynthesis.speak(utterance);
      } else {
        throw new Error('No TTS available');
      }
      
    } catch (error) {
      console.error('TTS error:', error);
      setIsSpeaking(false);
      setCurrentAudio(null);
      
      // Check if we need to navigate after TTS completion (even on error)
      if (message && message.navigateOnTTSComplete) {
        console.log('🎉 Interview completed! Navigating to results after TTS error...');
        setTimeout(() => {
          navigate('/results', { state: { sessionId } });
        }, 500);
        return;
      }
      
      // Auto-start recording even on TTS error
      if (inputMode === 'voice') {
        setTimeout(() => startRecording(), 500);
      }
    }
  };
  
  const stopTTS = () => {
    if (currentAudio) {
      if (currentAudio.pause) {
        currentAudio.pause();
        if (currentAudio.currentTime !== undefined) {
          currentAudio.currentTime = 0;
        }
      }
      setCurrentAudio(null);
    }
    // Also cancel browser speech synthesis
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  };

  // Derived UI state for Voice Mode
  const voiceStatus = isSpeaking ? 'Speaking…' : (isAnalyzing ? 'Thinking…' : (isRecording ? 'Listening…' : 'Ready'));

  // Start interview when connected - Fixed to prevent multiple calls
  useEffect(() => {
    console.log('🔄 useEffect triggered - isConnected:', isConnected, 'interviewStarted:', interviewStarted);
    if (isConnected && !interviewStarted) {
      console.log('✅ Conditions met, calling startInterview()');
      // Add a small delay to ensure state is stable
      const timer = setTimeout(() => {
        startInterview();
      }, 100);
      return () => clearTimeout(timer);
    } else {
      console.log('❌ Conditions not met for starting interview');
    }
  }, [isConnected]); // Remove interviewStarted from dependencies to prevent loops

  // For coding interviews, default to showing code editor instead of canvas
  const [serverInterviewType, setServerInterviewType] = useState('');
  const isCodingInterview = (formData.interviewType === 'coding') || (serverInterviewType === 'coding');
  const [codingProblemLoaded, setCodingProblemLoaded] = useState(false);
  const [currentHints, setCurrentHints] = useState('');
  
  // Timer state for coding problems
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [timerActive, setTimerActive] = useState(false);
  const [currentDifficulty, setCurrentDifficulty] = useState('');
  const timerRef = useRef(null);

  // Fetch coding problem for coding interviews
  useEffect(() => {
    if (isCodingInterview && sessionId && interviewPhase === 'questioning' && !codingProblemLoaded) {
      fetchCodingProblem();
    }
  }, [isCodingInterview, sessionId, interviewPhase, codingProblemLoaded]);

  // Timer effect for coding problems
  useEffect(() => {
    if (timerActive && timerSeconds > 0) {
      timerRef.current = setInterval(() => {
        setTimerSeconds(prev => {
          if (prev <= 1) {
            setTimerActive(false);
            handleTimeUp();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      clearInterval(timerRef.current);
    }

    return () => clearInterval(timerRef.current);
  }, [timerActive, timerSeconds]);

  // Handle when time runs out
  const handleTimeUp = async () => {
    console.log('⏰ Time is up! Evaluating current code...');
    
    // Get current code from the code editor
    const currentCode = codeTemplate; // This should be updated to get actual code from editor
    
    // Create a message about time being up
    const timeUpMessage = {
      id: `timeup_${Date.now()}`,
      role: 'assistant',
      content: `⏰ Time's up! Let's review what you've written so far and discuss your approach.`,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, timeUpMessage]);
    
    // TODO: Send code for evaluation and get follow-up questions
    // This would call a backend endpoint to analyze the code and generate follow-ups
  };

  // Start timer for coding problem
  const startCodingTimer = (difficulty) => {
    const timeInMinutes = difficulty.toLowerCase() === 'hard' ? 45 : 30;
    const timeInSeconds = timeInMinutes * 60;
    
    console.log(`⏱️ Starting timer: difficulty=${difficulty}, minutes=${timeInMinutes}, seconds=${timeInSeconds}`);
    
    setCurrentDifficulty(difficulty);
    setTimerSeconds(timeInSeconds);
    setTimerActive(true);
    
    console.log(`⏱️ Timer state set: timerSeconds=${timeInSeconds}, timerActive=true`);
  };

  // Stop timer (when user submits)
  const stopCodingTimer = () => {
    setTimerActive(false);
    setTimerSeconds(0);
    clearInterval(timerRef.current);
  };

  // Handle code submission
  const handleCodeSubmission = async () => {
    console.log('📝 User submitted code');
    
    // Stop the timer
    stopCodingTimer();
    
    if (!currentCode.trim()) {
      console.warn('⚠️ No code to submit');
      return;
    }
    
    try {
      // Submit code to backend for evaluation (no code dump in chat)
      const response = await fetch(`${config.API_BASE_URL}/coding/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          problem_id: currentQuestion?.id || 'current_problem',
          code: currentCode,
          language: 'python' // TODO: Get selected language from CodeEditor
        })
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        // Add clean submission summary (no code dump)
        const submissionMessage = {
          id: `submission_${Date.now()}`,
          role: 'assistant',
          content: result.message, // Clean summary with test results and complexity
          timestamp: new Date(),
          type: 'submission_result'
        };
        
        setMessages(prev => [...prev, submissionMessage]);
        
        // Add natural language follow-up question if provided
        if (result.followUpQuestion) {
          setIsInFollowUp(true); // Set follow-up state
          const followUpMessage = {
            id: `followup_${Date.now()}`,
            role: 'assistant',
            content: result.followUpQuestion,
            timestamp: new Date(),
            type: 'follow_up_question',
            followUpCount: result.followUpCount,
            maxFollowUps: result.maxFollowUps
          };
          
          setMessages(prev => [...prev, followUpMessage]);
        } else if (result.followUpCount >= result.maxFollowUps) {
          // All follow-ups completed
          const completionMessage = {
            id: `completion_${Date.now()}`,
            role: 'assistant',
            content: "Excellent work! We've covered all the key aspects of your solution. You demonstrated strong problem-solving skills and technical understanding. Ready for the next challenge?",
            timestamp: new Date(),
            type: 'completion'
          };
          
          setMessages(prev => [...prev, completionMessage]);
        }
      } else {
        throw new Error(result.error || 'Submission failed');
      }
      
    } catch (error) {
      console.error('Failed to submit code:', error);
      const errorMessage = {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: `Failed to submit code: ${error.message}. Please try again.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  // Format timer display
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Process inline formatting like **bold text**
  const processInlineFormatting = (text) => {
    const parts = [];
    let currentIndex = 0;
    
    // Find all **text** patterns
    const boldPattern = /\*\*(.*?)\*\*/g;
    let match;
    
    while ((match = boldPattern.exec(text)) !== null) {
      // Add text before the match
      if (match.index > currentIndex) {
        parts.push(text.slice(currentIndex, match.index));
      }
      
      // Add the bold text
      parts.push(
        <strong key={`bold-${match.index}`} style={{ fontWeight: 'bold' }}>
          {match[1]}
        </strong>
      );
      
      currentIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (currentIndex < text.length) {
      parts.push(text.slice(currentIndex));
    }
    
    return parts.length > 1 ? parts : text;
  };

  // Format coding problem content with proper styling
  const formatCodingProblem = (content) => {
    if (!content) return null;
    
    const lines = content.split('\n');
    const elements = [];
    let currentSection = [];
    let sectionType = 'normal';
    
    lines.forEach((line, index) => {
      const trimmedLine = line.trim();
      
      // Handle titles (lines starting with **)
      if (trimmedLine.startsWith('**') && trimmedLine.endsWith('**') && trimmedLine.length > 4) {
        // Flush current section
        if (currentSection.length > 0) {
          elements.push(renderSection(currentSection, sectionType, elements.length));
          currentSection = [];
        }
        
        const title = trimmedLine.slice(2, -2);
        // Check if it's a main title (contains difficulty) or subtitle
        const isMainTitle = title.includes('(Hard)') || title.includes('(Medium)') || title.includes('(Easy)');
        
        elements.push(
          <h3 key={`title-${elements.length}`} style={{
            fontSize: isMainTitle ? '20px' : '16px',
            fontWeight: 'bold',
            margin: isMainTitle ? '20px 0 12px 0' : '12px 0 6px 0',
            color: '#2c3e50'
          }}>
            {title}
          </h3>
        );
        sectionType = 'normal';
      }
      // Handle code blocks
      else if (trimmedLine === '```') {
        // Flush current section
        if (currentSection.length > 0) {
          elements.push(renderSection(currentSection, sectionType, elements.length));
          currentSection = [];
        }
        sectionType = sectionType === 'code' ? 'normal' : 'code';
      }
      // Handle bullet points
      else if (trimmedLine.startsWith('•') || trimmedLine.startsWith('-')) {
        if (sectionType !== 'list') {
          // Flush current section
          if (currentSection.length > 0) {
            elements.push(renderSection(currentSection, sectionType, elements.length));
            currentSection = [];
          }
          sectionType = 'list';
        }
        currentSection.push(trimmedLine.replace(/^[•-]\s*/, ''));
      }
      // Regular content
      else if (trimmedLine) {
        if (sectionType === 'list') {
          // Flush list section
          elements.push(renderSection(currentSection, sectionType, elements.length));
          currentSection = [];
          sectionType = 'normal';
        }
        currentSection.push(line);
      }
      // Empty lines
      else if (currentSection.length > 0) {
        currentSection.push('');
      }
    });
    
    // Flush remaining section
    if (currentSection.length > 0) {
      elements.push(renderSection(currentSection, sectionType, elements.length));
    }
    
    return <div>{elements}</div>;
  };

  // Render different section types
  const renderSection = (lines, type, key) => {
    if (lines.length === 0) return null;
    
    switch (type) {
      case 'code':
        return (
          <pre key={`code-${key}`} style={{
            backgroundColor: 'transparent',
            border: 'none',
            padding: '8px 0',
            margin: '8px 0',
            fontSize: '14px',
            fontFamily: 'Monaco, Consolas, monospace',
            overflow: 'auto',
            whiteSpace: 'pre-wrap'
          }}>
            {lines.join('\n')}
          </pre>
        );
      case 'list':
        return (
          <ul key={`list-${key}`} style={{
            margin: '8px 0',
            paddingLeft: '20px'
          }}>
            {lines.map((item, idx) => (
              <li key={idx} style={{ margin: '4px 0' }}>{item}</li>
            ))}
          </ul>
        );
      default:
        return (
          <div key={`text-${key}`} style={{
            margin: '8px 0',
            lineHeight: '1.5'
          }}>
            {lines.map((line, idx) => (
              <div key={idx}>
                {line ? processInlineFormatting(line) : <br />}
              </div>
            ))}
          </div>
        );
    }
  };

  const fetchCodingProblem = async () => {
    // Prevent multiple simultaneous calls
    if (codingProblemLoaded) {
      console.log('⚠️ Coding problem already loaded, skipping...');
      return;
    }
    
    // Set flag immediately to prevent race conditions
    setCodingProblemLoaded(true);
    
    try {
      // Background generation should have the problem ready - request immediately
      console.log('🎯 Requesting pre-generated coding problem...');
      const response = await fetch(`${config.API_BASE_URL}/interview/next-coding-problem?session_id=${sessionId}`);
      const data = await response.json();
      
      if (data.status === 'success' && data.problem) {
        // Clear messages for clean coding problem display (only on success)
        setMessages([]);
        
        // Debug: Log the received data to see what we're getting
        console.log('🔍 Received problem data:', JSON.stringify(data.problem, null, 2));
        
        // Build detailed, well-formatted message for chat
        const titleLine = `**${data.problem.title}** (${data.problem.difficulty})`;
        
        // Format example properly - handle both string and object formats
        let exampleSection = "**Example 1:**";
        if (data.problem.example) {
          console.log('🔍 Example type:', typeof data.problem.example, 'Value:', data.problem.example);
          if (typeof data.problem.example === 'object' && data.problem.example !== null) {
            const input = typeof data.problem.example.input === 'object' 
              ? JSON.stringify(data.problem.example.input) 
              : (data.problem.example.input || 'N/A');
            const output = typeof data.problem.example.output === 'object' 
              ? JSON.stringify(data.problem.example.output) 
              : (data.problem.example.output || 'N/A');
            const explanation = data.problem.example.explanation || '';
            
            exampleSection += `\n\`\`\`\nInput: ${input}\nOutput: ${output}\n\`\`\``;
            if (explanation) {
              exampleSection += `\n**Explanation:** ${explanation}`;
            }
          } else {
            exampleSection += `\n${data.problem.example}`;
          }
        } else {
          exampleSection += "\nNo example provided";
        }

        // Add test cases if available
        let testCasesSection = "";
        if (data.problem.testCases && data.problem.testCases.length > 0) {
          testCasesSection = "\n**Test Cases:**";
          data.problem.testCases.slice(0, 3).forEach((testCase, index) => {
            if (typeof testCase === 'object') {
              const tcInput = typeof testCase.input === 'object' ? JSON.stringify(testCase.input) : (testCase.input || 'N/A');
              const tcExpected = typeof testCase.expected === 'object' 
                ? JSON.stringify(testCase.expected) 
                : (testCase.expected || testCase.output || 'N/A');
              testCasesSection += `\n\`\`\`\nTest Case ${index + 1}:\nInput: ${tcInput}\nExpected Output: ${tcExpected}\n\`\`\``;
            }
          });
        }

        let constraintsSection = "";
        if (data.problem.constraints && data.problem.constraints.length > 0) {
          constraintsSection = "\n**Constraints:**";
          data.problem.constraints.forEach(constraint => {
            constraintsSection += `\n• ${constraint}`;
          });
        }

        // Store algorithm hints separately for the hint button
        const algorithmHints = `💡 **Algorithm Pattern:** ${data.problem.primaryPattern || 'Not specified'}

🔧 **Key Data Structures:** ${data.problem.dataStructures || 'Not specified'}

⏱️ **Target Complexity:** ${data.problem.optimalComplexity?.time || 'Not specified'} time, ${data.problem.optimalComplexity?.space || 'Not specified'} space

💭 **Approach Hints:**
• Think about the most efficient way to solve this step by step
• Consider edge cases like empty inputs, single elements, or maximum constraints
• Look for patterns that can help optimize your solution`;

        const messageText = [
          titleLine,
          '',
          data.problem.problemStatement,
          '',
          exampleSection,
          testCasesSection,
          constraintsSection,
          '',
          '📝 **Need clarification?** Press the mic button anytime to ask questions about this problem.',
          '',
          'Write your solution in the code editor on the right. You can choose your preferred programming language from the dropdown.'
        ].filter(section => section.trim() !== '').join('\n');

        const problemMessage = {
          id: `problem_${Date.now()}`,
          role: 'assistant',
          content: messageText,
          timestamp: new Date(),
          isCodingProblem: true
        };
        setMessages([problemMessage]);
        
        // Set the hints for this specific problem
        setCurrentHints(algorithmHints);
        
        // Set the code editor content with the template (now supports multiple languages)
        if (data.problem.template) {
          setCodeTemplate(data.problem.template);
        }
        
        // Start the timer based on difficulty
        if (data.problem.difficulty) {
          console.log(`🔍 About to start timer with difficulty: ${data.problem.difficulty}`);
          startCodingTimer(data.problem.difficulty);
        } else {
          console.log('⚠️ No difficulty found in problem data');
        }
        
        // codingProblemLoaded already set to true at the start
      } else {
        // Handle API errors (like rate limits) - reset flag so user can try again
        setCodingProblemLoaded(false);
        const errorMessage = {
          id: `error_${Date.now()}`,
          role: 'assistant',
          content: `Unable to generate coding problem: ${data.error || 'API service temporarily unavailable'}. This is likely due to API rate limits. Please wait a moment and refresh the page to try again.`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Failed to fetch coding problem:', error);
      // Reset flag on error so user can try again
      setCodingProblemLoaded(false);
      const errorMessage = {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: 'Failed to connect to coding problem service. This might be due to API rate limits or network issues. Please wait a moment and refresh the page to try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const startInterview = async () => {
    // Prevent multiple simultaneous calls
    if (interviewStarted) {
      console.log('⚠️ Interview already started, skipping...');
      return;
    }

    try {
      console.log('🚀 Starting interview with formData:', formData);
      console.log('🚀 Topic:', topic);
      
      // Set interview started immediately to prevent race conditions
      setInterviewStarted(true);
      
      const requestBody = { 
        formData: formData
      };
      console.log('📤 Request body:', requestBody);
      console.log('📤 Request body JSON:', JSON.stringify(requestBody));
      
      console.log('🌐 Making fetch request to:', `${config.API_BASE_URL}/interview/start`);
      const response = await fetch(`${config.API_BASE_URL}/interview/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      
      console.log('📡 Fetch completed. Response object:', response);
      
      console.log('📡 Response status:', response.status);
      console.log('📡 Response ok:', response.ok);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('📥 Backend response:', data);
      console.log('📥 Response status:', data.status);
      console.log('📥 Response message:', data.message);
      console.log('📥 Full response object:', JSON.stringify(data, null, 2));

      // New flow: backend returns greeting first
      console.log('🔍 Checking condition: data exists?', !!data);
      console.log('🔍 data.status === "greeting_shown"?', data?.status === 'greeting_shown');
      console.log('🔍 data.message exists?', !!data?.message);
      console.log('🔍 Overall condition result:', data && (data.status === 'greeting_shown' || data.message));
      
      if (data && (data.status === 'greeting_shown' || data.status === 'brief_introduction_required' || data.message)) {
        console.log('✅ Got greeting, setting up interview...');
        console.log('✅ Condition check passed - data.status:', data.status, 'data.message exists:', !!data.message);
        
        setSessionId(data.session_id);
        // Capture normalized interview type from backend
        if (data?.interview_info?.interview_type) {
          setServerInterviewType(data.interview_info.interview_type);
        }
        
        // Set appropriate phase based on interview type
        if (data.status === 'brief_introduction_required' && !isCodingInterview) {
          setInterviewPhase('brief_introduction');
          console.log('🎯 Set to brief_introduction phase for technical interview');
        } else {
          setInterviewPhase('awaiting_introduction');
          console.log('🎯 Set to awaiting_introduction phase for technical+behavioral interview');
        }

        const aiMessage = {
          id: `greeting_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          role: 'assistant',
          content: data.message || 'Welcome! Please introduce yourself and tell me what interests you about this role.',
          timestamp: new Date()
        };
        console.log('💬 Adding AI message to chat:', aiMessage);
        console.log('💬 Message content:', aiMessage.content);
        
        // Use functional update to ensure we get the latest state
        setMessages(prevMessages => {
          console.log('💬 Previous messages length:', prevMessages.length);
          const newMessages = [aiMessage];
          console.log('💬 New messages length:', newMessages.length);
          return newMessages;
        });
        
        // Note: TTS will be triggered by useEffect watching messages
        
        // Force a re-render check
        setTimeout(() => {
          console.log('🔄 Checking messages state after timeout...');
        }, 100);
        
      } else {
        console.log('❌ Condition failed!');
        console.log('❌ data:', data);
        console.log('❌ data.status:', data.status);
        console.log('❌ data.message:', data.message);
        // Fallback to old behavior if backend not updated
        setCurrentQuestion(data);
        const aiMessage = {
          id: `fallback_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          role: 'assistant',
          content: data.question || 'Welcome to the interview! Please introduce yourself.',
          timestamp: new Date()
        };
        setMessages([aiMessage]);
        setInterviewPhase('questioning');
      }
      
    } catch (error) {
      console.error('❌ Failed to start interview:', error);
      
      // Create fallback greeting message
      const errorMessage = {
        id: `error_fallback_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: `Hello ${formData?.username || 'there'}! I'm your AI interviewer. I'm excited to learn about your background and experience in ${formData?.position || 'your field'}. Could you please start by introducing yourself and telling me what interests you about this role?`,
        timestamp: new Date()
      };
      
      setMessages([errorMessage]);
      setInterviewPhase('awaiting_introduction');
      
      // Ensure interview started flag is still set even on error
      if (!interviewStarted) {
        setInterviewStarted(true);
      }
    }
  };

  const fetchNextQuestion = async () => {
    if (!sessionId) {
      console.log('❌ No sessionId available for fetchNextQuestion');
      return;
    }
    try {
      console.log('🔍 Fetching next question for session:', sessionId);
        const res = await fetch(`${config.API_BASE_URL}/interview/next-question?session_id=${encodeURIComponent(sessionId)}`);
      const data = await res.json();
      console.log('📋 Next question response:', JSON.stringify(data, null, 2));
      
      if (data.status === 'active') {
        // New conversational flow: backend may not return a specific question here.
        if (data.question && data.question.text) {
          console.log('✅ Got active question:', data.question.text);
          setCurrentQuestion(data.question);
          setInterviewPhase('questioning');
          const aiMessage = {
            id: `question_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: 'assistant',
            content: data.question.text,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, aiMessage]);
        } else if (data.message) {
          // Status-only response: surface the message to user to avoid confusion
          console.log('ℹ️ Status active (no question). Showing message from server.');
          const statusMsg = {
            id: `status_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: 'assistant',
            content: data.message,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, statusMsg]);
        } else {
          console.log('ℹ️ Status active with no question/message; conversation continues.');
        }
        // Do not treat as error
      } else if (data.status === 'completed') {
        console.log('🎉 Interview completed! Navigating to results...');
        // Navigate to results page
        navigate('/results', { state: { sessionId } });
      } else if (data.status === 'introduction_required') {
        console.log('⚠️ Introduction required');
        setInterviewPhase('awaiting_introduction');
        const msg = {
          id: `intro_required_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          role: 'assistant',
          content: data.greeting_message || 'Please introduce yourself and tell me what interests you about this role.',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, msg]);
      } else {
        // Treat any other status as informational to avoid false errors
        console.log('ℹ️ Informational response status:', data.status);
      }
    } catch (e) {
      console.error('Failed to get next question:', e);
    }
  };

  // Send message function (can be called with custom text)
  const sendMessage = async (messageText) => {
    if (!messageText.trim()) return;
    // Prevent sending messages after interview completion to avoid loops
    if (interviewPhase === 'completed') {
      const infoMessage = {
        id: `completed_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: 'Thanks for your question! This interview session is complete. We\'ll include your question in the final report.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, infoMessage]);
      // In text mode, navigate right away
      if (inputMode === 'text' && sessionId) {
        setTimeout(() => navigate('/results', { state: { sessionId } }), 600);
      }
      return;
    }
    
    const userMessage = {
      id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      role: 'user',
      content: messageText,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      // Handle company Q&A phase
      if (interviewPhase === 'company_qna' && sessionId) {
        console.log('🏢 Submitting company Q&A response...');
        const res = await fetch(`${config.API_BASE_URL}/interview/submit-company-question`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            session_id: sessionId, 
            response: messageText 
          })
        });
        
        const data = await res.json();
        console.log('🏢 Company Q&A response:', JSON.stringify(data, null, 2));
        
        if (data.status === 'success') {
          // Continue company Q&A
          const aiMessage = {
            id: `company_ai_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: 'assistant',
            content: data.message,
            timestamp: new Date(),
            type: 'company_qna'
          };
          setMessages(prev => [...prev, aiMessage]);
        } else if (data.status === 'completed') {
          // Company Q&A completed, show final message and navigate
          const finalMessage = {
            id: `company_final_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: 'assistant',
            content: data.message,
            timestamp: new Date(),
            type: 'interview_completion',
            navigateOnTTSComplete: true
          };
          setMessages(prev => [...prev, finalMessage]);
          setInterviewPhase('completed');
          // If in text mode, navigate after showing final message
          if (inputMode === 'text' && sessionId) {
            setTimeout(() => navigate('/results', { state: { sessionId } }), 800);
          }
        } else if (data.error) {
          const errorMessage = {
            id: `company_error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: 'assistant',
            content: 'Sorry, there was an error processing your question. Please try again.',
            timestamp: new Date()
          };
          setMessages(prev => [...prev, errorMessage]);
        }
        return;
      }
      
      // If regular introduction for technical+behavioral interview
      if (interviewPhase === 'awaiting_introduction' && sessionId) {
        const res = await fetch(`${config.API_BASE_URL}/interview/introduce`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId, introduction: messageText })
        });
        
        const data = await res.json();
        console.log('📋 Introduction response:', JSON.stringify(data, null, 2));
        
        if (data.status === 'success') {
          // Coding flow: go straight to coding question
          if (isCodingInterview && data.next_action === 'ready_for_questions') {
            setInterviewPhase('questioning');
            setShowCodeEditor(true);
            // Don't clear messages here - let fetchCodingProblem handle success/error
            await fetchCodingProblem();
            return;
          }

          // Check if there's a follow-up question from the introduction
          if (data.next_action === 'needs_followup' && data.follow_up_question) {
            // For coding interview, ignore follow-ups and start coding immediately
            if (isCodingInterview) {
              setInterviewPhase('questioning');
              setShowCodeEditor(true);
              await fetchCodingProblem();
              return;
            }
            const followUpMessage = {
              id: `assistant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
              role: 'assistant',
              content: data.follow_up_question,
              timestamp: new Date()
            };
            setMessages(prev => [...prev, followUpMessage]);
            // Stay in awaiting_introduction phase for follow-ups
          } else if (data.next_action === 'ready_for_questions') {
            setInterviewPhase('technical_questions');
            // Fetch the first technical question
            await fetchNextQuestion();
          }
        } else if (data.error) {
          console.error('❌ Error submitting introduction:', data.error);
          if (isCodingInterview) {
            // Proceed anyway for coding interviews — intro shouldn't block
            setInterviewPhase('questioning');
            setShowCodeEditor(true);
            await fetchCodingProblem();
          } else {
            const errorMessage = {
              id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
              role: 'assistant',
              content: 'Sorry, there was an error processing your introduction. Please try again.',
              timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
          }
        }
      } else if (interviewPhase === 'brief_introduction' && sessionId) {
        const res = await fetch(`${config.API_BASE_URL}/interview/brief-introduce`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId, introduction: messageText })
        });
        
        const data = await res.json();
        console.log('📋 Brief introduction response:', JSON.stringify(data, null, 2));
        
        if (data.status === 'success' && data.next_action === 'ready_for_questions') {
          if (isCodingInterview) {
            setInterviewPhase('questioning');
            setShowCodeEditor(true);
            await fetchCodingProblem();
          } else {
            setInterviewPhase('technical_questions');
            // Fetch the first technical question
            await fetchNextQuestion();
          }
        } else if (data.error) {
          console.error('❌ Error submitting brief introduction:', data.error);
          const errorMessage = {
            id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: 'assistant',
            content: 'Sorry, there was an error processing your introduction. Please try again.',
            timestamp: new Date()
          };
          setMessages(prev => [...prev, errorMessage]);
        }
      } else if (showCodeEditor && !isInFollowUp && sessionId) {
        // Handle clarification questions during coding phase (before code submission)
        console.log('❓ Asking clarification question...');
        const res = await fetch(`${config.API_BASE_URL}/coding/clarify`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            session_id: sessionId, 
            question: messageText 
          })
        });
        
        const data = await res.json();
        console.log('📋 Clarification response:', JSON.stringify(data, null, 2));
        
        if (data.status === 'success') {
          const clarificationMessage = {
            id: `clarification_${Date.now()}`,
            role: 'assistant',
            content: data.message,
            timestamp: new Date(),
            type: 'clarification',
            silent: data.silent || false,  // Flag to prevent TTS
            keepMicManual: data.keepMicManual || false  // Flag to keep mic manual
          };
          setMessages(prev => [...prev, clarificationMessage]);
        } else {
          const errorMessage = {
            id: `error_${Date.now()}`,
            role: 'assistant',
            content: data.message || 'Sorry, I couldn\'t process your clarification question. Please try again.',
            timestamp: new Date()
          };
          setMessages(prev => [...prev, errorMessage]);
        }
      } else if (isInFollowUp && sessionId) {
        // Handle follow-up question answer for coding interviews
        console.log('📤 Submitting follow-up answer...');
        const res = await fetch(`${config.API_BASE_URL}/coding/followup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            session_id: sessionId, 
            answer: messageText 
          })
        });
        
        const data = await res.json();
        console.log('📋 Follow-up response:', JSON.stringify(data, null, 2));
        
        if (data.status === 'success' && data.followUpQuestion) {
          // Continue with next follow-up question
          const followUpMessage = {
            id: `followup_${Date.now()}`,
            role: 'assistant',
            content: data.followUpQuestion,
            timestamp: new Date(),
            type: 'follow_up_question',
            followUpCount: data.followUpCount,
            maxFollowUps: data.maxFollowUps
          };
          setMessages(prev => [...prev, followUpMessage]);
        } else if (data.status === 'problem_completed') {
          // All follow-ups completed, move to next problem
          setIsInFollowUp(false);
          const completionMessage = {
            id: `completion_${Date.now()}`,
            role: 'assistant',
            content: data.message,
            timestamp: new Date(),
            type: 'problem_completion'
          };
          setMessages(prev => [...prev, completionMessage]);
          
          // Fetch next coding problem after a brief delay
          setTimeout(() => {
            fetchCodingProblem();
          }, 2000);
        } else if (data.status === 'interview_completed') {
          // Interview completed after follow-ups
          setIsInFollowUp(false);
          const completionMessage = {
            id: `completion_${Date.now()}`,
            role: 'assistant',
            content: data.message,
            timestamp: new Date(),
            type: 'interview_completion',
            navigateOnTTSComplete: true  // Flag to navigate after TTS completes
          };
          setMessages(prev => [...prev, completionMessage]);
        } else if (data.status === 'success' && !data.followUpQuestion) {
          // No more follow-ups, but problem not marked complete
          setIsInFollowUp(false);
          const thankYouMessage = {
            id: `thanks_${Date.now()}`,
            role: 'assistant',
            content: data.message || "Thank you for your detailed explanation!",
            timestamp: new Date()
          };
          setMessages(prev => [...prev, thankYouMessage]);
        }
      } else if (sessionId && currentQuestion) {
        // Submit answer to current question
        const res = await fetch(`${config.API_BASE_URL}/interview/answer`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            session_id: sessionId, 
            question_id: currentQuestion.id || currentQuestion.question_id || 'current_question',
            answer: messageText 
          })
        });
        
        const data = await res.json();
        console.log('📋 Answer submission response:', JSON.stringify(data, null, 2));
        
        // Handle interview completion and company Q&A transition
        if (data.status === 'completed' || data.next_action === 'interview_complete') {
          // Final completion - navigate to results
          const completionMessage = {
            id: `completion_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: 'assistant',
            content: data.message || 'Thank you! Your detailed feedback will be ready shortly.',
            timestamp: new Date(),
            type: 'interview_completion',
            navigateOnTTSComplete: true
          };
          setMessages(prev => [...prev, completionMessage]);
          setInterviewPhase('completed');
          // If in text mode (no TTS), navigate shortly after showing closing prompt
          if (inputMode === 'text' && sessionId) {
            setTimeout(() => navigate('/results', { state: { sessionId } }), 800);
          }
          return;
        } else if (data.next_action === 'start_company_qna') {
          // Interview completed, start company Q&A phase
          const closingMessage = {
            id: `closing_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: 'assistant',
            content: data.message,
            timestamp: new Date(),
            type: 'company_qna_start'
          };
          setMessages(prev => [...prev, closingMessage]);
          setInterviewPhase('company_qna');
          
          // Start the company Q&A phase
          try {
            const companyRes = await fetch(`${config.API_BASE_URL}/interview/start-company-qna`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ session_id: sessionId })
            });
            const companyData = await companyRes.json();
            console.log('🏢 Company Q&A started:', companyData);
          } catch (error) {
            console.error('❌ Error starting company Q&A:', error);
          }
          return;
        }

        if (data.status === 'success') {
          // Handle AI Conductor system responses
          if (data.next_action === 'continue_conversation' && data.message) {
            const aiMessage = {
              id: `assistant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
              role: 'assistant',
              content: data.message,
              timestamp: new Date()
            };
            setMessages(prev => [...prev, aiMessage]);
          } 
          // Legacy system responses
          else if (data.next_action === 'follow_up' && data.follow_up_question) {
            const followUpMessage = {
              id: `assistant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
              role: 'assistant',
              content: data.follow_up_question,
              timestamp: new Date()
            };
            setMessages(prev => [...prev, followUpMessage]);
          } else if (data.next_action === 'next_question') {
            // Fetch the next question
            await fetchNextQuestion();
          }
        } else if (data.error) {
          console.error('❌ Error submitting answer:', data.error);
          const errorMessage = {
            id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: 'assistant',
            content: 'Sorry, there was an error processing your answer. Please try again.',
            timestamp: new Date()
          };
          setMessages(prev => [...prev, errorMessage]);
        }
      } else if (sessionId) {
        console.log('⚠️ No current question available, fetching next question...');
        await fetchNextQuestion();
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  // Handlers
  const handleSendMessage = async () => {
    if (!inputText.trim()) return;
    const text = inputText;
    setInputText('');
    await sendMessage(text);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSendMessage();
    }
  };

  // Voice recording (aligned with Practice page)
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Choose best supported mime type
      let mimeType = 'audio/webm';
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4';
      } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
        mimeType = 'audio/ogg;codecs=opus';
      }
      
      const recorder = new MediaRecorder(stream, { mimeType });
      const chunks = [];
      
      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: mimeType });
        if (audioBlob.size > 0) {
          await transcribeAndFillInput(audioBlob);
        } else {
          alert('No audio was recorded. Please try again.');
        }
        stream.getTracks().forEach(track => track.stop());
      };
      
      recorder.start(1000); // collect data every 1s
      setMediaRecorder(recorder);
      setIsRecording(true);
      setAudioChunks([]);
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
      const formData = new FormData();
      // Pick filename based on blob type
      let filename = 'audio.webm';
      if (audioBlob.type.includes('mp4')) filename = 'audio.mp4';
      else if (audioBlob.type.includes('ogg')) filename = 'audio.ogg';
      formData.append('file', audioBlob, filename);
      
      const response = await fetch(`${config.API_BASE_URL}/transcribe`, {
        method: 'POST',
        body: formData,
      });
      
      const result = await response.json();
      if (result.success && result.transcription) {
        const transcribedText = result.transcription.trim();
        
        if (inputMode === 'voice') {
          // In voice mode: auto-send the transcribed text immediately
          if (transcribedText) {
            await sendMessage(transcribedText);
          }
        } else {
          // In text mode: fill the input field as before
          setInputText(transcribedText);
        }
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

  const handleAnalyze = () => {
    // Get current text from input
    const userResponse = inputText.trim();
    
    if (!userResponse && (!fabricCanvas || fabricCanvas.isEmpty())) {
      alert('Please type your response or draw something on the canvas first.');
      return;
    }
    
    setIsAnalyzing(true);
    
    // Get canvas data first
    let imageData = '';
    let hasImage = false;
    try {
      if (fabricCanvas && !fabricCanvas.isEmpty()) {
        imageData = fabricCanvas.toDataURL('image/png');
        hasImage = true;
      } else {
        const canvas = document.createElement('canvas');
        canvas.width = 800;
        canvas.height = 600;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, 800, 600);
        imageData = canvas.toDataURL('image/png');
      }
    } catch (error) {
      console.error('Error getting canvas data:', error);
      const canvas = document.createElement('canvas');
      canvas.width = 800;
      canvas.height = 600;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, 800, 600);
      imageData = canvas.toDataURL('image/png');
    }

    // Add user's response (text + image) to chat immediately
    const userMessage = {
      id: `user_drawing_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      role: 'user',
      content: userResponse || 'Submitted drawing for analysis',
      image: hasImage ? imageData : null, // Include image if canvas has content
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    if (userResponse) {
      setInputText(''); // Clear input after sending
    }
    
    // Send both drawing and text to selected AI model for analysis
    if (wsRef.current && isConnected) {
      const success = wsRef.current.sendWhiteboardAnalysis(
        imageData, 
        userResponse || 'User submitted drawing for analysis'
      );
      
      if (!success) {
        setTimeout(() => {
          const aiMessage = {
            id: `analysis_fallback_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: 'assistant',
            content: 'I can see your approach. How would you optimize this design for better performance?',
            timestamp: new Date()
          };
          setMessages(prev => [...prev, aiMessage]);
          setIsAnalyzing(false);
        }, 1500);
      }
    } else {
      // Demo response when not connected
      setTimeout(() => {
        const aiMessage = {
          id: `demo_response_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          role: 'assistant',
          content: 'Interesting solution! Can you walk me through how you would handle failure scenarios in this design?',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiMessage]);
        setIsAnalyzing(false);
      }, 1500);
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

  // Code editor toggle handlers
  const handleOpenCodeEditor = () => {
    try {
      if (fabricCanvas) {
        fabricCanvas.dispose();
        setFabricCanvas(null);
      }
    } catch (e) {
      console.warn('Canvas dispose warning:', e);
    }
    setShowCodeEditor(true);
  };

  const handleCloseCodeEditor = () => {
    setShowCodeEditor(false);
    // Recreate canvas after editor hides
    setTimeout(() => {
      createFabricCanvas();
    }, 0);
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <button className="icon-btn">
            <ArrowLeft size={20} />
          </button>
          <h1 className="topic">{topic}</h1>
          <div className="connection-status">
            <div className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></div>
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
        <div className="header-right">
          <div className="timer">
            <Timer size={16} />
            <span style={{ 
              color: isCodingInterview ? (timerSeconds < 300 ? '#ef4444' : '#059669') : '#6b7280'
            }}>
              {isCodingInterview ? (timerSeconds > 0 ? formatTime(timerSeconds) : '00:00') : '00:15'}
            </span>
          </div>
          <button 
            className="icon-btn" 
            onClick={() => {
              if (currentHints) {
                alert(currentHints);
              } else {
                alert('No hints available for this question.');
              }
            }}
            title={currentHints ? 'Show algorithm hints' : 'No hints available'}
          >
            <HelpCircle size={20} />
          </button>
          <button 
            className="primary-btn"
            onClick={() => {
              if (sessionId) {
                navigate('/results', { state: { sessionId } });
              } else {
                navigate('/dashboard');
              }
            }}
          >
            {sessionId ? 'View Results' : 'Exit Interview'}
          </button>
          <button className="icon-btn">
            <Info size={20} />
          </button>
        </div>
      </header>

      {/* Main Content - True 50/50 Split */}
      <main className="main">
        {/* Left Panel - Chat */}
        <section className="chat-section">

          <div className="messages-container">
            {(() => {
              console.log('🎨 Rendering messages container, count:', messages.length);
              console.log('🎨 Messages array:', messages);
              return null;
            })()}
            {messages.length === 0 ? (
              <div className="empty-state">
                <MessageCircle size={48} className="empty-icon" />
                <h3>Ready to Begin</h3>
                <p>Start the conversation. I'll provide feedback and ask follow-up questions.</p>
              </div>
            ) : (
              <>
                {console.log('🎨 Rendering messages, count:', messages.length)}
                {(() => {
                  const ids = messages.map(m => m.id);
                  const duplicates = ids.filter((id, index) => ids.indexOf(id) !== index);
                  if (duplicates.length > 0) {
                    console.error('❌ DUPLICATE MESSAGE IDs DETECTED:', duplicates);
                    console.error('❌ All message IDs:', ids);
                  } else {
                    console.log('✅ All message IDs are unique');
                  }
                  return null;
                })()}
                {messages.map((message, index) => {
                  console.log(`🎨 Rendering message ${index}:`, message);
                  return (
                    <div key={message.id} className={`message ${message.role}`}>
                      <div className="message-content">
                        <div className="message-header">
                          <span className="sender">{message.role === 'user' ? 'You' : 'AI Interviewer'}</span>
                          <span className="timestamp">
                            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <div className="message-text">
                          {message.isCodingProblem ? (
                            <div className="coding-problem-formatted">
                              {formatCodingProblem(message.content)}
                            </div>
                          ) : (
                            message.content
                          )}
                          {message.image && (
                            <div className="message-image">
                              <img src={message.image} alt="User drawing" style={{maxWidth: '300px', margin: '10px 0', border: '1px solid #ddd', borderRadius: '8px'}} />
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
                {isAnalyzing && (
                  <div className="message assistant analyzing">
                    <div className="message-content">
                      <div className="message-header">
                        <span className="sender">AI Interviewer</span>
                        <span className="timestamp">now</span>
                      </div>
                      <div className="message-text">
                        <div className="typing-indicator">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                        Analyzing your response...
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          <div className="input-section">
            {/* Top controls: input mode toggle (left) + disclaimer (right) */}
            <div className="input-controls">
              <div className="input-mode-toggle" role="group" aria-label="Input mode">
                <button 
                  className={`toggle-option ${inputMode === 'text' ? 'active' : ''}`}
                  onClick={() => setInputMode('text')}
                  title="Text mode"
                  aria-pressed={inputMode === 'text'}
                >
                  <MessageCircle size={16} />
                  <span>Text</span>
                </button>
                <button 
                  className={`toggle-option ${inputMode === 'voice' ? 'active' : ''}`}
                  onClick={() => setInputMode('voice')}
                  title="Voice mode"
                  aria-pressed={inputMode === 'voice'}
                >
                  <Mic size={16} />
                  <span>Voice</span>
                </button>
              </div>
            {interviewPhase === 'questioning' && !isCodingInterview && (
              <div className="drawing-disclaimer">
                <Info size={14} />
                <span>You can draw on the white space and include it in your response to elaborate better on technical concepts.</span>
              </div>
            )}
          </div>
          
          {/* Coding-only bottom panel removed per request; header timer remains */}
            
            {inputMode === 'text' ? (
              <div className="input-area">
                <textarea
                  id="chatMessage"
                  name="chatMessage"
                  className="message-input"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="Share your thoughts, explain your approach, or ask questions..."
                  rows={4}
                  aria-label="Interview chat message"
                />
                <div className="input-actions">
                  <button 
                    className={`record-btn ${isRecording ? 'recording' : ''}`}
                    onClick={toggleRecording}
                    title={isRecording ? 'Stop recording' : 'Click to speak (fills text field)'}
                  >
                    {isRecording ? <Square size={20} /> : <Mic size={20} />}
                    {isRecording && <div className="recording-indicator-dot"></div>}
                  </button>
                  <button 
                    className="send-btn"
                    onClick={handleSendMessage}
                    disabled={!inputText.trim()}
                  >
                    <Send size={20} />
                  </button>
                </div>
              </div>
            ) : (
              <div className="input-area">
                <div className="voice-panel compact" aria-live="polite">
                  <div className="voice-orb swirl" aria-hidden="true"></div>
                  <div className="voice-center">
                    <div className="voice-status">{voiceStatus}</div>
                    <div className={`voice-eq long ${isRecording ? 'listening' : (isAnalyzing ? 'thinking' : (isSpeaking ? 'speaking' : 'ready'))}`} aria-hidden="true">
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                      <span className="eq-bar"></span>
                    </div>
                  </div>
                </div>
                <div className="input-actions">
                  <button 
                    className={`record-btn ${isRecording ? 'recording' : ''}`}
                    onClick={toggleRecording}
                    title={isRecording ? 'Stop listening' : 'Start listening'}
                  >
                    {isRecording ? <Square size={20} /> : <Mic size={20} />}
                    {isRecording && <div className="recording-indicator-dot"></div>}
                  </button>
                  <button 
                    className="send-btn"
                    onClick={handleSendMessage}
                    disabled={!inputText.trim()}
                  >
                    <Send size={20} />
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Right Panel - Canvas */}
        <section className="canvas-section">
          <div className="canvas-area">
            {!showCodeEditor ? (
              <>
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
              </>
            ) : (
              <CodeEditor 
                isVisible={showCodeEditor}
                onClose={handleCloseCodeEditor}
                initialCode={codeTemplate}
                onCodeChange={(code, language) => {
                  setCurrentCode(code);
                  // You could also store the language if needed
                }}
              />
            )}
          </div>

          <div className="canvas-footer">
            <div className="footer-buttons">
              <button 
                className="analyze-button"
                onClick={handleAnalyze}
                disabled={isAnalyzing || !isConnected}
              >
                {isAnalyzing ? 'Analyzing...' : 'Send to Interviewer'}
              </button>
              
              {isCodingInterview && showCodeEditor ? (
                <button 
                  className="analyze-button submit-code-btn"
                  onClick={handleCodeSubmission}
                  disabled={!currentCode.trim() || isAnalyzing}
                  title="Submit your complete solution for review"
                >
                  <Code size={16} />
                  <span>Submit Solution</span>
                </button>
              ) : null}
              
              {isCodingInterview ? null : (
                <button 
                  className="analyze-button code-toggle-btn"
                  onClick={showCodeEditor ? handleCloseCodeEditor : handleOpenCodeEditor}
                  title={showCodeEditor ? "Back to Whitespace" : "Open Code Editor"}
                >
                  <Code size={16} />
                  <span>{showCodeEditor ? 'Back to Whitespace' : 'Code Editor'}</span>
                </button>
              )}
            </div>

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

export default InterviewSession;