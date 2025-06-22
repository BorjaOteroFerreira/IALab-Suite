import React, { useState, useRef, useEffect } from 'react';
import './MainContainer.css';
import Message from './Message';
import MessageInput from './MessageInput';

function MainContainer({
  chatHistory,
  currentResponse,
  totalTokens,
  tools,
  setTools,
  rag,
  setRag,
  sendMessage,
  stopResponse,
  toggleChatSidebar,
  toggleConfigSidebar,
  toggleHelpModal,
  isLoading,
  responseNumber
}) {
  const chatContainerRef = useRef(null);
  const [isExpanded, setIsExpanded] = useState(false);

  // Scroll al fondo del chat cuando cambia el historial o la respuesta actual
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatHistory, currentResponse]);

  const toggleTools = () => {
    setTools(!tools);
    // Enviar configuración al backend
    try {
      window.socket?.emit('tools', { tools: !tools });
    } catch (error) {
      console.error('Error al cambiar herramientas:', error);
    }
  };

  const toggleRAG = () => {
    setRag(!rag);
    // Enviar configuración al backend
    try {
      window.socket?.emit('rag', { rag: !rag });
    } catch (error) {
      console.error('Error al cambiar RAG:', error);
    }
  };

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
    // Si está expandido, ocultar sidebars
    if (!isExpanded) {
      document.body.classList.add('expanded-chat');
    } else {
      document.body.classList.remove('expanded-chat');
    }
  };

  return (
    <div id="main-container" className={isExpanded ? 'expanded' : ''}>
      <div id="header">
        <div className="header-actions">
          <button className="btn action-btn" onClick={toggleChatSidebar}>
            <i className="fa fa-comments"></i>
          </button>
          <h4>IALab Suite</h4>
        </div>

        <div className="token-info">
          <label>Tokens: <span id="tokens">{totalTokens}</span></label>
        </div>
        
        <div className="header-buttons">
          <button
            className={`btn toggle-btn ${tools ? 'active' : ''}`}
            onClick={toggleTools}
            title="Herramientas"
          >
            🛠️
          </button>
          
          <button
            className={`btn toggle-btn ${rag ? 'active' : ''}`}
            onClick={toggleRAG}
            title="RAG"
          >
            📚
          </button>
          
          <button className="btn action-btn" onClick={toggleExpand} title="Expandir/Contraer">
            {isExpanded ? '↙️' : '↗️'}
          </button>
          
          <button className="btn action-btn" onClick={toggleHelpModal} title="Ayuda">
            ❓
          </button>
          
          <button className="btn action-btn" onClick={toggleConfigSidebar} title="Configuración">
            ⚙️
          </button>
        </div>
      </div>

      <div id="chat-container" ref={chatContainerRef} className="container mt-4">
        <div id="chat-list">
          {/* Renderizar los mensajes del historial exceptuando el mensaje del sistema */}
          {chatHistory.slice(1).map((message, index) => (
            <Message 
              key={index} 
              role={message.role} 
              content={message.content}
              index={index}
            />
          ))}
          
          {/* Si hay una respuesta en curso, mostrarla */}
          {currentResponse && (
            <Message 
              role="assistant" 
              content={currentResponse}
              isTyping={isLoading}
              index={chatHistory.length}
            />
          )}
        </div>
      </div>

      <div id="input-container">
        <MessageInput 
          onSendMessage={sendMessage} 
          onStopResponse={stopResponse}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}

export default MainContainer;
