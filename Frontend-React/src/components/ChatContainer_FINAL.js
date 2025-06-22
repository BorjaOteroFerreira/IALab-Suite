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
import 'prismjs/components/prism-java';

// Componente de mensaje simplificado
function Message({ message }) {
  if (!message || typeof message !== 'object') {
    return <div className="message error">Error: Mensaje inválido</div>;
  }
  
  if (!message.role || typeof message.content !== 'string') {
    return <div className="message error">Error: Estructura de mensaje inválida</div>;
  }

  return (
    <div className={`message ${message.role}`}>
      <div className="message-content">
        {message.role === 'user' ? (
          <div className="message-text">{message.content}</div>
        ) : (
          <ReactMarkdown
            children={message.content}
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

  useEffect(() => {
    Prism.highlightAll();
  }, [messages, currentResponse]);

  useEffect(() => {
    if (chatListRef.current) {
      chatListRef.current.scrollTop = chatListRef.current.scrollHeight;
    }
  }, [messages, currentResponse]);

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
          messages.map((message, index) => {
            if (!message || typeof message !== 'object' || message.role === 'system') {
              return null;
            }
            
            return (
              <MemoizedMessage 
                key={`${index}-${message.role}-${Date.now()}`} 
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

        {currentResponse && typeof currentResponse === 'string' && (
          <div className="message assistant">
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
        )}
        
        {isLoading && !currentResponse && (
          <div className="message assistant">
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
          onSendMessage={sendMessage}
          onStopResponse={stopResponse}
          isResponding={!!currentResponse || isLoading}
        />
        
        <div className="sidebar-buttons">
          <button onClick={toggleChatSidebar} title="Historial de conversaciones">🧾</button>
          <button onClick={toggleConfigSidebar} title="Configuración">⚙️</button>
          <button title="Ayuda">❔</button>
        </div>
      </div>
    </div>
  );
};

export default ChatContainer;
