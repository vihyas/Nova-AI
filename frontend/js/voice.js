/**
 * NOVA AI — Voice Interaction Module (Web Speech API)
 * Handles Speech-to-Text (STT) and Text-to-Speech (TTS)
 */

class VoiceManager {
  constructor() {
    this.recognition = null;
    this.isListening = false;
    this.isSpeaking = false;
    this.speechRate = 1.0;
    this.speechPitch = 1.0;
    this.language = 'en-US';
    this.onResultCallback = null;
    this.onStateChangeCallback = null;
    this.synth = window.speechSynthesis;

    this.initRecognition();
  }

  initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Speech Recognition is not supported in this browser.');
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = false;
    this.recognition.interimResults = true;
    this.recognition.lang = this.language;

    this.recognition.onstart = () => {
      this.isListening = true;
      this.triggerStateChange('listening');
    };

    this.recognition.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      if (this.onResultCallback) {
        this.onResultCallback({
          interim: interimTranscript,
          final: finalTranscript
        });
      }
    };

    this.recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      this.isListening = false;
      this.triggerStateChange('idle');
    };

    this.recognition.onend = () => {
      this.isListening = false;
      this.triggerStateChange('idle');
    };
  }

  setLanguage(langCode) {
    if (langCode === 'ta') {
      this.language = 'ta-IN';
    } else {
      this.language = 'en-US';
    }
    if (this.recognition) {
      this.recognition.lang = this.language;
    }
  }

  startListening(onResult, onStateChange) {
    if (!this.recognition) {
      alert('Speech recognition is not available on this browser. Chrome or Edge is recommended.');
      return;
    }
    this.onResultCallback = onResult;
    this.onStateChangeCallback = onStateChange;

    try {
      this.synth.cancel(); // Stop any ongoing speech
      this.recognition.start();
    } catch (e) {
      console.warn('Recognition already started or error:', e);
    }
  }

  stopListening() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      this.isListening = false;
      this.triggerStateChange('idle');
    }
  }

  toggleListening(onResult, onStateChange) {
    if (this.isListening) {
      this.stopListening();
    } else {
      this.startListening(onResult, onStateChange);
    }
  }

  speak(text, onStart = null, onEnd = null) {
    if (!this.synth) return;

    this.synth.cancel(); // Stop prior utterance
    if (!text || text.trim() === '') return;

    // Clean markdown characters for voice output
    const cleanText = text
      .replace(/(\*\*|__|\*|_|```[\s\S]*?```|`)/g, '')
      .replace(/#+\s/g, '')
      .replace(/\[Page \d+\]/g, 'page reference')
      .replace(/https?:\/\/[^\s]+/g, 'link');

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = this.speechRate;
    utterance.pitch = this.speechPitch;
    utterance.lang = this.language;

    utterance.onstart = () => {
      this.isSpeaking = true;
      if (onStart) onStart();
      this.triggerStateChange('speaking');
    };

    utterance.onend = () => {
      this.isSpeaking = false;
      if (onEnd) onEnd();
      this.triggerStateChange('idle');
    };

    utterance.onerror = (e) => {
      console.warn('Speech synthesis error:', e);
      this.isSpeaking = false;
      if (onEnd) onEnd();
      this.triggerStateChange('idle');
    };

    this.synth.speak(utterance);
  }

  stopSpeaking() {
    if (this.synth) {
      this.synth.cancel();
      this.isSpeaking = false;
      this.triggerStateChange('idle');
    }
  }

  triggerStateChange(state) {
    if (this.onStateChangeCallback) {
      this.onStateChangeCallback(state);
    }
  }
}

export const voice = new VoiceManager();

