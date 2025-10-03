/**
 * Free Speech-to-Text using Web Speech API
 * No API keys required - works in modern browsers
 */

class SpeechRecognitionService {
  constructor() {
    this.recognition = null;
    this.isSupported = false;
    this.isListening = false;
    this.onResult = null;
    this.onError = null;
    this.onEnd = null;
    
    this.initialize();
  }
  
  initialize() {
    // Check for browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.warn('⚠️ Speech Recognition not supported in this browser');
      this.isSupported = false;
      return;
    }
    
    try {
      this.recognition = new SpeechRecognition();
      this.setupRecognition();
      this.isSupported = true;
      console.log('✅ Speech Recognition initialized');
    } catch (error) {
      console.error('❌ Failed to initialize Speech Recognition:', error);
      this.isSupported = false;
    }
  }
  
  setupRecognition() {
    if (!this.recognition) return;
    
    // Configuration
    this.recognition.continuous = false; // Stop after first result
    this.recognition.interimResults = true; // Show interim results
    this.recognition.lang = 'en-US'; // Default language
    this.recognition.maxAlternatives = 1;
    
    // Event handlers
    this.recognition.onstart = () => {
      console.log('🎤 Speech recognition started');
      this.isListening = true;
    };
    
    this.recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';
      
      // Process all results
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }
      
      // Call the result callback
      if (this.onResult) {
        this.onResult({
          final: finalTranscript,
          interim: interimTranscript,
          isFinal: finalTranscript.length > 0
        });
      }
    };
    
    this.recognition.onerror = (event) => {
      console.error('❌ Speech recognition error:', event.error);
      this.isListening = false;
      
      if (this.onError) {
        this.onError(event.error);
      }
    };
    
    this.recognition.onend = () => {
      console.log('🎤 Speech recognition ended');
      this.isListening = false;
      
      if (this.onEnd) {
        this.onEnd();
      }
    };
  }
  
  startListening(options = {}) {
    if (!this.isSupported) {
      throw new Error('Speech Recognition not supported in this browser');
    }
    
    if (this.isListening) {
      console.warn('⚠️ Already listening');
      return;
    }
    
    try {
      // Set language if provided
      if (options.language) {
        this.recognition.lang = options.language;
      }
      
      // Set callbacks
      this.onResult = options.onResult;
      this.onError = options.onError;
      this.onEnd = options.onEnd;
      
      // Start recognition
      this.recognition.start();
      console.log('🎤 Started listening...');
      
    } catch (error) {
      console.error('❌ Failed to start speech recognition:', error);
      throw error;
    }
  }
  
  stopListening() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      console.log('🎤 Stopped listening');
    }
  }
  
  abort() {
    if (this.recognition && this.isListening) {
      this.recognition.abort();
      console.log('🎤 Aborted listening');
    }
  }
  
  isAvailable() {
    return this.isSupported && !this.isListening;
  }
  
  getSupportedLanguages() {
    return [
      'en-US', 'en-GB', 'en-AU', 'en-CA',
      'es-ES', 'es-MX', 'es-AR',
      'fr-FR', 'fr-CA',
      'de-DE',
      'it-IT',
      'pt-BR', 'pt-PT',
      'ru-RU',
      'ja-JP',
      'ko-KR',
      'zh-CN', 'zh-TW',
      'ar-SA',
      'hi-IN'
    ];
  }
  
  setLanguage(language) {
    if (this.recognition) {
      this.recognition.lang = language;
    }
  }
}

// Create singleton instance
const speechRecognition = new SpeechRecognitionService();

export default speechRecognition;
