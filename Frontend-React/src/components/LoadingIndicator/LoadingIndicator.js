import React from 'react';

/*
 * Componente de indicador de carga avanzado que muestra diferentes estados
 * basados en el tipo de operación que se está realizando
 */
const LoadingIndicator = ({ type = 'default', message = '' }) => {
  
  // Diferentes estilos de animación según el tipo de operación
  const renderIndicator = () => {
    switch(type) {
      case 'modelLoad':
        // Indicador para carga de modelo 
        return (
          <div className="model-loading-indicator">
            <div className="spinner-ring"></div>
            <div className="loading-text">
              {message || 'Cargando modelo...'}
            </div>
          </div>
        );
        
      case 'thinking':
        // Indicador para cuando el modelo está "pensando"
        return (
          <div className="thinking-indicator">
            <div className="dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div className="loading-text">
              {message || 'Procesando...'}
            </div>
          </div>
        );
        
      case 'saving':
        // Indicador para operaciones de guardado
        return (
          <div className="saving-indicator">
            <div className="progress-bar">
              <div className="progress-fill"></div>
            </div>
            <div className="loading-text">
              {message || 'Guardando...'}
            </div>
          </div>
        );
      
      default:
        // Indicador de carga predeterminado
        return (
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
            {message && <div className="loading-message">{message}</div>}
          </div>
        );
    }
  };
  
  return (
    <div className="message assistant">
      <div className="message-content assistant">
        {renderIndicator()}
      </div>
    </div>
  );
};

export default LoadingIndicator;
