import React, { useState, useEffect, useMemo } from 'react';
import { useChatContext } from '../../../hooks/useChatContext';
import { useLanguage } from '../../../context/LanguageContext';
import './ConfigSidebar.css';

const ConfigSidebar = ({ visible, onClose }) => {
  const { modelConfig, setModelConfig, applyConfig, unloadModel, fetchModelsAndFormats } = useChatContext();
  const [modelsList, setModelsList] = useState([]);
  const [allModelsList, setAllModelsList] = useState([]); // Lista completa incluyendo .mmproj
  const [isApplying, setIsApplying] = useState(false);
  // Obtener strings dinámicamente en cada render para reflejar el idioma actual
  const { getStrings, currentLang } = useLanguage();
  const strings = getStrings('configSidebar');

  // Guardar el valor por defecto anterior en un ref
  const prevDefaultRef = React.useRef(getStrings('configSidebar').textareaDefault);
  // Estado local para saber si el usuario ha editado el textarea
  const [userEdited, setUserEdited] = useState(false);

  // Obtener el valor por defecto actual del idioma
  const defaultText = getStrings('configSidebar').textareaDefault;

  // Determinar el valor a mostrar en el textarea
  const textareaValue = useMemo(() => {
    if (
      !userEdited && (
        modelConfig.systemMessage === undefined ||
        modelConfig.systemMessage === null ||
        modelConfig.systemMessage === '' ||
        modelConfig.systemMessage === prevDefaultRef.current
      )
    ) {
      return defaultText;
    }
    return modelConfig.systemMessage ?? defaultText;
    // eslint-disable-next-line
  }, [userEdited, modelConfig.systemMessage, defaultText]);

  // Actualizar el ref del valor por defecto anterior en cada render
  useEffect(() => {
    prevDefaultRef.current = defaultText;
  }, [defaultText]);

  // Cambiar el texto por defecto de systemMessage al cambiar de idioma si el usuario no lo ha tocado
  useEffect(() => {
    const defaultText = getStrings('configSidebar').textareaDefault;
    // Solo actualizar si el usuario NO ha editado el textarea (valor local igual al anterior por defecto, vacío, null o undefined)
    if (
      modelConfig.systemMessage === prevDefaultRef.current ||
      modelConfig.systemMessage === undefined ||
      modelConfig.systemMessage === null ||
      modelConfig.systemMessage === ''
    ) {
      setModelConfig({
        ...modelConfig,
        systemMessage: defaultText
      });
    }
    prevDefaultRef.current = defaultText;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentLang, modelConfig.systemMessage]);

  // Sincronizar modelConfig.systemMessage con el default del idioma si el usuario no ha editado o el valor es vacío
  useEffect(() => {
    if (
      !userEdited ||
      modelConfig.systemMessage === undefined ||
      modelConfig.systemMessage === null ||
      modelConfig.systemMessage === ''
    ) {
      setModelConfig({
        ...modelConfig,
        systemMessage: defaultText
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultText, currentLang]);

  // Obtener la lista de modelos al cargar el componente
  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('ConfigSidebar: Cargando modelos...');
        if (fetchModelsAndFormats) {
          const data = await fetchModelsAndFormats();
          if (data && data.models && Array.isArray(data.models)) {
            // Normalizar: asegurar que todos los modelos sean objetos {path, size}
            const normalizedModels = data.models
              .map(model => {
                if (typeof model === 'string') {
                  return { path: model, size: null };
                }
                if (model && typeof model === 'object' && model.path) {
                  return { path: model.path, size: model.size ?? null };
                }
                return null;
              })
              .filter(Boolean);
            setAllModelsList(normalizedModels);
            // Filtrar archivos que contengan "mmproj" en el nombre
            const filteredModels = normalizedModels.filter(modelObj =>
              typeof modelObj.path === 'string' && !modelObj.path.toLowerCase().includes('mmproj')
            );
            setModelsList(filteredModels);
          } else {
            setModelsList([]);
            setAllModelsList([]);
          }
        } else {
          setModelsList([]);
          setAllModelsList([]);
        }
      } catch (error) {
        setModelsList([]);
        setAllModelsList([]);
      }
    };
    fetchData();
  }, [fetchModelsAndFormats]);

  // Cuando el usuario edita el textarea, marcar como editado y actualizar config
  const handleSystemMessageChange = (e) => {
    setUserEdited(true);
    setModelConfig({
      ...modelConfig,
      systemMessage: e.target.value
    });
  };

  // Adaptar el resto del código para trabajar con objetos {path, size}
  const formatModelName = (modelObjOrPath) => {
    if (!modelObjOrPath) return '';
    const path = typeof modelObjOrPath === 'object' ? modelObjOrPath.path : modelObjOrPath;
    if (!path) return '';
    const fileName = path.split(/[/\\]/).pop();
    let cleanName = fileName || '';
    cleanName = cleanName.replace(/\.(gguf|bin|pt|pth|safetensors)$/i, '');
    cleanName = cleanName.replace(/[-_]?Q\d+(_K|_M|_KM|_KS)?/gi, '');
    cleanName = cleanName.replace(/[-_]?(\d+)\.?\d*[Bb]/gi, '');
    cleanName = cleanName.replace(/[-_]/g, ' ');
    cleanName = cleanName.replace(/\s+/g, ' ').trim();
    cleanName = cleanName.replace(/\b\w/g, l => l.toUpperCase());
    return cleanName;
  };

  const getModelInfo = (modelObjOrPath) => {
    if (!modelObjOrPath) return { size: null, type: null, quantization: null, icon: '🤖', hasVision: false, fileSize: null };
    const path = typeof modelObjOrPath === 'object' ? modelObjOrPath.path : modelObjOrPath;
    if (!path) return { size: null, type: null, quantization: null, icon: '🤖', hasVision: false, fileSize: null };
    const fileName = path.split(/[/\\]/).pop();
    const size = fileName.match(/(\d+)\.?\d*[Bb]/i);
    const type = fileName.match(/(chat|instruct|base|code)/i);
    const quantization = fileName.match(/Q(\d+)(_K|_M|_KM|_KS)?/i);
    let hasVision = false;
    if (allModelsList.length > 0) {
      const folderPath = path.substring(0, Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\')));
      hasVision = allModelsList.some(model => {
        const modelPath = typeof model === 'object' ? model.path : model;
        const modelFolder = modelPath.substring(0, Math.max(modelPath.lastIndexOf('/'), modelPath.lastIndexOf('\\')));
        const modelFileName = modelPath.split(/[/\\]/).pop();
        const isSameFolder = modelFolder === folderPath;
        const isMMProj = modelFileName && modelFileName.toLowerCase().includes('mmproj');
        const isDifferentFile = modelPath !== path;
        return isSameFolder && isMMProj && isDifferentFile;
      });
    }
    let icon = '🤖';
    if (type) {
      const typeStr = type[0].toLowerCase();
      if (typeStr === 'chat') icon = '💬';
      else if (typeStr === 'instruct') icon = '📝';
      else if (typeStr === 'code') icon = '💻';
    }
    let fileSize = typeof modelObjOrPath === 'object' && modelObjOrPath.size ? modelObjOrPath.size : null;
    return {
      size: size ? size[0].toUpperCase() : null,
      type: type ? type[0].toLowerCase() : null,
      quantization: quantization ? quantization[0].toUpperCase() : null,
      icon: icon,
      hasVision: hasVision,
      fileSize: fileSize
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

  // seleccionar un modelo
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
      alert(strings.selectModelAlert);
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
      alert(strings.errorApply);
    } finally {
      setIsApplying(false);
    }
  };
  
  // Memoizar la información de los modelos para evitar recálculos innecesarios
  const modelsWithInfo = useMemo(() => {
    // Ordenar por la primera letra del nombre (ascendente) y, si hay empate, por tamaño (descendente)
    const sorted = [...modelsList].sort((a, b) => {
      const nameA = formatModelName(a).toLowerCase();
      const nameB = formatModelName(b).toLowerCase();
      const firstA = nameA.charAt(0);
      const firstB = nameB.charAt(0);
      if (firstA < firstB) return -1;
      if (firstA > firstB) return 1;
      // Si la primera letra es igual, ordenar por tamaño descendente (mayor a menor)
      const sizeA = (typeof a.size === 'number') ? a.size : (parseFloat(a.size) || 0);
      const sizeB = (typeof b.size === 'number') ? b.size : (parseFloat(b.size) || 0);
      return sizeB - sizeA;
    });
    return sorted.map(modelObj => {
      const info = getModelInfo(modelObj);
      const displayName = formatModelName(modelObj);
      return {
        path: typeof modelObj === 'object' ? modelObj.path : modelObj,
        info,
        displayName
      };
    });
  }, [modelsList, allModelsList]);

  // Obtener el modelo seleccionado
  const selected = modelsWithInfo.find(m => m.path === modelConfig.modelPath) || {info:{}};

  return (
    <div className={`config-sidebar ${visible ? 'visible' : 'hidden'}`}>
      <div className="sidebar-header config-title-gradient">
        <h5 className="config-title-text config-title-text-gradient">{strings.title}</h5>
      </div>
      <form onSubmit={handleSubmit}>        <div className="form-group">

          {/* Agrupar trigger y dropdown en un contenedor relativo */}
          <div className="model-selector-wrapper" style={{ position: 'relative' }}>
            <select
              className="form-control model-select"
              id="modelPath"
              name="modelPath"
              value={modelConfig.modelPath || ''}
              onChange={handleChange}
              required
              disabled={modelsList.length === 0}
            >
              <option value="" className="placeholder-option">
                {modelsList.length === 0 ? `⏳ ${strings.loadingModels}` : `🔍 ${strings.selectModel}`}
              </option>
              {modelsWithInfo.map(({ path, info, displayName }, index) => (
                <option key={index} value={path} className="model-option">
                  {displayName}
                  {info.size && ` • ${info.size}`}
                  {info.type && ` • ${info.type}`}
                </option>
              ))}
            </select>
            <style>{`
              .form-control.model-select {
                display: none !important;
              }
            `}</style>
            <button
              type="button"
              className={`model-selector-trigger ${isModelSelectorOpen ? 'open' : ''}`}
              onClick={() => setIsModelSelectorOpen(!isModelSelectorOpen)}
              disabled={modelsList.length === 0}
            >
              {modelConfig.modelPath ? (
                <div className="selected-model-display">
                  {/* <span className="model-icon">{selected.info.icon || '🤖'}</span> */}
                  <div className="model-details">
                    <span className="model-name">{selected.displayName || formatModelName(modelConfig.modelPath)}</span>
                    <div className="model-badges">
                      {selected.info.size && (
                        <span className="model-size">{selected.info.size}</span>
                      )}
                      {selected.info.quantization && (
                        <span className="model-quantization">{selected.info.quantization}</span>
                      )}
                      {selected.info.type && (
                        <span className="model-meta-type">{selected.info.type}</span>
                      )}
                      {selected.info.hasVision && (
                        <span className="model-meta-vision">{strings.vision}</span>
                      )}
                      {selected.info.fileSize && selected.info.fileSize > 0 && (
                        <span className="model-meta-weight">{(selected.info.fileSize / (1024*1024*1024)).toFixed(2)} {strings.gb}</span>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="placeholder-display">
                  {modelsList.length === 0 ? (
                    <>⏳ {strings.loadingModels}</>
                  ) : (
                    <>🔍 {strings.selectModel}</>
                  )}
                </div>
              )}
              <span className={`dropdown-arrow ${isModelSelectorOpen ? 'open' : ''}`}>▼</span>
            </button>
            {/* Dropdown ahora está dentro del wrapper relativo */}
            {isModelSelectorOpen && (
              <div className="model-selector-dropdown">
                <div className="model-cards-container">
                  {modelsWithInfo.map(({ path, info, displayName }, index) => {
                    const isSelected = modelConfig.modelPath === path;
                    return (
                      <div
                        key={index}
                        className={`model-card ${isSelected ? 'selected' : ''} ${info.hasVision ? 'has-vision' : ''}`}
                        onClick={() => handleModelSelect(path)}
                      >
                        {/* <div className="model-card-icon">{info.icon}</div> */}
                        <div className="model-card-info">
                          <div className="model-card-name">{displayName}</div>
                          <div className="model-card-meta">
                            {info.size && <span className="model-meta-size">{info.size}</span>}
                            {info.quantization && <span className="model-meta-quantization">{info.quantization}</span>}
                            {info.type && <span className="model-meta-type">{info.type}</span>}
                            {info.hasVision && <span className="model-meta-vision">{strings.vision}</span>}
                            {info.fileSize && info.fileSize > 0 && (
                              <span className="model-meta-weight">{(info.fileSize / (1024*1024*1024)).toFixed(2)} {strings.gb}</span>
                            )}
                          </div>
                        </div>
                        {isSelected && <div className="selected-indicator">✓</div>}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
          {/* Mostrar el modelo seleccionado */}
          {modelConfig.modelPath && (
            <div className="selected-model-info">
              ✅ {strings.selectedModel} <strong>{formatModelName(modelConfig.modelPath)}</strong>
            </div>
          )}
          <div className="model-info">
            📊 {strings.modelsAvailable(modelsList.length)}
          </div>
        </div>
        
        <div className="form-group">
          <label htmlFor="temperature">{strings.temperature}</label>
          <input
            type="number"
            className="form-control param-temperature"
            id="temperature"
            name="temperature"
            step="0.01"
            min="0"
            max="1"
            placeholder={strings.temperaturePlaceholder}
            value={modelConfig.temperature || 0.8}
            onChange={handleChange}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="context">{strings.context}</label>
          <input
            type="number"
            className="form-control param-context"
            id="context"
            name="context"
            placeholder={strings.contextPlaceholder}
            value={modelConfig.context || 8192}
            onChange={handleChange}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="systemMessage">{strings.systemMessage}</label>
          <textarea
            className="form-control param-system-message"
            id="systemMessage"
            name="systemMessage"
            rows="3"
            placeholder={strings.systemMessagePlaceholder}
            value={textareaValue}
            onChange={handleSystemMessageChange}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="gpuLayers">
            {strings.gpuLayers} <span className="slider-value">{modelConfig.gpuLayers || -1}</span>
          </label>
          <input
            type="range"
            className="form-control slider param-gpu-layers"
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
            className={`btn btn-primary apply-btn ${isApplying ? 'loading' : ''}`}
            disabled={isApplying}
          >
            <span style={{opacity: isApplying ? 0 : 1}}>
              {isApplying ? strings.applying : strings.apply}
            </span>
          </button>
          <button 
            type="button" 
            className="btn btn-secondary" 
            onClick={unloadModel}
            disabled={isApplying}
          >
            {strings.unload}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ConfigSidebar;
