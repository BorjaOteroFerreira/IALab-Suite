import React from 'react';

function Header({ 
  tools, 
  rag, 
  tokensCount, 
  chatSidebarVisible, 
  configSidebarVisible,
  onToggleTools, 
  onToggleRag, 
  onToggleChatSidebar, 
  onToggleConfigSidebar, 
  onClearChat 
}) {
  return (
    <header className="app-header">
      <div className="header-left">
        <h1 className="app-title">🤖 AI Lab Suite</h1>
        <span className="tokens-counter">
          Contexto usado: {tokensCount} Tokens
        </span>
      </div>
      
      <div className="header-controls">
        <div className="toggle-group">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={tools}
              onChange={(e) => onToggleTools(e.target.checked)}
            />
            <span className="toggle-slider"></span>
            Tools
          </label>
          
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={rag}
              onChange={(e) => onToggleRag(e.target.checked)}
            />
            <span className="toggle-slider"></span>
            RAG
          </label>
        </div>

        <button
          onClick={onToggleChatSidebar}
          className={`header-button ${chatSidebarVisible ? 'active' : ''}`}
          title="Historial"
        >
          📁
        </button>
        
        <button
          onClick={onToggleConfigSidebar}
          className={`header-button ${configSidebarVisible ? 'active' : ''}`}
          title="Configuración"
        >
          ⚙️
        </button>
        
        <button
          onClick={onClearChat}
          className="header-button danger"
          title="Nuevo chat"
        >
          🗑️
        </button>
      </div>
    </header>
  );
}

export default Header;
