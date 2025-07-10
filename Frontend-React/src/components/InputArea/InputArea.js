import React, { useRef, useEffect, useState } from 'react';
import './InputArea.css';
import { Send, Square, Database, Image as ImageIcon, Paperclip } from 'lucide-react';
import ToolsSelector from '../ToolsSelector/ToolsSelector';
import { useChatContext } from '../../hooks/useChatContext';

function getModelInfo(modelObjOrPath, allModelsList = []) {
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
}

function InputArea({ 
  input, 
  setInput, 
  onSubmit, 
  isLoading, 
  tokensCount, 
  currentResponse, 
  onStopResponse, 
  tools, rag, onToggleTools, onToggleRag 
}) {
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const { socket, modelConfig, modelList, formatList } = useChatContext();
  // Estado para imagen base64 y preview
  const [imageBase64, setImageBase64] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  // Auto-resize del textarea
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [input]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isLoading) return;
    // Validar correctamente si hay texto o imagen
    const hasText = typeof input === 'string' ? input.trim().length > 0 : false;
    if (hasText || imageBase64) {
      if (imageBase64) {
        onSubmit({ text: typeof input === 'string' ? input : '', image_base64: imageBase64 });
        setImageBase64(null);
        setImagePreview(null);
      } else {
        onSubmit(input);
      }
      setInput('');
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
        }
      }, 100);
    }
  };

  // --- Integración visión ---
  const currentModel = modelList && modelList.find(m => (typeof m === 'object' ? m.path : m) === modelConfig.modelPath);
  const hasVision = getModelInfo(currentModel, modelList)?.hasVision;

  const handleImageButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        setImageBase64(ev.target.result.split(',')[1]);
        setImagePreview(ev.target.result);
      };
      reader.readAsDataURL(file);
      // Opcional: limpiar el input para permitir volver a subir la misma imagen
      e.target.value = '';
    }
  };

  const handleRemoveImage = () => {
    setImageBase64(null);
    setImagePreview(null);
  };

  return (
    <div className="input-area">
      <form onSubmit={handleSubmit} className="message-form">
        <span className="tokens-counter">
          Contexto usado: {tokensCount} Tokens
        </span>
        <div className="input-container">
          {/* Botón RAG */}
          <button
            type="button"
            onClick={() => onToggleRag(!rag)}
            className={`input-icon-button${!!rag ? ' active' : ''}`}
            title="RAG"
            style={{ marginRight: 6 }}
          >
            <Database size={23} />
          </button>
          {/* Botón de herramientas */}
          <div className="input-side-buttons" style={{ marginRight: 6 }}>
            <ToolsSelector 
              tools={tools} 
              onToggleTools={onToggleTools}
              socket={socket}
            />
          </div>
          {/* Textarea con botones superpuestos */}
          <div className="textarea-wrapper" style={{ position: 'relative', flex: 1, display: 'flex', alignItems: 'center' }}>
            {/* Botón de clip superpuesto a la izquierda */}
            <button
              type="button"
              className="input-icon-button clip-inside-textarea"
              title="Adjuntar archivo"
              style={{ position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)', zIndex: 2 }}
              tabIndex={-1}
              // onClick={handleClipClick} // Implementa si quieres funcionalidad
            >
              <Paperclip size={20} />
            </button>
            {/* Botón de imagen superpuesto a la izquierda, después del clip */}
            {hasVision && (
              <>
                <button
                  type="button"
                  className="input-icon-button image-inside-textarea"
                  title="Subir imagen"
                  onClick={handleImageButtonClick}
                  style={{ position: 'absolute', left: 38, top: '50%', transform: 'translateY(-50%)', zIndex: 2 }}
                  tabIndex={-1}
                >
                  <ImageIcon size={22} />
                </button>
                <input
                  type="file"
                  accept="image/*"
                  style={{ display: 'none' }}
                  ref={fileInputRef}
                  onChange={handleFileChange}
                />
              </>
            )}
            {/* Textarea con padding a ambos lados */}
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  e.target.form.requestSubmit();
                }
              }}
              placeholder="Escribe tu mensaje aquí... (Enter para enviar, Shift+Enter para nueva línea)"
              className="message-textarea"
              disabled={isLoading}
              rows={1}
              style={hasVision ? { paddingLeft: 85, paddingRight: 40 } : { paddingLeft: 53, paddingRight: 40 }}
            />
            {/* Indicador de imagen lista */}
            {imagePreview && (
              <div className="image-ready-indicator" style={{ position: 'absolute', left: 70, top: '50%', transform: 'translateY(-50%)', zIndex: 3, display: 'flex', alignItems: 'center', background: '#f5f5f5', borderRadius: 6, padding: '2px 6px', boxShadow: '0 1px 4px #0001' }}>
                <img src={imagePreview} alt="preview" style={{ width: 28, height: 28, objectFit: 'cover', borderRadius: 4, marginRight: 6 }} />
                <span style={{ fontSize: 13, color: '#333', marginRight: 4 }}>Imagen lista</span>
                <button type="button" onClick={handleRemoveImage} style={{ background: 'none', border: 'none', color: '#c00', fontWeight: 'bold', cursor: 'pointer', fontSize: 16, lineHeight: 1, padding: 0 }} title="Quitar imagen">×</button>
              </div>
            )}
            {/* Botón de enviar superpuesto a la derecha */}
            {isLoading && currentResponse ? (
              <button
                type="button"
                onClick={onStopResponse}
                className="send-button stop"
                title="Detener respuesta"
                style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', zIndex: 2 }}
              >
                <Square size={20} />
              </button>
            ) : (
              <button
                type="submit"
                disabled={isLoading || (!(typeof input === 'string' && input.trim().length > 0) && !imageBase64)}
                className="send-button"
                title="Enviar mensaje"
                style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', zIndex: 2 }}
              >
                ➤
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
    
  );
}

export default InputArea;
