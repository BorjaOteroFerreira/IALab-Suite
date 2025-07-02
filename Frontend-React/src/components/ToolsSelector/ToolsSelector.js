import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';
import { Wrench, X, RefreshCw, Check, Settings, List, ListFilter, Search, Film, DollarSign, Image as ImageIcon, BarChart2, Key, Ban, AlertCircle } from 'lucide-react';
import './ToolsSelector.css';

const CATEGORY_ICONS = {
  search: <Search size={16} className="icon" />, // Búsqueda
  media: <Film size={16} className="icon" />, // Media
  finance: <DollarSign size={16} className="icon" />, // Finanzas
  image: <ImageIcon size={16} className="icon" />, // Imagen
  analysis: <BarChart2 size={16} className="icon" />, // Análisis
  utility: <Wrench size={16} className="icon" /> // Utilidad
};

const ToolsSelector = ({ tools, onToggleTools, socket }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [availableTools, setAvailableTools] = useState([]);
  const [selectedTools, setSelectedTools] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [activeCategory, setActiveCategory] = useState(null);
  const popupRef = useRef(null);

  // Cargar herramientas disponibles al montar el componente
  useEffect(() => {
    const initializeTools = async () => {
      setIsLoading(true);
      try {
        // Cargar herramientas disponibles y seleccionadas en paralelo
        await Promise.all([
          loadAvailableTools(),
          loadSelectedTools()
        ]);
        
        // Si no se han cargado herramientas, solicitarlas explícitamente por socket
        if (!availableTools.length && socket) {
          console.log('🔧 Solicitando registro de herramientas por socket...');
          socket.emit('request_tools_registry', {}, (response) => {
            console.log('🔧 Respuesta a solicitud de registro:', response);
          });
        }
      } catch (error) {
        console.error('Error inicializando herramientas:', error);
        setError('Error al cargar herramientas. Intente refrescar.');
      } finally {
        setIsLoading(false);
        setIsInitializing(false);
      }
    };
    
    initializeTools();
  }, [socket]);

  // Escuchar actualizaciones del socket
  useEffect(() => {
    if (!socket) return;

    const handleToolsUpdate = (data) => {
      console.log('🔧 Tools update received:', data);
      if (data && Array.isArray(data)) {
        setSelectedTools(data);
        
        // Muestra feedback visual para todos los cambios
        setTimeout(() => {
          data.forEach(toolName => {
            const toolElement = document.querySelector(`.tool-item[data-tool="${toolName}"]`);
            if (toolElement && !selectedTools.includes(toolName)) {
              toolElement.classList.add('tool-update-success');
              setTimeout(() => toolElement.classList.remove('tool-update-success'), 800);
            }
          });
          
          selectedTools.forEach(toolName => {
            if (!data.includes(toolName)) {
              const toolElement = document.querySelector(`.tool-item[data-tool="${toolName}"]`);
              if (toolElement) {
                toolElement.classList.add('tool-update-success');
                setTimeout(() => toolElement.classList.remove('tool-update-success'), 800);
              }
            }
          });
        }, 100);
      }
    };
    
    const handleToolsRegistry = (data) => {
      console.log('🔧 Tools registry received:', data);
      if (data && data.available_tools) {
        setAvailableTools(Object.values(data.available_tools || {}));
        setError(null);
        
        // También actualizar las herramientas seleccionadas si vienen en la respuesta
        if (data.active_tools) {
          setSelectedTools(data.active_tools);
          console.log('🔧 Herramientas seleccionadas actualizadas desde registry:', data.active_tools);
        }
      }
    };

    const handleSocketConnect = () => {
      console.log('🔧 Socket conectado, recuperando estado de herramientas...');
      // Recargar herramientas seleccionadas cuando se reconecte el socket
      loadSelectedTools();
    };

    socket.on('tools_selection_update', handleToolsUpdate);
    socket.on('tools_registry', handleToolsRegistry);
    socket.on('connect', handleSocketConnect);

    return () => {
      socket.off('tools_selection_update', handleToolsUpdate);
      socket.off('tools_registry', handleToolsRegistry);
      socket.off('connect', handleSocketConnect);
    };
  }, [socket, selectedTools]);

  // Actualizar loadAvailableTools para manejar correctamente errores
  const loadAvailableTools = async () => {
    try {
      setError(null);
      console.log('🔧 Iniciando carga de herramientas disponibles...');
      
      const response = await fetch('/api/tools/available');
      if (!response.ok) {
        console.error(`🔧 Error HTTP: ${response.status} - ${response.statusText}`);
        
        // Intentar leer el cuerpo de la respuesta para más detalles
        try {
          const errorBody = await response.text();
          console.error('Detalles de error:', errorBody);
          
          // Intentar analizar el cuerpo como JSON por si contiene información útil
          try {
            const errorJson = JSON.parse(errorBody);
            if (errorJson && errorJson.error) {
              throw new Error(errorJson.error);
            }
          } catch (jsonError) {
            // No es JSON válido, usamos el texto completo
          }
        } catch (e) {
          console.error('No se pudo leer el cuerpo de la respuesta de error');
        }
        
        throw new Error(`Error de servidor: ${response.status} ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log('🔧 Respuesta recibida:', result);
      
      if (result.success) {
        const toolsData = result.data;
        if (!toolsData || !toolsData.available_tools) {
          console.warn('🔧 No se recibieron herramientas disponibles en la respuesta');
          if (availableTools.length === 0) {
            setAvailableTools([]);
          }
          // Mantener las herramientas seleccionadas actuales
          if (toolsData && toolsData.active_tools) {
            setSelectedTools(toolsData.active_tools);
          }
        } else {
          // Convertir las herramientas a un formato más uniforme
          const tools = Object.entries(toolsData.available_tools || {}).map(([key, value]) => {
            return {
              name: key,
              description: value.description || 'Sin descripción',
              category: value.category || 'utility',
              available: value.available !== false,  // true por defecto si no se especifica
              requires_api_key: value.requires_api_key || false
            };
          });
          
          setAvailableTools(tools);
          // Cargar herramientas seleccionadas después de cargar las disponibles
          if (toolsData.active_tools) {
            setSelectedTools(toolsData.active_tools);
            console.log(`🔧 Herramientas activas desde backend: ${toolsData.active_tools.length}`);
          }
          console.log(`🔧 Herramientas cargadas: ${tools.length}`);
        }
      } else {
        console.error('🔧 Error en respuesta:', result.error);
        throw new Error(result.error || 'Error al cargar herramientas');
      }
    } catch (error) {
      console.error('🔧 Error cargando herramientas:', error);
      setError(`Error al cargar herramientas: ${error.message}`);
      return false;
    }
    return true;
  };

  const loadSelectedTools = async () => {
    try {
      console.log('🔧 Cargando herramientas seleccionadas desde el backend...');
      const response = await fetch('/api/tools/selected');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('🔧 Herramientas seleccionadas recibidas:', result);
      
      if (result.success) {
        const selectedToolsList = result.data.selected_tools || [];
        setSelectedTools(selectedToolsList);
        console.log(`🔧 ${selectedToolsList.length} herramientas seleccionadas cargadas desde el backend`);
        return selectedToolsList;
      } else {
        console.error('🔧 Error en respuesta de herramientas seleccionadas:', result.error);
        throw new Error(result.error || 'Error al cargar herramientas seleccionadas');
      }
    } catch (error) {
      console.error('🔧 Error cargando herramientas seleccionadas:', error);
      setError(`Error al cargar herramientas seleccionadas: ${error.message}`);
      return [];
    }
  };

  const handleToolToggle = async (toolName) => {
    const newSelectedTools = selectedTools.includes(toolName)
      ? selectedTools.filter(name => name !== toolName)
      : [...selectedTools, toolName];

    try {
      setSelectedTools(newSelectedTools);
      
      const toolElement = document.querySelector(`.tool-item[data-tool="${toolName}"]`);
      if (toolElement) {
        toolElement.classList.add('tool-updating');
        setTimeout(() => toolElement.classList.remove('tool-updating'), 800);
      }
      
      const response = await fetch('/api/tools/selected', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          selected_tools: newSelectedTools
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'Error al actualizar herramientas');
      }
      
      if (toolElement) {
        toolElement.classList.add('tool-update-success');
        setTimeout(() => toolElement.classList.remove('tool-update-success'), 800);
      }
    } catch (error) {
      console.error('Error actualizando herramientas:', error);
      // Revertir cambio en caso de error
      setSelectedTools(selectedTools);
      setError(error.message);
      
      const toolElement = document.querySelector(`.tool-item[data-tool="${toolName}"]`);
      if (toolElement) {
        toolElement.classList.add('tool-update-error');
        setTimeout(() => toolElement.classList.remove('tool-update-error'), 800);
      }
    }
  };

  const handleRefreshTools = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch('/api/tools/refresh', {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      if (result.success) {
        // Recargar tanto herramientas disponibles como seleccionadas
        await Promise.all([
          loadAvailableTools(),
          loadSelectedTools()
        ]);
        console.log('🔧 Herramientas refrescadas correctamente');
      } else {
        throw new Error(result.error || 'Failed to refresh tools');
      }
    } catch (error) {
      console.error('Error refreshing tools:', error);
      setError(`Error al refrescar herramientas: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Agrupar herramientas por categoría
  const groupToolsByCategory = (tools) => {
    return tools.reduce((groups, tool) => {
      const category = tool.category || 'utility';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(tool);
      return groups;
    }, {});
  };

  // Determinar categorías y la activa
  const categories = Object.entries(groupToolsByCategory(availableTools));
  const defaultCategory = categories.length > 0 ? categories[0][0] : null;
  const currentCategory = activeCategory || defaultCategory;
  const currentTools = currentCategory ? groupToolsByCategory(availableTools)[currentCategory] || [] : [];

  // Selección visual y lógica
  const handleCategoryClick = (cat) => setActiveCategory(cat);
  const handleCardClick = (tool) => {
    if (!tool.available) return;
    handleToolToggle(tool.name);
  };

  // Auto-ocultar errores después de 5 segundos
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  return (
    <div className="tools-selector">
      <button
        onClick={() => onToggleTools(!tools)}
        className={`tools-button ${tools ? 'active' : ''} ${isLoading ? 'loading' : ''} ${isInitializing ? 'initializing' : ''}`}
        title={`Herramientas ${isLoading ? '(Cargando...)' : isInitializing ? '(Inicializando...)' : tools ? '(Activadas)' : '(Desactivadas)'}`}
      >
        <Wrench size={23} />
        {selectedTools.length > 0 && (
          <span className="tools-count">{selectedTools.length}</span>
        )}
        {(isLoading || isInitializing) && <span className="tools-loading-indicator"></span>}
      </button>

      {tools && (
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="tools-config-button"
          title="Seleccionar herramientas"
        >
          <ListFilter size={14} />
        </button>
      )}

      {isOpen && ReactDOM.createPortal(
        <div className="tools-overlay">
          <div className="tools-popup" ref={popupRef}>
            {/* Sidebar de categorías */}
            <div className="tools-sidebar">
              <div className="tools-sidebar-header">
                <h3 className="tools-sidebar-title">
                  <Wrench size={18} style={{marginRight: 6}} /> Herramientas
                </h3>
                <p className="tools-sidebar-subtitle">{selectedTools.length} de {availableTools.length} seleccionadas</p>
              </div>
              <nav className="category-nav">
                {categories.map(([cat, toolsArr]) => {
                  // Calcular seleccionadas en esta categoría
                  const selectedInCategory = toolsArr.filter(tool => selectedTools.includes(tool.name)).length;
                  const totalInCategory = toolsArr.length;
                  return (
                    <button
                      key={cat}
                      className={`category-nav-item${cat === currentCategory ? ' active' : ''}`}
                      onClick={() => handleCategoryClick(cat)}
                    >
                      <span className="icon">{CATEGORY_ICONS[cat] || <Settings size={16} className="icon" />}</span>
                      {cat.charAt(0).toUpperCase() + cat.slice(1)}
                      <span className="category-count">{selectedInCategory}/{totalInCategory}</span>
                    </button>
                  );
                })}
              </nav>
            </div>
            {/* Contenido principal */}
            <div className="tools-main">
              <div className="tools-main-header">
                <h2 className="tools-main-title">{currentCategory ? currentCategory.charAt(0).toUpperCase() + currentCategory.slice(1) : ''}</h2>
                <div className="tools-actions">
                  <button
                    className="action-button"
                    onClick={handleRefreshTools}
                    title="Refrescar"
                    disabled={isLoading}
                  >
                    <RefreshCw size={16} />
                  </button>
                  <button
                    className="action-button"
                    onClick={() => setIsOpen(false)}
                    title="Cerrar"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
              <div className="tools-content">
                {error && (
                  <div className="tools-error">
                    <AlertCircle size={14} style={{marginRight: 4, color: '#e74c3c'}} /> {error}
                  </div>
                )}
                {isLoading || isInitializing ? (
                  <div className="tools-loading">
                    <div className="loading-spinner" />
                    <span>{isInitializing ? 'Inicializando herramientas...' : 'Cargando herramientas...'}</span>
                  </div>
                ) : (
                  <>
                    {currentTools.length === 0 ? (
                      <div className="empty-state">
                        <div className="empty-state-icon">🔍</div>
                        <div className="empty-state-title">No hay herramientas en esta categoría</div>
                        <div className="empty-state-description">Selecciona otra categoría o refresca.</div>
                      </div>
                    ) : (
                      <div className="tools-grid">
                        {currentTools.map((tool) => (
                          <div
                            key={tool.name}
                            className={`tool-card${selectedTools.includes(tool.name) ? ' selected' : ''}${!tool.available ? ' disabled' : ''}`}
                            onClick={() => handleCardClick(tool)}
                          >
                            <div className="tool-card-header">
                              <div className="tool-checkbox-custom">
                                {selectedTools.includes(tool.name) ? <Check size={14} /> : ''}
                              </div>
                              <div className="tool-info">
                                <h4 className="tool-name">{tool.name}</h4>
                                <p className="tool-description">{tool.description}</p>
                                <div className="tool-badges">
                                  {tool.requires_api_key && (
                                    <span className="tool-badge badge-api-key"> <Key size={12} style={{marginRight: 2}} /> API Key</span>
                                  )}
                                  {!tool.available && (
                                    <span className="tool-badge badge-unavailable"> <Ban size={12} style={{marginRight: 2}} /> No disponible</span>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
          <div className="tools-overlay-bg" onClick={() => setIsOpen(false)} />
        </div>,
        document.body
      )}
    </div>
  );
};

export default ToolsSelector;
