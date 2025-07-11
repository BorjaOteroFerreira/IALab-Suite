import React, { useState, useEffect } from 'react';
import './ErrorMessage.css';
import { useLanguage } from '../../context/LanguageContext';

/**
 * Componente para mostrar errores de una manera amigable
 */
const ErrorMessage = ({ 
  error, 
  onRetry = null,
  onDismiss = null,
  timeout = 0  //  no se ocultará automáticamente
}) => {
  const { getStrings } = useLanguage();
  const strings = getStrings('error');
  
  const [visible, setVisible] = useState(true);
  
  // Determinar el tipo de error para mostrar la UI adecuada
  const getErrorType = () => {
    const errorMessage = error?.message || error?.toString() || '';
    
    if (errorMessage.includes('network') || errorMessage.includes('conexión') || 
        errorMessage.includes('connection') || errorMessage.includes('ECONNREFUSED')) {
      return 'network';
    }
    
    if (errorMessage.includes('timeout') || errorMessage.includes('tiempo')) {
      return 'timeout';
    }
    
    if (errorMessage.includes('model') || errorMessage.includes('modelo')) {
      return 'model';
    }
    
    return 'unknown';
  };
  
  const errorType = getErrorType();
  
  // Ocultar automáticamente 
  useEffect(() => {
    let timer;
    if (timeout > 0) {
      timer = setTimeout(() => {
        setVisible(false);
        onDismiss && onDismiss();
      }, timeout);
    }
    
    return () => {
      timer && clearTimeout(timer);
    };
  }, [timeout, onDismiss]);
  
  // Manejar el cierre del mensaje
  const handleClose = () => {
    setVisible(false);
    onDismiss && onDismiss();
  };
  
  // Si no es visible, no renderizar nada
  if (!visible) {
    return null;
  }
  
  // Renderizar diferentes UIs según el tipo de error
  return (
    <div className={`error-message error-${errorType}`}>
      <div className="error-icon">
        {errorType === 'network' ? '🌐❌' : 
         errorType === 'timeout' ? '⏱️❌' : 
         errorType === 'model' ? '🤖❌' : '⚠️'}
      </div>
      
      <div className="error-content">
        <h3>
          {errorType === 'network' ? strings.error.networkTitle :
           errorType === 'timeout' ? strings.error.timeoutTitle :
           errorType === 'model' ? strings.error.modelTitle : strings.general.error}
        </h3>
        
        <p>{error?.message || error?.toString() || strings.error.unknown}</p>
        
        {/* Sugerencias específicas para cada tipo de error */}
        {errorType === 'network' && (
          <ul className="error-tips">
            <li>{strings.error.networkTip1}</li>
            <li>{strings.error.networkTip2}</li>
            <li>{strings.error.networkTip3}</li>
          </ul>
        )}
        
        {errorType === 'timeout' && (
          <ul className="error-tips">
            <li>{strings.error.timeoutTip1}</li>
            <li>{strings.error.timeoutTip2}</li>
            <li>{strings.error.timeoutTip3}</li>
          </ul>
        )}
        
        {errorType === 'model' && (
          <ul className="error-tips">
            <li>{strings.error.modelTip1}</li>
            <li>{strings.error.modelTip2}</li>
            <li>{strings.error.modelTip3}</li>
          </ul>
        )}
      </div>
      
      <div className="error-actions">
        {onRetry && (
          <button className="retry-btn" onClick={onRetry}>
            {strings.error.retry}
          </button>
        )}
        <button className="close-btn" onClick={handleClose}>
          {strings.error.close}
        </button>
      </div>
    </div>
  );
};

export default ErrorMessage;
