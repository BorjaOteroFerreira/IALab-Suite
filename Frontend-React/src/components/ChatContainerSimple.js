import React from 'react';
import './ChatContainer.css';

function ChatContainer({ toggleChatSidebar, toggleConfigSidebar }) {
  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>AI Lab Suite Chat</h1>
      </div>
      
      <div className="messages-container">
        <div className="message user">
          <div className="message-content">
            <p>Hola, este es un mensaje de prueba del usuario</p>
          </div>
        </div>
        
        <div className="message assistant">
          <div className="message-content">
            <p>¡Hola! Soy el asistente AI. Esta es una respuesta de prueba.</p>
          </div>
        </div>
      </div>
      
      <div className="input-container">
        <input 
          type="text" 
          placeholder="Escribe tu mensaje aquí..." 
          style={{
            width: '100%',
            padding: '12px',
            borderRadius: '8px',
            border: '1px solid #ccc',
            fontSize: '16px'
          }}
        />
        <button 
          style={{
            padding: '12px 20px',
            backgroundColor: '#6366f1',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            marginTop: '10px',
            cursor: 'pointer'
          }}
        >
          Enviar
        </button>
      </div>
    </div>
  );
}

export default ChatContainer;
