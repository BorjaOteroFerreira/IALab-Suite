import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import './theme.css';
import './components.css';
import './animations.css';
import './fonts.css';
import { ChatProvider } from './context/ChatContext';
import { useChatContext } from './hooks/useChatContext';
import ReactMarkdown from 'react-markdown';
import CodeBlock from './components/CodeBlock';
import ConfigSidebarComponent from './components/ConfigSidebar';

// Función para extraer ID de video de YouTube desde diferentes formatos de URL
const extractYouTubeVideoId = (url) => {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([^&\n?#]+)/,
    /youtube\.com\/watch\?.*v=([^&\n?#]+)$/
  ];
  
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) {
      return match[1];
    }
  }
  return null;
};

// Componente para renderizar iframe de YouTube
const YouTubeEmbed = ({ videoId }) => {
  return (
    <div className="youtube-embed-container" style={{
      position: 'relative',
      paddingBottom: '56.25%' /* 16:9 aspect ratio */,
      height: 0,
      overflow: 'hidden',
      maxWidth: '100%',
      background: '#000',
      marginTop: '10px',
      marginBottom: '10px',
      borderRadius: '8px'
    }}>
      <iframe
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          border: 'none',
          borderRadius: '8px'
        }}
        src={`https://www.youtube.com/embed/${videoId}`}
        title="YouTube video player"
        frameBorder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
    </div>
  );
};

// Componente personalizado para enlaces que detecta YouTube
const LinkRenderer = ({ href, children }) => {
  const videoId = extractYouTubeVideoId(href);
  
  if (videoId) {
    return (
      <div>
        <a href={href} target="_blank" rel="noopener noreferrer" className="youtube-link">
          {children || href}
        </a>
        <YouTubeEmbed videoId={videoId} />
      </div>
    );
  }
  
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children || href}
    </a>
  );
};

// Función para procesar texto y convertir URLs de YouTube en componentes embebidos
const processYouTubeLinks = (text) => {
  const youtubeRegex = /(https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([^&\n?#\s]+))/g;
  
  const parts = [];
  let lastIndex = 0;
  let match;
  
  while ((match = youtubeRegex.exec(text)) !== null) {
    // Agregar texto antes del enlace
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    
    // Agregar el componente de YouTube
    const videoId = extractYouTubeVideoId(match[1]);
    if (videoId) {
      parts.push(
        <div key={match.index}>
          <a href={match[1]} target="_blank" rel="noopener noreferrer" className="youtube-link">
            {match[1]}
          </a>
          <YouTubeEmbed videoId={videoId} />
        </div>
      );
    } else {
      parts.push(match[1]);
    }
    
    lastIndex = match.index + match[0].length;
  }
  
  // Agregar el texto restante
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  
  return parts.length > 1 ? parts : text;
};

// Componente ChatSidebar
function ChatSidebar({ visible, onLoadChat, onDeleteChat }) {
  const { chatList, fetchChatList } = useChatContext();

  useEffect(() => {
    if (visible) {
      fetchChatList();
    }
  }, [visible, fetchChatList]);

  if (!visible) return null;

  return (
    <div className="chat-sidebar">
      <h3>📁 Historial</h3>
      <div className="chat-list">
        {chatList.map((chatName, idx) => (
          <div key={idx} className="chat-item">
            <button
              onClick={() => onDeleteChat(chatName)}
              className="delete-chat-btn"
              title="Eliminar chat"
            >
              🗑️
            </button>
            <button
              onClick={() => onLoadChat(chatName)}
              className="chat-name-btn"
              title={`Cargar: ${chatName}`}
            >
              {chatName}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// Componente principal de Chat
function ChatComponent() {
  const [chatSidebarVisible, setChatSidebarVisible] = useState(false);
  const [configSidebarVisible, setConfigSidebarVisible] = useState(false);
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);

  const {
    messages,
    currentResponse,
    isLoading,
    tools,
    rag,
    setTools,
    setRag,
    sendMessage,
    stopResponse,
    tokensCount,
    clearChat,
    loadChat,
    deleteChat
  } = useChatContext();

  // Auto-scroll a los mensajes más recientes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentResponse]);

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
    console.log('🚀 DEBUG: handleSubmit LLAMADO, input:', input.trim(), 'isLoading:', isLoading);
    if (input.trim() && !isLoading) {
      console.log('🚀 DEBUG: handleSubmit EJECUTANDO sendMessage');
      sendMessage(input);
      setInput('');
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
        }
      }, 100);
    } else {
      console.log('🚀 DEBUG: handleSubmit IGNORADO (input vacío o loading)');
    }
  };

  const handleLoadChat = (chatName) => {
    loadChat(chatName);
    setChatSidebarVisible(false);
  };

  const handleDeleteChat = (chatName) => {
    if (window.confirm(`¿Estás seguro de que quieres eliminar "${chatName}"?`)) {
      deleteChat(chatName);
    }
  };

  return (
    <div className="app-layout">
      {/* Sidebar de Historial */}
      <ChatSidebar 
        visible={chatSidebarVisible} 
        onLoadChat={handleLoadChat}
        onDeleteChat={handleDeleteChat}
      />

      {/* Contenedor principal */}
      <div className={`main-container ${chatSidebarVisible ? 'sidebar-left-open' : ''} ${configSidebarVisible ? 'sidebar-right-open' : ''}`}>
        {/* Header */}
        <header className="app-header">
          <div className="header-left">
            <h1 className="app-title">🤖 AI Lab Suite</h1>
            <span className="tokens-counter">
              Contexto usado: {tokensCount} Tokens
            </span>
          </div>
          
          <div className="header-controls">
            <div className="toggle-group">
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={tools}
                  onChange={(e) => setTools(e.target.checked)}
                />
                <span className="toggle-slider"></span>
                Tools
              </label>
              
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={rag}
                  onChange={(e) => setRag(e.target.checked)}
                />
                <span className="toggle-slider"></span>
                RAG
              </label>
            </div>

            <button
              onClick={() => setChatSidebarVisible(!chatSidebarVisible)}
              className={`header-button ${chatSidebarVisible ? 'active' : ''}`}
              title="Historial"
            >
              📁
            </button>
            
            <button
              onClick={() => setConfigSidebarVisible(!configSidebarVisible)}
              className={`header-button ${configSidebarVisible ? 'active' : ''}`}
              title="Configuración"
            >
              ⚙️
            </button>
            
            <button
              onClick={clearChat}
              className="header-button danger"
              title="Nuevo chat"
            >
              🗑️
            </button>
          </div>
        </header>

        {/* Área de mensajes */}
        <div className="messages-container">
          <div className="messages-list">
            {messages.length === 0 ? (
              <div className="welcome-message">
                <h2>¡Bienvenido a AI Lab Suite! 🚀</h2>
                <p>Escribe un mensaje para comenzar la conversación.</p>
              </div>
            ) : (
              messages.map((message, idx) => (
                <div key={idx} className={`message ${message.role}`}>
                  <div className="message-avatar">
                    {message.role === 'user' ? '👤' : '🤖'}
                  </div>                  <div className="message-content">
                    {message.role === 'user' ? (
                      <div className="user-message">{message.content}</div>
                    ) : (
                      <ReactMarkdown 
                        className="assistant-message"
                        components={{
                          code({node, inline, className, children, ...props}) {
                            const match = /language-(\w+)/.exec(className || '');
                            const language = match ? match[1] : '';
                            
                            return !inline ? (
                              <CodeBlock language={language}>
                                {String(children).replace(/\n$/, '')}
                              </CodeBlock>
                            ) : (
                              <code className="inline-code" {...props}>
                                {children}
                              </code>
                            );
                          },
                          a: LinkRenderer
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    )}
                  </div>
                </div>
              ))
            )}
              {currentResponse && (
              <div className="message assistant">
                <div className="message-avatar">🤖</div>
                <div className="message-content">
                  <ReactMarkdown 
                    className="assistant-message streaming"
                    components={{
                      code({node, inline, className, children, ...props}) {
                        const match = /language-(\w+)/.exec(className || '');
                        const language = match ? match[1] : '';
                        
                        return !inline ? (
                          <CodeBlock language={language}>
                            {String(children).replace(/\n$/, '')}
                          </CodeBlock>
                        ) : (
                          <code className="inline-code" {...props}>
                            {children}
                          </code>
                        );
                      },
                      a: LinkRenderer
                    }}
                  >
                    {currentResponse}
                  </ReactMarkdown>
                </div>
              </div>
            )}
            
            {isLoading && !currentResponse && (
              <div className="message assistant">
                <div className="message-avatar">🤖</div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input area */}
        <div className="input-area">
          <form onSubmit={handleSubmit} className="message-form">
            <div className="input-container">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    // No llamar a handleSubmit aquí, dejar que el formulario lo maneje
                    console.log('⌨️ DEBUG: Enter presionado en textarea, formulario manejará el envío');
                    // Simular clic en el botón de envío para que el formulario maneje todo
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
                  onClick={stopResponse}
                  className="send-button stop"
                  title="Detener respuesta"
                >
                  ⏹️
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
        </div>      </div>

      {/* Overlay y Sidebar de Configuración - Solo renderizar cuando esté visible */}
      {configSidebarVisible && (
        <>
          <div 
            className={`config-sidebar-overlay ${configSidebarVisible ? 'visible' : ''}`}
            onClick={() => setConfigSidebarVisible(false)}
          />
          <ConfigSidebarComponent 
            visible={configSidebarVisible} 
            onClose={() => setConfigSidebarVisible(false)}
          />
        </>
      )}
    </div>
  );
}

function App() {
  return (
    <ChatProvider>
      <ChatComponent />
    </ChatProvider>
  );
}

export default App;