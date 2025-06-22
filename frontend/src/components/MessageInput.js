import React, { useState, useRef, useEffect } from 'react';
import './MessageInput.css';

function MessageInput({ onSendMessage, onStopResponse, isLoading }) {
  const [inputValue, setInputValue] = useState('');
  const textareaRef = useRef(null);

  // Focus textarea cuando el componente se monte
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  // Ajustar la altura del textarea cuando cambie el contenido
  useEffect(() => {
    adjustTextareaHeight();
  }, [inputValue]);

  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue('');
      
      // Resetear altura del textarea
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      const lineHeight = parseFloat(getComputedStyle(textarea).lineHeight);
      const maxLines = 8;
      const maxHeight = maxLines * lineHeight;
      
      // Reset height to get the correct scrollHeight
      textarea.style.height = 'auto';
      
      // Set the height based on content, but limit it
      const newHeight = Math.min(textarea.scrollHeight, maxHeight);
      textarea.style.height = newHeight + 'px';
      
      // Add scrollbar if content exceeds max height
      textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden';
    }
  };

  return (
    <div className="message-input-container">
      <textarea
        ref={textareaRef}
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Escribe un mensaje..."
        disabled={isLoading}
        rows={1}
      />
      
      {isLoading ? (
        <button 
          className="stop-button" 
          onClick={onStopResponse}
          title="Detener respuesta"
        >
          <span>⏹️</span>
        </button>
      ) : (
        <button 
          className="send-button" 
          onClick={handleSend} 
          disabled={!inputValue.trim()}
          title="Enviar mensaje"
        >
          <span>➤</span>
        </button>
      )}
    </div>
  );
}

export default MessageInput;
