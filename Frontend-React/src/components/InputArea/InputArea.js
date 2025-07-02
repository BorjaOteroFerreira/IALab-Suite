import React, { useRef, useEffect } from 'react';
import './InputArea.css';
import { Square, Database } from 'lucide-react';
import ToolsSelector from '../ToolsSelector/ToolsSelector';
import { useChatContext } from '../../hooks/useChatContext';

function InputArea({ 
  input, 
  setInput, 
  onSubmit, 
  isLoading, 
  tokensCount, 
  currentResponse, 
  onStopResponse, 
  tools, rag, onToggleTools, onToggleRag 
}) {
  const textareaRef = useRef(null);
  
  // Obtener el socket del contexto de chat
  const { socket } = useChatContext();

  // Auto-resize del textarea
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [input]);
  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSubmit(input);
      setInput('');
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
        }
      }, 100);
    }
  };

  return (
    <div className="input-area">
      <form onSubmit={handleSubmit} className="message-form">
        <span className="tokens-counter">
          Contexto usado: {tokensCount} Tokens
        </span>
        <div className="input-container">
           <button
              type="button"
              onClick={() => onToggleRag(!rag)}
              className={`input-icon-button${!!rag ? ' active' : ''}`}
              title="RAG"
            >
              <Database size={23} />
            </button>
          
          <div className="input-side-buttons">
            <ToolsSelector 
              tools={tools} 
              onToggleTools={onToggleTools}
              socket={socket}
            />
           </div>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                e.target.form.requestSubmit();
              }
            }}
            placeholder="Escribe tu mensaje aquí... (Enter para enviar, Shift+Enter para nueva línea)"
            className="message-textarea"
            disabled={isLoading}
            rows={1}
          />
          {isLoading && currentResponse ? (
            <button
              type="button"
              onClick={onStopResponse}
              className="send-button stop"
              title="Detener respuesta"
            >
              <Square size={20} />
            </button>
          ) : (
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="send-button"
              title="Enviar mensaje"
            >
              ➤
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

export default InputArea;
