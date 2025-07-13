import React, { useState, useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import './MessageInput.css';
import { useLanguage } from '../../../context/LanguageContext';
import { Volume2 } from 'lucide-react';

const MessageInput = forwardRef(({ onSendMessage, onStopResponse, isResponding }, ref) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);
  const shouldFocusRef = useRef(true);
  const { getStrings } = useLanguage();
  const strings = getStrings('chat');

  // Exponer el método focus al padre
  useImperativeHandle(ref, () => ({
    focus: () => {
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }
  }));

  // Ajustar altura del textarea automáticamente
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  };
  // Mantener foco después de cada cambio
  useEffect(() => {
    adjustTextareaHeight();
    // Solo enfocar si el mensaje está vacío (después de enviar)
    if (message === '' && shouldFocusRef.current && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [message]);

  // Mantener foco independientemente del streaming
  useEffect(() => {
    const interval = setInterval(() => {
      if (textareaRef.current && document.activeElement !== textareaRef.current && message === '') {
        textareaRef.current.focus();
      }
    }, 100);

    return () => clearInterval(interval);
  }, [message]);
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
  const handleSend = () => {
    if (message.trim()) {
      const currentMessage = message;
      
      // Limpiar inmediatamente y mantener foco
      setMessage('');
      
      // Mantener foco durante el envío
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
      
      // Enviar mensaje después de limpiar
      onSendMessage(currentMessage);
      
      // Asegurar foco después del envío
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
          textareaRef.current.setSelectionRange(0, 0);
        }
      }, 0);
    }
  };

  return (
    <div className="message-input-container">
      {isResponding && (
        <button className="stop-button" onClick={onStopResponse}>
          {strings.stop || 'Detener'}
        </button>
      )}      <textarea
        ref={textareaRef}
        id="main-chat-textarea"
        className="message-textarea"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          shouldFocusRef.current = true;
        }}
        onBlur={(e) => {
          // Solo recuperar foco si el textarea está vacío (después de enviar)
          if (message === '') {
            setTimeout(() => {
              if (textareaRef.current) {
                textareaRef.current.focus();
              }
            }, 10);
          }
        }}
        placeholder={strings.inputPlaceholder || 'Escribe tu mensaje aquí...'}
        rows={1}
        autoFocus
        style={{
          flex: '1 1 0%',
          padding: '12px',
          borderRadius: '6px',
          border: '1px solid #444',
          background: '#2a2a2a',
          color: '#fff',
          resize: 'none',
          minHeight: '44px',
          maxHeight: '120px'
        }}
      />
      <button
        className="send-button"
        onClick={handleSend}
        disabled={isResponding || !message.trim()}
        title={strings.send || 'Enviar'}
      >
        <Volume2 size={22} />
      </button>
    </div>
  );
});

export default MessageInput;
