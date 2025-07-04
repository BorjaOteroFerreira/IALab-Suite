import React from 'react';
import './Header.css';
import { Download, Folder, Settings, Plus, MessagesSquare, Database } from 'lucide-react';
import ToolsSelector from '../ToolsSelector/ToolsSelector';
import { useChatContext } from '../../hooks/useChatContext';

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
  onOpenDownloader
}) {
  // Obtener el socket del contexto de chat
  const { socket } = useChatContext();
  return (
    <header className="app-header">
      <div className="header-left">
        <h1 className="app-title">🤖 AI Lab Suite</h1>
      </div>
      
      <div className="header-controls">
        <button
          onClick={onClearChat}
          className="header-button"
          title="Nuevo chat"
        >
          <Plus size={22} />
        </button>
        <button
          onClick={onToggleChatSidebar}
          className={`header-button ${chatSidebarVisible ? 'active' : ''}`}
          title="Historial"
        >
          <MessagesSquare size={22} />
        </button>
        
        <button
          onClick={onToggleConfigSidebar}
          className={`header-button ${configSidebarVisible ? 'active' : ''}`}
          title="Configuración"
        >
          <Settings size={22} />
        </button>
        

        
        <button
          onClick={onOpenDownloader}
          className="header-button"
          title="Descargar modelos GGUF"
        >
          <Download size={22} />
        </button>
      </div>
    </header>
  );
}

export default Header;
