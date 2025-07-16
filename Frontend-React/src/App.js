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
function ChatComponent({ onOpenDownloader, headerHidden, onToggleHeader, chatSidebarVisible, setChatSidebarVisible, configSidebarVisible, setConfigSidebarVisible, setClearChatRef, setSetToolsRef }) {
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
  };

  const handleDeleteChat = (chatName) => {
    if (window.confirm(strings.app?.confirmDelete?.replace('{chatName}', chatName) || `¿Eliminar chat ${chatName}?`)) {
      deleteChat(chatName);
    }
  };

  useEffect(() => {
    if (setClearChatRef) {
      setClearChatRef(() => clearChat);
    }
    if (setSetToolsRef) {
      setSetToolsRef(() => setTools);
    }
  }, [clearChat, setTools, setClearChatRef, setSetToolsRef]);

  return (
    <div className="app-layout">
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
            headerHidden={headerHidden}
          />
        </>
      )}
      {configSidebarVisible && (
        <>
          <div
            className="sidebar-overlay"
            onClick={() => setConfigSidebarVisible(false)}
          />
          <ConfigSidebarComponent
            visible={configSidebarVisible}
            onClose={() => setConfigSidebarVisible(false)}
            headerHidden={headerHidden}
          />
        </>
      )}

      {/* Contenedor central flex  para mensajes */}
      <div className="main-flex-content" style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <MessageList
          messages={messages}
          currentResponse={currentResponse}
          isLoading={isLoading}
          messagesEndRef={messagesEndRef}
        />
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
        Los modelos de lenguaje pueden cometer errores. Considera verificar la información importante. 
      </div>
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

  const [clearChatRef, setClearChatRef] = useState(null);
  const [setToolsRef, setSetToolsRef] = useState(null);

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

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!e.shiftKey) return;
      switch (e.key.toLowerCase()) {
        case 'a':
          setHeaderHidden(false);
          setChatSidebarVisible(true);
          setConfigSidebarVisible(true);
          break;
        case 'x':
          setConfigSidebarVisible(v => !v);
          break;
        case 'c':
          setChatSidebarVisible(v => !v);
          break;
        case 'h':
          setHeaderHidden(v => !v);
          break;
        case 'q':
          setHeaderHidden(true);
          setChatSidebarVisible(false);
          setConfigSidebarVisible(false);
          // Cerrar ToolSelector si está abierto, sin modificar tools
          window.dispatchEvent(new Event('close-tools-selector-ui'));
          break;
        case 'n':
          if (typeof clearChatRef === 'function') {
            clearChatRef();
          } else if (clearChatRef) {
            clearChatRef();
          }
          break;
        case 'w':
          // Shift+W: activar tools y abrir ToolSelector
          if (typeof setToolsRef === 'function') {
            setToolsRef(true);
          } else if (setToolsRef) {
            setToolsRef(true);
          }
          window.dispatchEvent(new Event('open-tools-selector-ui'));
          break;
        case 'd':
          // Shift+D: alternar estado de tools
          if (typeof setToolsRef === 'function') {
            setToolsRef(v => !v);
          } else if (setToolsRef) {
            setToolsRef(v => !v);
          }
          break;
        default:
          break;
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [clearChatRef, setToolsRef]);

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
          setClearChatRef={setClearChatRef}
          setSetToolsRef={setSetToolsRef}
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