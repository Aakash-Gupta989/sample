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
    
    // For handling long sentences
    this.lastInterimResult = '';
    this.interimTimeout = null;
    this.pauseThreshold = 5000; // 5 seconds pause to finalize - allows for longer speech
    
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
    this.recognition.continuous = true; // Keep listening until stopped
    this.recognition.interimResults = true; // Show interim results
    this.recognition.lang = 'en-US'; // Default language
    this.recognition.maxAlternatives = 1;
    
    // Add timeout handling for long sentences
    this.recognition.timeout = 30000; // 30 seconds timeout for long sentences
    this.recognition.interval = 1000; // 1 second intervals
    
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
      
      // Handle long sentences - if we have interim results, start a timer
      if (interimTranscript && interimTranscript !== this.lastInterimResult) {
        this.lastInterimResult = interimTranscript;
        
        // Clear existing timeout
        if (this.interimTimeout) {
          clearTimeout(this.interimTimeout);
        }
        
        // Only set timeout if we have substantial content (more than 10 words)
        const wordCount = interimTranscript.trim().split(/\s+/).length;
        if (wordCount > 10) {
          // Set new timeout to finalize after pause
          this.interimTimeout = setTimeout(() => {
            if (this.lastInterimResult && this.onResult) {
              console.log('⏰ Auto-finalizing long sentence:', this.lastInterimResult);
              this.onResult({
                final: this.lastInterimResult,
                interim: '',
                isFinal: true
              });
              this.lastInterimResult = '';
            }
          }, this.pauseThreshold);
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
      
      // Handle specific error types
      let errorMessage = event.error;
      if (event.error === 'no-speech') {
        errorMessage = 'No speech detected. Please speak louder or closer to the microphone.';
      } else if (event.error === 'audio-capture') {
        errorMessage = 'Microphone access denied. Please allow microphone access.';
      } else if (event.error === 'not-allowed') {
        errorMessage = 'Microphone permission denied. Please enable microphone access.';
      } else if (event.error === 'network') {
        errorMessage = 'Network error. Please check your internet connection.';
      }
      
      if (this.onError) {
        this.onError(errorMessage);
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
      
      // Add a timeout to prevent hanging
      const timeout = setTimeout(() => {
        if (this.isListening) {
          console.log('⏰ Speech recognition timeout - stopping');
          this.recognition.stop();
        }
      }, 60000); // 60 second timeout for long responses
      
      // Store timeout for cleanup
      this.timeout = timeout;
      
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
    
    // Clear timeouts
    if (this.timeout) {
      clearTimeout(this.timeout);
      this.timeout = null;
    }
    
    if (this.interimTimeout) {
      clearTimeout(this.interimTimeout);
      this.interimTimeout = null;
    }
    
    // Finalize any pending interim result
    if (this.lastInterimResult && this.onResult) {
      console.log('🎤 Finalizing pending speech:', this.lastInterimResult);
      this.onResult({
        final: this.lastInterimResult,
        interim: '',
        isFinal: true
      });
      this.lastInterimResult = '';
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
