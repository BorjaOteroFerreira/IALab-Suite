import React, { useState, useRef } from 'react';
import './MessageInput.css';

function MessageInput() {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim()) {
      console.log('Enviando mensaje:', message);
      setMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="message-input-container">
      <form onSubmit={handleSubmit} className="message-form">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Escribe tu mensaje..."
            className="message-textarea"
            rows={1}
          />
          <button
            type="submit"
            disabled={!message.trim()}
            className="send-button"
          >
            ➤
          </button>
        </div>
      </form>
    </div>
  );
}

export default MessageInput;
