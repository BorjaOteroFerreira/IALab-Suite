import React, { useRef, useEffect, useState } from 'react';
import './InputArea.css';
import { Send, Square, Database, Image as ImageIcon, Paperclip, Globe, ChevronUp, Download } from 'lucide-react';
import ToolsSelector from '../../UI/ToolsSelector/ToolsSelector';
import { useChatContext } from '../../../hooks/useChatContext';
import { useLanguage } from '../../../context/LanguageContext';

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

function LanguageDropdown({ lang, setLang }) {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef(null);
  const { availableLangs } = useLanguage();

  // Genera las opciones dinámicamente según los idiomas detectados
  const options = availableLangs.map(code => ({ value: code, label: code.toUpperCase() }));

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  return (
    <div className="custom-lang-dropdown" ref={dropdownRef}>
      <button
        className="lang-dropdown-btn"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <Globe size={15} style={{ marginRight: 6, opacity: 0.7 }} />
        <span>{options.find(o => o.value === lang)?.label}</span>
        <ChevronUp size={14} style={{ marginLeft: 2, transition: 'transform 0.2s', transform: open ? 'rotate(180deg)' : 'none' }} />
      </button>
      {open && (
        <ul className="lang-dropdown-list" role="listbox">
          {options.map(opt => (
            <li
              key={opt.value}
              className={`lang-dropdown-item${lang === opt.value ? ' selected' : ''}`}
              onClick={() => { setLang(opt.value); setOpen(false); }}
              role="option"
              aria-selected={lang === opt.value}
            >
              {opt.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function InputArea({ 
  input, 
  setInput, 
  onSubmit, 
  isLoading, 
  tokensCount, 
  currentResponse, 
  onStopResponse, 
  tools, rag, onToggleTools, onToggleRag, onOpenDownloader 
}) {
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const { socket, modelConfig, modelList, formatList } = useChatContext();
  const { lang, setLang, getStrings } = useLanguage();
  const strings = getStrings('inputArea');
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
          {strings.contextUsed}: {tokensCount} {strings.tokens}
        </span>
        <div className="input-container">
          {/* Botón RAG */}
          <button
            type="button"
            onClick={() => onToggleRag(!rag)}
            className={`input-icon-button${!!rag ? ' active' : ''}`}
            title={strings.ragTooltip || strings.rag}
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
              title={strings.attachFileTooltip || strings.attachFile}
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
                  title={strings.uploadImageTooltip || strings.uploadImage}
                  onClick={handleImageButtonClick}
                  style={{ position: 'absolute', left: 38, top: '50%', transform: 'translateY(-50%)', zIndex: 2 }}
                  tabIndex={-1}
                >
                  <ImageIcon size={22} />
                </button>
                <input
                  type="file"
                  accept="image/*"
                  ref={fileInputRef}
                  style={{ display: 'none' }}
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
              placeholder={strings.placeholder}
              className="message-textarea"
              disabled={isLoading}
              rows={1}
              style={hasVision ? { paddingLeft: 85, paddingRight: 40 } : { paddingLeft: 53, paddingRight: 40 }}
            />
            {/* Indicador de imagen lista */}
            {imagePreview && (
              <div className="image-ready-indicator" style={{ position: 'absolute', left: 70, top: '50%', transform: 'translateY(-50%)', zIndex: 3, display: 'flex', alignItems: 'center', background: '#f5f5f5', borderRadius: 6, padding: '2px 6px', boxShadow: '0 1px 4px #0001' }}>
                <img src={imagePreview} alt="preview" style={{ width: 28, height: 28, objectFit: 'cover', borderRadius: 4, marginRight: 6 }} />
                <span style={{ fontSize: 13, color: '#333', marginRight: 4 }}>{strings.imageReady}</span>
                <button type="button" onClick={handleRemoveImage} style={{ background: 'none', border: 'none', color: '#c00', fontWeight: 'bold', cursor: 'pointer', fontSize: 16, lineHeight: 1, padding: 0 }} title={strings.removeImage}>{strings.removeImage}</button>
              </div>
            )}
            {/* Botón de enviar superpuesto a la derecha */}
            {isLoading && currentResponse ? (
              <button
                type="button"
                onClick={onStopResponse}
                className="send-button stop"
                title={strings.stopResponse}
                style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', zIndex: 2 }}
              >
                <Square size={20} />
              </button>
            ) : (
              <button
                type="submit"
                disabled={isLoading || (!(typeof input === 'string' && input.trim().length > 0) && !imageBase64)}
                className="send-button"
                title={strings.sendMessage}
                style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', zIndex: 2 }}
              >
                ➤
              </button>
            )}
          </div>
        </div>
      </form>
      {/* Selector de idioma flotante custom en la esquina inferior izquierda */}
      <div className="floating-language-selector compact" style={{ zIndex: 3001 }}>
        <LanguageDropdown lang={lang} setLang={setLang} />
      </div>
      {/* Leyenda de shortcuts flotante: mover más a la derecha */}
      <style>{`.shortcuts-legend-floating { left: 4.5rem !important; }`}</style>
      {/* Botón flotante para abrir el Downloader en la esquina inferior derecha */}
      <button
        className="header-button floating-downloader-btn"
        title={strings.downloadModelsTooltip || strings.downloadModels || 'Download GGUF models'}
        onClick={onOpenDownloader}
        style={{ position: 'fixed', right: '1.5rem', bottom: 16, zIndex: 2000 }}
      >
        <Download size={22} />
      </button>
    </div>
    
  );
}

export default InputArea;