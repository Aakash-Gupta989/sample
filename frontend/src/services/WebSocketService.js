import config from '../config';

class WebSocketService {
  constructor(sessionId) {
    this.sessionId = sessionId;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    
    // Callbacks
    this.onConnect = null;
    this.onDisconnect = null;
    this.onMessage = null;
    this.onError = null;
  }

  connect() {
    try {
      const wsUrl = `${config.WS_BASE_URL}/ws/${this.sessionId}`;
      console.log('🔄 Connecting to:', wsUrl);
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected successfully');
        this.reconnectAttempts = 0;
        if (this.onConnect) {
          this.onConnect();
        }
      };

      this.ws.onclose = (event) => {
        console.log('❌ WebSocket closed. Code:', event.code, 'Reason:', event.reason);
        if (this.onDisconnect) {
          this.onDisconnect();
        }
        
        // Only auto-reconnect for unexpected closures
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          setTimeout(() => {
            this.reconnectAttempts++;
            console.log(`🔄 Reconnecting attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            this.connect();
          }, this.reconnectDelay);
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 Message received:', data);
          if (this.onMessage) {
            this.onMessage(data);
          }
        } catch (error) {
          console.error('❌ Error parsing message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        if (this.onError) {
          this.onError(error);
        }
      };

    } catch (error) {
      console.error('❌ Error creating WebSocket:', error);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }
  }

  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
      console.log('📤 Message sent:', message);
      return true;
    } else {
      console.error('❌ WebSocket not connected');
      return false;
    }
  }

  sendWhiteboardAnalysis(imageData, userSpeech = '') {
    return this.sendMessage({
      type: 'whiteboard_analysis',
      image_data: imageData,
      user_speech: userSpeech,
      ai_model: 'gpt4o', // Use OpenAI for image analysis (same as practice page)
      timestamp: new Date().toISOString()
    });
  }

  sendChatMessage(message) {
    return this.sendMessage({
      type: 'chat_message',
      content: message,
      timestamp: new Date().toISOString()
    });
  }

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

export default WebSocketService;
