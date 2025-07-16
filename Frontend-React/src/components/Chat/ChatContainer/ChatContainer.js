import React, { useEffect, useRef, useCallback, memo } from 'react';
import { useChatContext } from '../../hooks/useChatContext';
import ReactMarkdown from 'react-markdown';
import MessageInput from '../Chat/MessageInput/MessageInput';
import './ChatContainer.css';
import Prism from 'prismjs';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-sql';



function Message({ message }) {
  if (!message || typeof message !== 'object') {
    return <div className="message error">Error: Mensaje inválido</div>;
  }
  if (!message.role) {
    return <div className="message error">Error: Estructura de mensaje inválida</div>;
  }
  // Manejar tanto  string como objeto
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
    // Si se agregó un mensaje nuevo del asistente, forzar el foco con JS
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
    console.log('ChatContainer: Alternando tools. Valor actual:', tools);
    setTools(prev => {
      console.log('ChatContainer: Cambiando tools de', prev, 'a', !prev);
      return !prev;
    });
  }, [setTools, tools]);

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
          tools={tools}
          rag={rag}
          onToggleTools={handleToolsToggle}
          onToggleRag={handleRagToggle}
          tokensCount={tokensCount}
          currentResponse={currentResponse}
        />
        <div className="sidebar-buttons">
          <button onClick={toggleChatSidebar} title="Historial de conversaciones">🗂️</button>
          <button onClick={toggleConfigSidebar} title="Configuración">⚙️</button>
          <button title="Ayuda">❔</button>
        </div>
        {/* El botón flotante de descargas se ha movido a App.js */}
      </div>
    </div>
  );
};

export default ChatContainer;