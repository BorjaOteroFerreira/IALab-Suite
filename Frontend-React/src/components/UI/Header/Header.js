import React from 'react';
import { Download, Folder, Settings, Plus, MessagesSquare, Database, Volume2, VolumeX } from 'lucide-react';
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
  setTTSEnabled
}) {
  // Obtener el socket del contexto de chat
  const { socket } = useChatContext();
  const { getStrings } = useLanguage();
  const strings = getStrings('header');
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
      </div>
    </header>
  );
}

export default Header;
