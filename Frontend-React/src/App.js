import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import './theme.css';
import './components.css';
import './animations.css';
import './fonts.css';
import './safari-mobile-fix.css';
import { ChatProvider } from './context/ChatContext';
import { useChatContext } from './hooks/useChatContext';
import ConfigSidebarComponent from './components/ConfigSidebar/ConfigSidebar';
import ChatSidebar from './components/ChatSidebar/ChatSidebar';
import Header from './components/Header/Header';
import MessageList from './components/MessageList/MessageList';
import InputArea from './components/InputArea/InputArea';

// Componente principal de Chat
function ChatComponent() {
  const [chatSidebarVisible, setChatSidebarVisible] = useState(false);
  const [configSidebarVisible, setConfigSidebarVisible] = useState(false);
  const [input, setInput] = useState('');
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
      {/* Contenedor principal */}
      <div className={`main-container ${configSidebarVisible ? 'sidebar-right-open' : ''}`}>
        <Header
          tools={tools}
          rag={rag}
          tokensCount={tokensCount}
          chatSidebarVisible={chatSidebarVisible}
          configSidebarVisible={configSidebarVisible}
          onToggleTools={setTools}
          onToggleRag={setRag}
          onToggleChatSidebar={() => setChatSidebarVisible(!chatSidebarVisible)}
          onToggleConfigSidebar={() => setConfigSidebarVisible(!configSidebarVisible)}
          onClearChat={clearChat}
        />

        <MessageList
          messages={messages}
          currentResponse={currentResponse}
          isLoading={isLoading}
          messagesEndRef={messagesEndRef}
        />

        <InputArea
          input={input}
          setInput={setInput}
          onSubmit={sendMessage}
          isLoading={isLoading}
          currentResponse={currentResponse}
          onStopResponse={stopResponse}
        />
      </div>

      {/* Overlay y Sidebar de Chat - Solo renderizar cuando esté visible */}
      {chatSidebarVisible && (
        <>
          <div 
            className="sidebar-overlay"
            onClick={() => setChatSidebarVisible(false)}
          />
          <ChatSidebar 
            visible={chatSidebarVisible} 
            onLoadChat={handleLoadChat}
            onDeleteChat={handleDeleteChat}
            onClose={() => setChatSidebarVisible(false)}
          />
        </>
      )}

      {/* Overlay y Sidebar de Configuración - Solo renderizar cuando esté visible */}
      {configSidebarVisible && (
        <>
          <div 
            className="sidebar-overlay"
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