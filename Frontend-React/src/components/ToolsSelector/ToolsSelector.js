import React, { useState, useEffect, useRef } from 'react';
import { Wrench, X, RefreshCw, Check, Settings, List, ListFilter } from 'lucide-react';
import './ToolsSelector.css';

const ToolsSelector = ({ tools, onToggleTools, socket }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [availableTools, setAvailableTools] = useState([]);
  const [selectedTools, setSelectedTools] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const popupRef = useRef(null); // Referencia al popup

  // Efecto para manejar la apertura del popup sin recolocación
  useEffect(() => {
    if (isOpen && popupRef.current) {
      // Forzar reflow/repaint antes de que comience la animación
      const popup = popupRef.current;
      popup.style.opacity = '0';
      popup.style.transform = 'translate(-50%, -60%) scale(0.95)';
      
      // Pequeño truco para forzar un recálculo inmediato antes de la animación
      void popup.offsetWidth;
      
      // Restaurar estilos para permitir que la animación CSS se encargue
      popup.style.opacity = '';
      popup.style.transform = '';
    }
  }, [isOpen]);

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
          // En lugar de borrar herramientas, mantener las existentes si las hay
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
      // Mostrar un error más descriptivo
      setError(`Error al cargar herramientas: ${error.message}`);
      // No lanzamos el error, simplemente mostramos el mensaje y continuamos
      // con las herramientas que pudimos cargar anteriormente
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
      // Actualización optimista de la UI
      setSelectedTools(newSelectedTools);
      
      // Elemento visual para feedback temporal
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
      
      // Muestra un indicador visual de éxito
      if (toolElement) {
        toolElement.classList.add('tool-update-success');
        setTimeout(() => toolElement.classList.remove('tool-update-success'), 800);
      }
    } catch (error) {
      console.error('Error actualizando herramientas:', error);
      // Revertir cambio en caso de error
      setSelectedTools(selectedTools);
      setError(error.message);
      
      // Muestra un indicador visual de error
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

  const getCategoryIcon = (category) => {
    const icons = {
      search: '🔍',
      media: '🎥',
      finance: '💰',
      image: '🖼️',
      analysis: '📊',
      utility: '🔧'
    };
    return icons[category] || '⚙️';
  };

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

      {isOpen && (
        <>
          <div className="tools-overlay" onClick={() => setIsOpen(false)} />
          <div className="tools-popup" ref={popupRef}>
            <div className="tools-header">
              <h3>🔧 Herramientas Disponibles</h3>
              <div className="tools-header-actions">
                <button
                  onClick={handleRefreshTools}
                  className="refresh-button"
                  disabled={isLoading}
                  title="Refrescar herramientas"
                >
                  <RefreshCw size={16} className={isLoading ? 'spinning' : ''} />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="close-button"
                  title="Cerrar"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            {error && (
              <div className="tools-error">
                ❌ {error}
              </div>
            )}

            <div className="tools-content">
              {isLoading || isInitializing ? (
                <div className="tools-loading">
                  <div className="loading-spinner" />
                  <span>{isInitializing ? 'Inicializando herramientas...' : 'Cargando herramientas...'}</span>
                </div>
              ) : (
                <>
                  <div className="tools-summary">
                    <span>{selectedTools.length} de {availableTools.length} herramientas seleccionadas</span>
                  </div>

                  <div className="tools-list">
                    {Object.entries(groupToolsByCategory(availableTools)).map(([category, tools]) => (
                      <div key={category} className="tools-category">
                        <h4 className="category-title">
                          {getCategoryIcon(category)} {category.charAt(0).toUpperCase() + category.slice(1)}
                        </h4>
                        <div className="category-tools">
                          {tools.map((tool) => (
                            <div
                              key={tool.name}
                              className={`tool-item ${!tool.available ? 'disabled' : ''}`}
                              data-tool={tool.name}
                            >
                              <label className="tool-checkbox">
                                <input
                                  type="checkbox"
                                  checked={selectedTools.includes(tool.name)}
                                  onChange={() => handleToolToggle(tool.name)}
                                  disabled={!tool.available}
                                />
                                <span className="checkmark">
                                  {selectedTools.includes(tool.name) && <Check size={12} />}
                                </span>
                                <div className="tool-info">
                                  <span className="tool-name">{tool.name}</span>
                                  <span className="tool-description">{tool.description}</span>
                                  {tool.requires_api_key && (
                                    <span className="api-key-indicator">🔑 API Key</span>
                                  )}
                                  {!tool.available && (
                                    <span className="unavailable-indicator">❌ No disponible</span>
                                  )}
                                </div>
                              </label>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ToolsSelector;
