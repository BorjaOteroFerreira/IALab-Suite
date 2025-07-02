import React, { useState, useEffect } from 'react';
import './ErrorMessage.css';

/**
 * Componente para mostrar errores de una manera amigable
 * con opciones para reintentar o resolver problemas comunes
 */
const ErrorMessage = ({ 
  error, 
  onRetry = null,
  onDismiss = null,
  timeout = 0  // 0 significa que no se ocultará automáticamente
}) => {
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
          {errorType === 'network' ? 'Error de conexión' :
           errorType === 'timeout' ? 'Tiempo de espera agotado' :
           errorType === 'model' ? 'Error en el modelo' : 'Error'}
        </h3>
        
        <p>{error?.message || error?.toString() || 'Ocurrió un error desconocido'}</p>
        
        {/* Sugerencias específicas para cada tipo de error */}
        {errorType === 'network' && (
          <ul className="error-tips">
            <li>Verifica tu conexión a Internet</li>
            <li>Asegúrate que el servidor de Flask esté ejecutándose</li>
            <li>Comprueba si hay un firewall bloqueando la conexión</li>
          </ul>
        )}
        
        {errorType === 'timeout' && (
          <ul className="error-tips">
            <li>La operación está tomando demasiado tiempo</li>
            <li>Intenta con una solicitud más pequeña</li>
            <li>Verifica el rendimiento del servidor</li>
          </ul>
        )}
        
        {errorType === 'model' && (
          <ul className="error-tips">
            <li>Comprueba si el modelo está correctamente cargado</li>
            <li>Verifica la ruta y el formato del modelo</li>
            <li>Intenta con otro modelo o formato</li>
          </ul>
        )}
      </div>
      
      <div className="error-actions">
        {onRetry && (
          <button className="retry-btn" onClick={onRetry}>
            Reintentar
          </button>
        )}
        <button className="close-btn" onClick={handleClose}>
          Cerrar
        </button>
      </div>
    </div>
  );
};

export default ErrorMessage;
