import React from 'react';
import { Download, Folder, Settings, Plus, MessagesSquare, Database, Volume2, VolumeX, ChevronDown, ChevronUp } from 'lucide-react';
import ToolsSelector from '../ToolsSelector/ToolsSelector';
import { useChatContext } from '../../../hooks/useChatContext';
import { useLanguage } from '../../../context/LanguageContext';
import './Header.css';

function Header({ 
  tools, 
  rag, 
  chatSidebarVisible, 
  configSidebarVisible,
  onToggleTools, 
  onToggleRag, 
  onToggleChatSidebar, 
  onToggleConfigSidebar, 
  onClearChat,
  onOpenDownloader,
  ttsEnabled,
  setTTSEnabled,
  headerHidden,
  onToggleHeader
}) {
  // Obtener el socket del contexto de chat
  const { socket } = useChatContext();
  const { getStrings } = useLanguage();
  const strings = getStrings('header');

  return (
    <>
      <header
        className="app-header"
        style={{
          position: 'fixed',
          left: 0,
          top: 0,
          width: '100%',
          zIndex: 3000,
          transform: headerHidden ? 'translateY(-100%)' : 'translateY(0)',
          transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      >
        <div className="header-left">
          <h1 className="app-title">{strings.logo}</h1>
        </div>
        {/* Botón para ocultar la cabecera centrado y pegado abajo */}
        <div className="header-hide-center" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%', position: 'absolute', left: 0, bottom: 0, pointerEvents: 'none', zIndex: 2 }}>
          <button
            onClick={onToggleHeader}
            className="header-button"
            title={strings.hideHeaderTooltip || 'Ocultar cabecera'}
            style={{ pointerEvents: 'auto' }}
          >
            <ChevronUp size={20} />
          </button>
        </div>
        <div className="header-controls">
          <button
            onClick={onClearChat}
            className="header-button"
            title={strings.newChatTooltip || strings.newChat || 'Nuevo chat'}
          >
            <Plus size={22} />
          </button>
          <button
            onClick={onToggleChatSidebar}
            className={`header-button ${chatSidebarVisible ? 'active' : ''}`}
            title={strings.historyTooltip || strings.history || 'Historial'}
          >
            <MessagesSquare size={22} />
          </button>
          <button
            onClick={onToggleConfigSidebar}
            className={`header-button ${configSidebarVisible ? 'active' : ''}`}
            title={strings.settingsTooltip || strings.settings || 'Configuración'}
          >
            <Settings size={22} />
          </button>
          {/* Botón de descarga de modelos GGUF */}
          <button
            onClick={onOpenDownloader}
            className="header-button"
            title={strings.downloadModelsTooltip || 'Descargar modelos GGUF'}
          >
            <Download size={22} />
          </button>
        </div>
      </header>
      {headerHidden && (
        <div className="app-header-hidden" style={{
          width: '100%',
          height: '0px',
          position: 'fixed',
          left: 0,
          top: 0,
          zIndex: 3000,
          background: 'transparent',
        }}>
          <button
            className="show-header-btn"
            style={{
              position: 'absolute',
              left: '50%',
              top: '2px',
              transform: 'translateX(-50%)',
              background: 'none', // sin fondo
              border: 'none',
              borderRadius: '50%',
              width: '24px',
              height: '24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              zIndex: 3001,
              color: '#87CEEB', // color neon igual que la flecha de ocultar
            }}
            title={strings.showHeaderTooltip || 'Mostrar cabecera'}
            onClick={onToggleHeader}
          >
            <ChevronDown size={20} color="#87CEEB" />
          </button>
        </div>
      )}
    </>
  );
}

export default Header;
