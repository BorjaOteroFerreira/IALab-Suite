import React, { useState, useEffect, useMemo } from 'react';
import { useChatContext } from '../../hooks/useChatContext';
import './ConfigSidebar.css';

const ConfigSidebar = ({ visible, onClose }) => {
  const { modelConfig, setModelConfig, applyConfig, unloadModel, fetchModelsAndFormats } = useChatContext();
  const [modelsList, setModelsList] = useState([]);
  const [allModelsList, setAllModelsList] = useState([]); // Lista completa incluyendo .mmproj
  const [isApplying, setIsApplying] = useState(false);

  // Obtener la lista de modelos al cargar el componente
  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('ConfigSidebar: Cargando modelos...');
        
        if (fetchModelsAndFormats) {
          const data = await fetchModelsAndFormats();          if (data && data.models && Array.isArray(data.models)) {
            console.log(`ConfigSidebar: ${data.models.length} modelos cargados desde el backend`);
              // Guardar lista completa para detectar archivos mmproj
            setAllModelsList(data.models);
            
            // Filtrar archivos que contengan "mmproj" en el nombre
            const filteredModels = data.models.filter(model => 
              !model.toLowerCase().includes('mmproj')
            );
            
            console.log(`ConfigSidebar: ${filteredModels.length} modelos después de filtrar mmproj`);
            setModelsList(filteredModels);          } else {
            console.warn('ConfigSidebar: No se encontraron modelos válidos en la respuesta del backend');
            setModelsList([]);
            setAllModelsList([]);
          }
        } else {
          console.warn('ConfigSidebar: fetchModelsAndFormats no disponible');
          setModelsList([]);
          setAllModelsList([]);
        }
      } catch (error) {
        console.error('ConfigSidebar: Error al cargar los modelos:', error);
        setModelsList([]);
        setAllModelsList([]);
      }
    };
    
    fetchData();
  }, [fetchModelsAndFormats]);  // Función para formatear el nombre del modelo de forma más legible
  const formatModelName = (modelPath) => {
    if (!modelPath) return '';
    
    // Extraer solo el nombre del archivo de la última barra invertida
    const fileName = modelPath.split('\\').pop() || modelPath.split('/').pop();
    let cleanName = fileName;
    
    // Quitar extensiones comunes
    cleanName = cleanName.replace(/\.(gguf|bin|pt|pth|safetensors)$/i, '');
    
    // Quitar información de cuantización del nombre (Q4, Q3, Q8, etc.)
    cleanName = cleanName.replace(/[-_]?Q\d+(_K|_M|_KM|_KS)?/gi, '');
    
    // Quitar información de tamaño del nombre (7b, 13b, etc.)
    cleanName = cleanName.replace(/[-_]?(\d+)\.?\d*[Bb]/gi, '');
    
    // Reemplazar guiones y guiones bajos con espacios
    cleanName = cleanName.replace(/[-_]/g, ' ');
    
    // Limpiar espacios múltiples
    cleanName = cleanName.replace(/\s+/g, ' ').trim();
    
    // Capitalizar las primeras letras de cada palabra
    cleanName = cleanName.replace(/\b\w/g, l => l.toUpperCase());
    
    return cleanName;
  };  // Función para obtener información adicional del modelo
  const getModelInfo = (modelPath) => {
    if (!modelPath) return { size: null, type: null, quantization: null, icon: '🤖', hasVision: false };
    
    const fileName = modelPath.split('\\').pop() || modelPath.split('/').pop();
    
    // Detectar tamaño del modelo
    const size = fileName.match(/(\d+)\.?\d*[Bb]/i);
    
    // Detectar tipo de modelo
    const type = fileName.match(/(chat|instruct|base|code)/i);
    
    // Detectar cuantización (Q4, Q3, Q8, etc.)
    const quantization = fileName.match(/Q(\d+)(_K|_M|_KM|_KS)?/i);
    
    // Verificar si hay un archivo con "mmproj" en el nombre en la misma carpeta del modelo
    let hasVision = false;
    
    if (allModelsList.length > 0) {
      // Obtener la carpeta del modelo actual
      const folderPath = modelPath.substring(0, Math.max(
        modelPath.lastIndexOf('/'), 
        modelPath.lastIndexOf('\\')
      ));
      
      hasVision = allModelsList.some(model => {
        // Obtener la carpeta del modelo en la lista
        const modelFolder = model.substring(0, Math.max(
          model.lastIndexOf('/'), 
          model.lastIndexOf('\\')
        ));
        
        const modelFileName = model.split(/[/\\]/).pop();
        
        // Verificar si está en la misma carpeta, contiene "mmproj" y es un archivo diferente
        const isSameFolder = modelFolder === folderPath;
        const isMMProj = modelFileName.toLowerCase().includes('mmproj');
        const isDifferentFile = model !== modelPath;
        
        return isSameFolder && isMMProj && isDifferentFile;
      });
    }
    
    // Seleccionar icono basado en el tipo (NO cambiar por visión)
    let icon = '🤖';
    if (type) {
      const typeStr = type[0].toLowerCase();
      if (typeStr === 'chat') icon = '💬';
      else if (typeStr === 'instruct') icon = '📝';
      else if (typeStr === 'code') icon = '💻';
    }
    
    return {
      size: size ? size[0].toUpperCase() : null,
      type: type ? type[0].toLowerCase() : null,
      quantization: quantization ? quantization[0].toUpperCase() : null,
      icon: icon,
      hasVision: hasVision
    };
  };

  // Estado para controlar si el selector está abierto
  const [isModelSelectorOpen, setIsModelSelectorOpen] = useState(false);

  // Cerrar dropdown al hacer clic fuera
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isModelSelectorOpen && !event.target.closest('.model-selector-trigger') && !event.target.closest('.model-selector-dropdown')) {
        setIsModelSelectorOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isModelSelectorOpen]);

  // Función para seleccionar un modelo
  const handleModelSelect = (modelPath) => {
    setModelConfig({
      ...modelConfig,
      modelPath: modelPath
    });
    setIsModelSelectorOpen(false);
  };

  // Manejar cambios en los inputs
  const handleChange = (e) => {
    const { name, value } = e.target;
    
    setModelConfig({
      ...modelConfig,
      [name]: value
    });
  };

  // Manejar envío del formulario
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validar campos obligatorios
    if (!modelConfig.modelPath) {
      alert('Por favor selecciona un modelo');
      return;
    }
    
    setIsApplying(true);
    
    try {
      console.log('ConfigSidebar: Aplicando configuración...', modelConfig);
      
      await applyConfig(modelConfig);
      
      console.log('ConfigSidebar: Configuración aplicada exitosamente');
      
      // Cerrar el sidebar después de aplicar la configuración
      setTimeout(() => {
        if (onClose) {
          onClose();
        }
      }, 1000);
      
    } catch (error) {
      console.error('ConfigSidebar: Error al aplicar configuración:', error);
      alert('Error al aplicar la configuración. Revisa la consola para más detalles.');
    } finally {
      setIsApplying(false);
    }
  };
  
  // Memoizar la información de los modelos para evitar recálculos innecesarios
  const modelsWithInfo = useMemo(() => {
    console.log(`🔄 Recalculando modelos. modelsList: ${modelsList.length}, allModelsList: ${allModelsList.length}`);
    
    return modelsList.map(model => {
      const info = getModelInfo(model);
      const displayName = formatModelName(model);
      
      if (info.hasVision) {
        console.log(`👁️ Modelo con visión detectado: ${displayName} (${model})`);
      }
      
      return {
        path: model,
        info,
        displayName
      };
    });
  }, [modelsList, allModelsList]);

  return (
    <div className={`config-sidebar ${visible ? 'visible' : 'hidden'}`}>
      <div className="sidebar-header">
        <h5>⚙️ Configuración del modelo</h5>
        {onClose && (
          <button type="button" className="close-btn" onClick={onClose} title="Cerrar">
            ✕
          </button>
        )}
      </div>
      
      <form onSubmit={handleSubmit}>        <div className="form-group">
          <label htmlFor="modelPath" className="model-label">
            🤖 Modelo de IA:
          </label>          <select
            className="form-control model-select"
            id="modelPath"
            name="modelPath"
            value={modelConfig.modelPath || ''}
            onChange={handleChange}
            required
            disabled={modelsList.length === 0}
          >
            <option value="" className="placeholder-option">
              {modelsList.length === 0 ? '⏳ Cargando modelos...' : '🔍 Selecciona un modelo'}
            </option>{modelsWithInfo.map(({ path, info, displayName }, index) => {
              return (
                <option key={index} value={path} className="model-option">
                  {displayName}
                  {info.size && ` • ${info.size}`}
                  {info.type && ` • ${info.type}`}
                </option>
              );
            })}</select>
          
          {/* Ocultar el select tradicional */}
          <style>{`
            .form-control.model-select {
              display: none !important;
            }
          `}</style>
          
          {/* Selector moderno de modelos */}
          <button
            type="button"
            className={`model-selector-trigger ${isModelSelectorOpen ? 'open' : ''}`}
            onClick={() => setIsModelSelectorOpen(!isModelSelectorOpen)}
            disabled={modelsList.length === 0}
          >            {modelConfig.modelPath ? (
              <div className="selected-model-display">
                <span className="model-icon">{
                  modelsWithInfo.find(m => m.path === modelConfig.modelPath)?.info.icon || '🤖'
                }</span>
                <div className="model-details">
                  <span className="model-name">{
                    modelsWithInfo.find(m => m.path === modelConfig.modelPath)?.displayName || formatModelName(modelConfig.modelPath)
                  }</span>
                  <div className="model-badges">
                    {modelsWithInfo.find(m => m.path === modelConfig.modelPath)?.info.size && (
                      <span className="model-size">{modelsWithInfo.find(m => m.path === modelConfig.modelPath).info.size}</span>
                    )}
                    {modelsWithInfo.find(m => m.path === modelConfig.modelPath)?.info.quantization && (
                      <span className="model-quantization">{modelsWithInfo.find(m => m.path === modelConfig.modelPath).info.quantization}</span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="placeholder-display">
                {modelsList.length === 0 ? (
                  <>⏳ Cargando modelos...</>
                ) : (
                  <>🔍 Selecciona un modelo</>
                )}
              </div>
            )}
            <span className={`dropdown-arrow ${isModelSelectorOpen ? 'open' : ''}`}>▼</span>
          </button>
          
          {/* Lista de modelos como cards */}
          {isModelSelectorOpen && (
            <div className="model-selector-dropdown">
              <div className="model-cards-container">
                {modelsWithInfo.map(({ path, info, displayName }, index) => {
                  const isSelected = modelConfig.modelPath === path;
                  
                  return (                    <div
                      key={index}
                      className={`model-card ${isSelected ? 'selected' : ''} ${info.hasVision ? 'has-vision' : ''}`}
                      onClick={() => handleModelSelect(path)}
                    >
                      <div className="model-card-icon">{info.icon}</div>
                      <div className="model-card-info">
                        <div className="model-card-name">{displayName}</div>                        <div className="model-card-meta">
                          {info.size && <span className="model-meta-size">{info.size}</span>}
                          {info.quantization && <span className="model-meta-quantization">{info.quantization}</span>}
                          {info.type && <span className="model-meta-type">{info.type}</span>}
                          {info.hasVision && <span className="model-meta-vision">visión</span>}
                        </div>
                      </div>
                      {isSelected && <div className="selected-indicator">✓</div>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          
          {/* Mostrar el modelo seleccionado */}
          {modelConfig.modelPath && (
            <div className="selected-model-info">
              ✅ Modelo seleccionado: <strong>{formatModelName(modelConfig.modelPath)}</strong>
            </div>
          )}
          
          <div className="model-info">
            📊 {modelsList.length} modelo{modelsList.length !== 1 ? 's' : ''} disponible{modelsList.length !== 1 ? 's' : ''}
          </div>
        </div>
        
        <div className="form-group">
          <label htmlFor="temperature">Temperatura:</label>
          <input
            type="number"
            className="form-control"
            id="temperature"
            name="temperature"
            step="0.01"
            min="0"
            max="1"
            placeholder="Ejemplo: 0.8"
            value={modelConfig.temperature || 0.8}
            onChange={handleChange}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="context">Contexto máximo:</label>
          <input
            type="number"
            className="form-control"
            id="context"
            name="context"
            placeholder="Ejemplo: 2048"
            value={modelConfig.context || 2048}
            onChange={handleChange}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="systemMessage">Mensaje de sistema:</label>
          <textarea
            className="form-control"
            id="systemMessage"
            name="systemMessage"
            rows="3"
            placeholder="Eres un asistente en español. Debes responder siempre en español."
            value={modelConfig.systemMessage || 'Eres un asistente en español. Debes responder siempre en español'}
            onChange={handleChange}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="gpuLayers">
            Capas GPU: <span className="slider-value">{modelConfig.gpuLayers || -1}</span>
          </label>
          <input
            type="range"
            className="form-control slider"
            id="gpuLayers"
            name="gpuLayers"
            min="-1"
            max="100"
            step="1"
            value={modelConfig.gpuLayers || -1}
            onChange={handleChange}
          />
          <div className="slider-labels">
            <span>-1</span>
            <span>100</span>
          </div>
        </div>
        
        <div className="config-buttons">
          <button 
            type="submit" 
            className={`btn btn-primary ${isApplying ? 'loading' : ''}`}
            disabled={isApplying}
          >
            {isApplying ? 'Aplicando...' : 'Aplicar configuración'}
          </button>
          <button 
            type="button" 
            className="btn btn-secondary" 
            onClick={unloadModel}
            disabled={isApplying}
          >
            Desmontar
          </button>
        </div>
      </form>
    </div>
  );
};

export default ConfigSidebar;
