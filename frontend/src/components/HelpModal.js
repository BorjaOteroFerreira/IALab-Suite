import React, { useEffect } from 'react';
import './HelpModal.css';

function HelpModal({ onClose }) {
  // Cerrar el modal al presionar Escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  return (
    <div className="help-modal-overlay" onClick={onClose}>
      <div className="help-modal" onClick={(e) => e.stopPropagation()}>
        <div className="help-modal-header">
          <h3>Ayuda de IALab Suite</h3>
          <button className="help-modal-close" onClick={onClose}>✕</button>
        </div>
        
        <div className="help-modal-body">
          <div className="help-section">
            <h4>Introducción</h4>
            <p>
              IALab Suite es una interfaz para interactuar con modelos de lenguaje 
              locales. Permite cargar diferentes modelos, configurar parámetros y 
              mantener conversaciones con asistentes de IA.
            </p>
          </div>
          
          <div className="help-section">
            <h4>Funciones principales</h4>
            <p>
              <strong>Chatear:</strong> Escribe mensajes en el cuadro de entrada en la parte inferior y presiona Enter o haz clic en el botón de enviar.
            </p>
            <p>
              <strong>Detener respuesta:</strong> Puedes detener la generación de una respuesta haciendo clic en el botón de detener que aparece durante la generación.
            </p>
            <p>
              <strong>Historial:</strong> Las conversaciones se guardan automáticamente y puedes acceder a ellas desde la barra lateral izquierda.
            </p>
            <p>
              <strong>Configuración:</strong> Ajusta parámetros como el modelo, formato, temperatura y más desde la barra lateral derecha.
            </p>
          </div>
          
          <div className="help-section">
            <h4>Comandos especiales</h4>
            <p>
              <strong>Herramientas (🛠️):</strong> Activa o desactiva el acceso a herramientas externas.
            </p>
            <p>
              <strong>RAG (📚):</strong> Activa o desactiva el sistema de Retrieval Augmented Generation.
            </p>
          </div>
          
          <div className="help-section">
            <h4>Atajos de teclado</h4>
            <div className="help-shortcut">
              <span><span className="keyboard-key">Enter</span></span>
              <span>Enviar mensaje</span>
            </div>
            <div className="help-shortcut">
              <span><span className="keyboard-key">Shift</span> + <span className="keyboard-key">Enter</span></span>
              <span>Nueva línea</span>
            </div>
            <div className="help-shortcut">
              <span><span className="keyboard-key">Esc</span></span>
              <span>Cerrar modal</span>
            </div>
            <div className="help-shortcut">
              <span><span className="keyboard-key">Ctrl</span> + <span className="keyboard-key">C</span></span>
              <span>Copiar texto seleccionado</span>
            </div>
          </div>
          
          <div className="help-section">
            <h4>Acerca de</h4>
            <p>
              Desarrollado por Borja Otero Ferreira. IALab Suite es un proyecto de código abierto para interactuar con modelos de lenguaje.
            </p>
            <p>
              Para más información y actualizaciones, visita el repositorio del proyecto.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HelpModal;
