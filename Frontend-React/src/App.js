import React, { useState, useEffect, useRef } from 'react';
import './styles/App.css';
import './styles/theme.css';
import './styles//components.css';
import './styles//animations.css';
import './styles//fonts.css';
import './styles//safari-mobile-fix.css';
import { ChatProvider } from './context/ChatContext';
import { LanguageProvider, useLanguage } from './context/LanguageContext';
import { useChatContext } from './hooks/useChatContext';
import ConfigSidebarComponent from './components/ConfigSidebar/ConfigSidebar';
import ChatSidebar from './components/ChatSidebar/ChatSidebar';
import Header from './components/Header/Header';
import MessageList from './components/MessageList/MessageList';
import InputArea from './components/InputArea/InputArea';
import DownloaderPage from './components/DownloaderPage/DownloaderPage';
import DevConsole from './components/DevConsole/DevConsole';
import { Download, MessageCircle } from 'lucide-react';

// Componente principal de Chat
function ChatComponent({ onOpenDownloader }) {
  const [chatSidebarVisible, setChatSidebarVisible] = useState(false);
  const [configSidebarVisible, setConfigSidebarVisible] = useState(false);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const { getStrings } = useLanguage();

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

  const strings = getStrings('app');

  // Auto-scroll a los mensajes más recientes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentResponse]);

  const handleLoadChat = (chatName) => {
    loadChat(chatName);
    // setChatSidebarVisible(false); // Eliminado para que el sidebar no se cierre al cargar un chat
  };

  const handleDeleteChat = (chatName) => {
    if (window.confirm(strings.app?.confirmDelete?.replace('{chatName}', chatName) || `¿Eliminar chat ${chatName}?`)) {
      deleteChat(chatName);
    }
  };

  return (
    <div className="app-layout">
      {/* Header siempre arriba */}
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
        onOpenDownloader={onOpenDownloader}
      />

      {/* Contenedor central flex para sidebars y mensajes */}
      <div className="main-flex-content" style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        {/* ChatSidebar a la izquierda si visible */}
        {chatSidebarVisible && (
          <ChatSidebar
            visible={chatSidebarVisible}
            onLoadChat={handleLoadChat}
            onDeleteChat={handleDeleteChat}
            onClose={() => setChatSidebarVisible(false)}
          />
        )}

        {/* MessageList SIEMPRE como hermano de los sidebars */}
        <MessageList
          messages={messages}
          currentResponse={currentResponse}
          isLoading={isLoading}
          messagesEndRef={messagesEndRef}
        />

        {/* ConfigSidebar a la derecha si visible */}
        {configSidebarVisible && (
          <ConfigSidebarComponent
            visible={configSidebarVisible}
            onClose={() => setConfigSidebarVisible(false)}
          />
        )}
      </div>

      {/* InputArea siempre abajo */}
      <InputArea
        input={input}
        setInput={setInput}
        onSubmit={sendMessage}
        isLoading={isLoading}
        currentResponse={currentResponse}
        onStopResponse={stopResponse}
        tokensCount={tokensCount}
        tools={tools}
        rag={rag}
        onToggleTools={setTools}
        onToggleRag={setRag}
        onOpenDownloader={onOpenDownloader}
      />

      {/* Overlay para cerrar sidebars (sin sidebar flotante) */}
      {chatSidebarVisible && (
        <div
          className="sidebar-overlay"
          onClick={() => setChatSidebarVisible(false)}
        />
      )}
      {configSidebarVisible && (
        <div
          className="sidebar-overlay"
          onClick={() => setConfigSidebarVisible(false)}
        />
      )}
    </div>
  );
}

function App() {
  const [showDownloader, setShowDownloader] = useState(false);

  return (
    <ChatProvider>
      <ChatComponent onOpenDownloader={() => setShowDownloader(true)} />
      <DownloaderPage open={showDownloader} onClose={() => setShowDownloader(false)} />
      <DevConsole />
    </ChatProvider>
  );
}

export default function AppWithLangProvider(props) {
  return (
    <LanguageProvider>
      <App {...props} />
    </LanguageProvider>
  );
}