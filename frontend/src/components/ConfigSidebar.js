import React, { useState, useEffect } from 'react';
import './ConfigSidebar.css';

function ConfigSidebar({ applyConfig, unloadModel, modelsList = [], formatList = [], isOpen }) {
  const [selectedModel, setSelectedModel] = useState('');
  const [selectedFormat, setSelectedFormat] = useState('');
  const [temperature, setTemperature] = useState(0.7);
  const [context, setContext] = useState(2048);
  const [systemMessage, setSystemMessage] = useState('Eres un asistente en español. Debes responder siempre en español');
  const [gpuLayers, setGpuLayers] = useState(0);

  // Establecer el primer modelo y formato como valores predeterminados cuando se cargan
  useEffect(() => {
    if (modelsList.length > 0 && !selectedModel) {
      setSelectedModel(modelsList[0]);
      console.log('Modelo seleccionado por defecto:', modelsList[0]);
    }
    
    if (formatList.length > 0 && !selectedFormat) {
      setSelectedFormat(formatList[0]);
      console.log('Formato seleccionado por defecto:', formatList[0]);
    }
  }, [modelsList, formatList, selectedModel, selectedFormat]);

  const handleApplyConfig = () => {
    const config = {
      model_path: selectedModel,
      format: selectedFormat,
      temperature: parseFloat(temperature),
      system_message: systemMessage,
      gpu_layers: parseInt(gpuLayers),
      context: parseInt(context)
    };
    
    console.log('Aplicando configuración:', config);
    applyConfig(config);
  };

  const handleUnloadModel = () => {
    console.log('Descargando modelo');
    unloadModel();
  };

  return (
    <div id="config-sidebar" className={isOpen ? 'open' : ''}>
      <h5>Configuración del modelo</h5>
      
      <div className="form-group">
        <label htmlFor="model-select">Modelo:</label>
        <select 
          className="form-control" 
          id="model-select" 
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
        >
          {modelsList.map((model, index) => (
            <option key={index} value={model}>{model}</option>
          ))}
        </select>
      </div>
      
      <div className="form-group">
        <label htmlFor="format-select">Formato:</label>
        <select 
          className="form-control" 
          id="format-select" 
          value={selectedFormat}
          onChange={(e) => setSelectedFormat(e.target.value)}
        >
          {formatList.map((format, index) => (
            <option key={index} value={format}>{format}</option>
          ))}
        </select>
      </div>
      
      <div className="form-group">
        <label htmlFor="temperature-input">
          Temperatura: {temperature}
        </label>
        <input 
          type="range" 
          className="form-control-range" 
          id="temperature-input" 
          min="0" 
          max="1" 
          step="0.01" 
          value={temperature}
          onChange={(e) => setTemperature(e.target.value)}
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="context-input">
          Tokens de contexto: {context}
        </label>
        <input 
          type="range" 
          className="form-control-range" 
          id="context-input" 
          min="512" 
          max="8192" 
          step="512" 
          value={context}
          onChange={(e) => setContext(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label htmlFor="gpu-layers-input">
          Capas GPU: {gpuLayers}
        </label>
        <input 
          type="range" 
          className="form-control-range" 
          id="gpu-layers-input" 
          min="0" 
          max="100" 
          value={gpuLayers}
          onChange={(e) => setGpuLayers(e.target.value)}
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="system-message-input">Mensaje del sistema:</label>
        <textarea 
          className="form-control" 
          id="system-message-input" 
          rows="3" 
          value={systemMessage}
          onChange={(e) => setSystemMessage(e.target.value)}
        ></textarea>
      </div>
      
      <div className="config-buttons">
        <button className="btn btn-primary" onClick={handleApplyConfig}>
          Aplicar configuración
        </button>
        <button className="btn btn-danger" onClick={handleUnloadModel}>
          Descargar modelo
        </button>
      </div>
    </div>
  );
}

export default ConfigSidebar;
