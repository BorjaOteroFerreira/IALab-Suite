import React, { useEffect, useRef, useCallback, memo } from 'react';
// import { useChatContext } from '../hooks/useChatContext';
import ReactMarkdown from 'react-markdown';
import MessageInputSimple from './MessageInputSimple';
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
          <ReactMarkdown>{textContent}</ReactMarkdown>
        )}
      </div>
    </div>
  );
}

function ChatContainer({ toggleChatSidebar, toggleConfigSidebar }) {
  const messagesEndRef = useRef(null);
  
  // Datos de prueba sin contexto
  const messages = [
    { role: 'user', content: 'Hola, ¿cómo estás?' },
    { role: 'assistant', content: '¡Hola! Estoy bien, gracias por preguntar. ¿En qué puedo ayudarte hoy?' },
    { role: 'user', content: 'Explícame qué es React' },
    { role: 'assistant', content: 'React es una biblioteca de JavaScript para construir interfaces de usuario. Fue desarrollada por Facebook y se basa en componentes reutilizables.' }
  ];
  
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [scrollToBottom]);

  return (
    <div className="chat-container">
      <div className="messages-container">
        {messages.map((message, index) => (
          <Message key={index} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>
        <div className="input-section">
        <MessageInputSimple />
      </div>
    </div>
  );
}

export default ChatContainer;
