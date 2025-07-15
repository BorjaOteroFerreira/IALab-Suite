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
import ConfigSidebarComponent from './components/UI/ConfigSidebar/ConfigSidebar';
import ChatSidebar from './components/Chat/ChatSidebar/ChatSidebar';
import Header from './components/UI/Header/Header';
import MessageList from './components/Chat/MessageList/MessageList';
import InputArea from './components/Chat/InputArea/InputArea';
import DownloaderPage from './components/UI/DownloaderPage/DownloaderPage';
import DevConsole from './components/DevConsole/DevConsole';
import { Download } from 'lucide-react';
import { SocketProvider } from './context/SocketContext';
import LanguageSelector from './components/UI/LanguageSelector/LanguageSelector';
import AppTour from './components/AppTour';
import ConfigSidebarTour from './components/ConfigSidebarTour';
import DownloaderTour from './components/DownloaderTour';
import ToolSelectorTour from './components/ToolSelectorTour';

// Componente principal de Chat
function ChatComponent({ onOpenDownloader, headerHidden, onToggleHeader, chatSidebarVisible, setChatSidebarVisible, configSidebarVisible, setConfigSidebarVisible }) {
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
        headerHidden={headerHidden}
        onToggleHeader={onToggleHeader}
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
      <div className="input-area-wrapper">
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
        />
      </div>
      {/* Marca de agua fija en la parte inferior */}
      <div style={{ position: 'fixed', left: 0, right: 0, bottom: 0, textAlign: 'center', fontSize: '0.69rem', color: '#888', zIndex: 1500, pointerEvents: 'none', paddingBottom: '4px' }}>
        Los modelos de lenguaje pueden cometer errores. Considera verificar la información importante. Ver preferencias de cookies.
      </div>
      {/* Botones flotantes fuera del input area */}
      <button
        className="header-button floating-downloader-btn-global"
        title="Descargar modelos GGUF"
        style={{ position: 'fixed', right: '1.5rem', bottom: 16, zIndex: 2000 }}
        onClick={onOpenDownloader}
      >
        <Download size={22} />
      </button>

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
  const [headerHidden, setHeaderHidden] = useState(false);
  const [chatSidebarVisible, setChatSidebarVisible] = useState(false);
  const [configSidebarVisible, setConfigSidebarVisible] = useState(false);
  // Estados para mostrar los tours contextuales solo la primera vez
  const [showDownloaderTour, setShowDownloaderTour] = useState(false);
  const [hasSeenDownloaderTour, setHasSeenDownloaderTour] = useState(false);
  const [showConfigSidebarTour, setShowConfigSidebarTour] = useState(false);
  const [hasSeenConfigSidebarTour, setHasSeenConfigSidebarTour] = useState(false);
  const [showToolSelectorTour, setShowToolSelectorTour] = useState(false);
  const [hasSeenToolSelectorTour, setHasSeenToolSelectorTour] = useState(false);

  const handleToggleHeader = () => setHeaderHidden(h => !h);

  // Mostrar tour contextual al abrir DownloaderPage por primera vez
  useEffect(() => {
    if (showDownloader && !hasSeenDownloaderTour) {
      setShowDownloaderTour(true);
      setHasSeenDownloaderTour(true);
    }
  }, [showDownloader, hasSeenDownloaderTour]);

  // Mostrar tour contextual al abrir ConfigSidebar por primera vez
  useEffect(() => {
    if (configSidebarVisible && !hasSeenConfigSidebarTour) {
      setShowConfigSidebarTour(true);
      setHasSeenConfigSidebarTour(true);
    }
  }, [configSidebarVisible, hasSeenConfigSidebarTour]);

  // Mostrar tour contextual al abrir ToolSelector por primera vez
  useEffect(() => {
    const handleOpenToolsSelector = () => {
      if (!hasSeenToolSelectorTour) {
        setShowToolSelectorTour(true);
        setHasSeenToolSelectorTour(true);
      }
    };
    window.addEventListener('open-tools-selector-ui', handleOpenToolsSelector);
    return () => window.removeEventListener('open-tools-selector-ui', handleOpenToolsSelector);
  }, [hasSeenToolSelectorTour]);

  return (
    <SocketProvider>
      <ChatProvider>
        <ChatComponent
          onOpenDownloader={() => setShowDownloader(true)}
          headerHidden={headerHidden}
          onToggleHeader={handleToggleHeader}
          chatSidebarVisible={chatSidebarVisible}
          setChatSidebarVisible={setChatSidebarVisible}
          configSidebarVisible={configSidebarVisible}
          setConfigSidebarVisible={setConfigSidebarVisible}
        />
        {/* Selector de idioma flotante al mismo nivel que el botón de descargas */}
        <div className="floating-language-selector-global" style={{ position: 'fixed', left: '1.5rem', bottom: 16, zIndex: 3001 }}>
          <LanguageSelector />
        </div>
        <DownloaderPage open={showDownloader} onClose={() => setShowDownloader(false)} />
        <DevConsole />
        {/* Tours contextuales independientes */}
        {showDownloaderTour && <DownloaderTour run={showDownloaderTour} onClose={() => setShowDownloaderTour(false)} />}
        {showConfigSidebarTour && <ConfigSidebarTour run={showConfigSidebarTour} onClose={() => setShowConfigSidebarTour(false)} />}
        {showToolSelectorTour && <ToolSelectorTour run={showToolSelectorTour} onClose={() => setShowToolSelectorTour(false)} />}
      </ChatProvider>
    </SocketProvider>
  );
}

export default function AppWithLangProvider(props) {
  return (
    <LanguageProvider>
      <App {...props} />
    </LanguageProvider>
  );
}