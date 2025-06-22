import React, { useEffect, useRef, useCallback, memo } from 'react';
import { useChatContext } from '../hooks/useChatContext';
import ReactMarkdown from 'react-markdown';
import MessageInput from './MessageInput';
import './ChatContainer.css';
import Prism from 'prismjs';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-sql';

// Componente de avatar tipo Perplexity
const Avatar = ({ role }) => (
  <div className={`avatar ${role}`}>
    {role === 'user' ? (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none"><circle cx="18" cy="18" r="18" fill="#60a5fa"/><text x="50%" y="55%" textAnchor="middle" fill="#fff" fontSize="16" fontFamily="Arial" dy=".3em">U</text></svg>
    ) : (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none"><circle cx="18" cy="18" r="18" fill="#23272f"/><text x="50%" y="55%" textAnchor="middle" fill="#60a5fa" fontSize="16" fontFamily="Arial" dy=".3em">AI</text></svg>
    )}
  </div>
);

function Message({ message }) {
  if (!message || typeof message !== 'object') {
    return <div className="message error">Error: Mensaje inválido</div>;
  }
  if (!message.role) {
    return <div className="message error">Error: Estructura de mensaje inválida</div>;
  }
  // Manejar tanto el formato antiguo (content como string) como el nuevo (content como objeto)
  const isNewFormat = typeof message.content === 'object' && message.content !== null;
  const textContent = isNewFormat ? message.content.text : message.content;
  if (typeof textContent !== 'string') {
    return <div className="message error">Error: Contenido de mensaje inválido</div>;
  }
  return (
    <div className={`message ${message.role}`}>
      <Avatar role={message.role} />
      <div className="message-content">
        {message.role === 'user' ? (
          <div className="message-text">{textContent}</div>
        ) : (
          <ReactMarkdown
            children={textContent}
            components={{
              code({node, inline, className, children, ...props}) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <pre className={`language-${match[1]}`}>
                    <code className={`language-${match[1]}`} {...props}>
                      {String(children).replace(/\n$/, '')}
                    </code>
                  </pre>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                )
              }
            }}
          />
        )}
      </div>
    </div>
  );
}

const MemoizedMessage = memo(Message);

const ChatContainer = ({ toggleChatSidebar, toggleConfigSidebar }) => {
  const {
    messages,
    currentResponse,
    isLoading,
    tools,
    rag,
    setTools,
    setRag,
    sendMessage,
    tokensCount,
    stopResponse
  } = useChatContext();

  const chatListRef = useRef(null);
  const messageInputRef = useRef(null);
  const prevMessagesLength = useRef(messages.length);
  const [shouldFocusInput, setShouldFocusInput] = React.useState(false);

  useEffect(() => {
    Prism.highlightAll();
  }, [messages, currentResponse]);

  useEffect(() => {
    if (chatListRef.current) {
      chatListRef.current.scrollTop = chatListRef.current.scrollHeight;
    }
  }, [messages, currentResponse]);

  useEffect(() => {
    // Si se agregó un mensaje nuevo del asistente, forzar el foco con JS puro
    if (
      messages.length > prevMessagesLength.current &&
      messages[messages.length - 1]?.role === 'assistant'
    ) {
      let attempts = 0;
      function tryFocus() {
        const el = document.getElementById('main-chat-textarea');
        if (el) {
          el.focus();
          attempts++;
          if (document.activeElement === el) return;
        }
        if (attempts < 5) setTimeout(tryFocus, 80);
      }
      tryFocus();
    }
    prevMessagesLength.current = messages.length;
  }, [messages]);

  const handleToolsToggle = useCallback(() => {
    setTools(prev => !prev);
  }, [setTools]);

  const handleRagToggle = useCallback(() => {
    setRag(prev => !prev);
  }, [setRag]);

  return (
    <div className="chat-container">
      <div className="header">
        <label>Contexto usado:</label>
        <label id="tokens">{tokensCount} Tokens</label>
      </div>
      <div className="chat-list" ref={chatListRef}>
        {Array.isArray(messages) && messages.length > 0 ? (
          messages.map((message, idx) => {
            if (!message || typeof message !== 'object' || message.role === 'system') {
              return null;
            }
            return (
              <MemoizedMessage
                key={message.id || `${message.role}_${idx}`}
                message={message}
              />
            );
          })
        ) : (
          <div className="message system">
            <div className="message-content system">
              Bienvenido a IALab Suite. Escribe un mensaje para comenzar.
            </div>
          </div>
        )}
        {currentResponse && typeof currentResponse === 'string' && currentResponse.length > 0 && (
          (!messages.length || messages[messages.length - 1]?.role !== 'assistant' || isLoading) && (
            <div className="message assistant">
              <Avatar role="assistant" />
              <div className="message-content">
                <ReactMarkdown
                  children={currentResponse}
                  components={{
                    code({node, inline, className, children, ...props}) {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        <pre className={`language-${match[1]}`}>
                          <code className={`language-${match[1]}`} {...props}>
                            {String(children).replace(/\n$/, '')}
                          </code>
                        </pre>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      )
                    }
                  }}
                />
              </div>
            </div>
          )
        )}
        {isLoading && !currentResponse && (
          <div className="message assistant">
            <Avatar role="assistant" />
            <div className="message-content assistant typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
      </div>
      <div className="footer">
        <div className="tools-container">
          <label>Tools</label>
          <input
            type="checkbox"
            id="checkbox-tools"
            checked={tools}
            onChange={handleToolsToggle}
          />
          <label htmlFor="checkbox-tools" className="ios8-switch"></label>
          <label>RAG</label>
          <input
            type="checkbox"
            id="checkbox-rag"
            checked={rag}
            onChange={handleRagToggle}
          />
          <label htmlFor="checkbox-rag" className="ios8-switch"></label>
        </div>
        <MessageInput
          ref={messageInputRef}
          onSendMessage={sendMessage}
          onStopResponse={stopResponse}
          isResponding={!!currentResponse || isLoading}
        />
        <div className="sidebar-buttons">
          <button onClick={toggleChatSidebar} title="Historial de conversaciones">🗂️</button>
          <button onClick={toggleConfigSidebar} title="Configuración">⚙️</button>
          <button title="Ayuda">❔</button>
        </div>
      </div>
    </div>
  );
};

export default ChatContainer;
