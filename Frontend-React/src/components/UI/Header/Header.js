import React from 'react';
import { Download, Folder, Settings, Plus, MessagesSquare, Database, Volume2, VolumeX, ChevronDown } from 'lucide-react';
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

  if (headerHidden) {
    // Solo mostrar el botón flotante para mostrar la cabecera
    return (
      <div className="app-header-hidden" style={{width: '100%', height: '0px', position: 'relative', zIndex: 3000, background: 'transparent'}}>
        <button
          className="show-header-btn"
          style={{position: 'absolute', left: '50%', top: '2px', transform: 'translateX(-50%)', background: '#fff', border: '1px solid #ccc', borderRadius: '50%', width: '24px', height: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', zIndex: 3001}}
          title={strings.showHeaderTooltip || 'Mostrar cabecera'}
          onClick={onToggleHeader}
        >
          <ChevronDown size={18} />
        </button>
      </div>
    );
  }

  return (
    <header className="app-header">
      <div className="header-left">
        <h1 className="app-title">{strings.logo}</h1>
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
        {/* Botón para ocultar la cabecera */}
        <button
          onClick={onToggleHeader}
          className="header-button"
          title={strings.hideHeaderTooltip || 'Ocultar cabecera'}
        >
          <ChevronDown size={20} />
        </button>
      </div>
    </header>
  );
}

export default Header;
