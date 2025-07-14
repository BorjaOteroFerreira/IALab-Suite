import React, { useState, useEffect, useRef, memo, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useDevConsole } from '../../hooks/useDevConsole';
import './DevConsole.css';
import { Filter, Download, Trash2, X, ExternalLink } from 'lucide-react';

const DevConsole = () => {
    const [pipWindow, setPipWindow] = useState(null);
    const pipButtonRef = useRef(null);
    
    const {
        isVisible, setIsVisible, messagesEndRef, consoleRef,
        showFilters, setShowFilters, dimensions, position, isResizing, isDragging,
        resizeDirection, showdown, filteredMessages, uniqueRoles, selectedRoles,
        handleRoleToggle, handleMouseDown, handleHeaderMouseDown, handleHeaderDoubleClick,
        exportConsole, clearConsole, formatTime, normalizeRole, strings, lang,
        isPiPMode, setIsPiPMode
    } = useDevConsole();

    // Verificar soporte para Document Picture-in-Picture
    const supportsPiP = 'documentPictureInPicture' in window;

    const copyCSSToWindow = (targetWindow) => {
        const allStyles = document.querySelectorAll('style, link[rel="stylesheet"]');
        
        allStyles.forEach(styleElement => {
            if (styleElement.tagName === 'STYLE') {
                // Copiar estilos inline
                const newStyle = targetWindow.document.createElement('style');
                newStyle.textContent = styleElement.textContent;
                targetWindow.document.head.appendChild(newStyle);
            } else if (styleElement.tagName === 'LINK' && styleElement.href) {
                // Copiar links CSS
                const newLink = targetWindow.document.createElement('link');
                newLink.rel = 'stylesheet';
                newLink.type = 'text/css';
                newLink.href = styleElement.href;
                targetWindow.document.head.appendChild(newLink);
            }
        });

        // También copiar CSS computado como fallback
        const computedStyles = `
            .dev-console {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
                overflow: hidden;
                color: #fff;
                font-size: 12px;
                line-height: 1.4;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            
            .pip-mode {
                width: 100% !important;
                height: 100% !important;
                border: none !important;
                border-radius: 0 !important;
                position: static !important;
                transform: none !important;
            }
            
            .console-header {
                background: #2d2d2d;
                padding: 8px 12px;
                border-bottom: 1px solid #333;
                display: flex;
                justify-content: space-between;
                align-items: center;
                user-select: none;
            }
            
            .console-title {
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
                color: #fff;
            }
            
            .console-controls {
                display: flex;
                gap: 4px;
            }
            
            .console-controls button {
                background: none;
                border: 1px solid #555;
                color: #ccc;
                padding: 4px 6px;
                border-radius: 4px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
            }
            
            .console-controls button:hover {
                background: #3a3a3a;
                border-color: #666;
                color: #fff;
            }
            
            .console-body {
                flex: 1;
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }
            
            .console-messages {
                flex: 1;
                overflow-y: auto;
                padding: 8px;
                pointer-events: auto;
                overscroll-behavior: contain;
                position: relative;
                z-index: 1;
            }
            
            .console-message {
                margin-bottom: 4px;
                display: flex;
                gap: 8px;
                word-wrap: break-word;
                align-items: flex-start;
                pointer-events: auto;
            }
            
            .message-timestamp {
                color: #888;
                font-size: 10px;
                white-space: nowrap;
                margin-top: 1px;
            }
            
            .message-role {
                color: #4a9eff;
                font-weight: 600;
                font-size: 10px;
                white-space: nowrap;
                margin-top: 1px;
            }
            
            .message-content {
                flex: 1;
                color: #fff;
            }
            
            .console-footer {
                background: #2d2d2d;
                padding: 6px 12px;
                border-top: 1px solid #333;
                font-size: 10px;
                color: #888;
            }
            
            .console-shortcuts {
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
            }
            
            .pip-badge {
                background: #4a9eff;
                color: white;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 600;
            }
            
            .console-filters {
                background: #2a2a2a;
                border-bottom: 1px solid #333;
                padding: 8px 12px;
            }
            
            .filter-title {
                color: #ccc;
                font-size: 11px;
                margin-bottom: 6px;
            }
            
            .filter-checkboxes {
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
            }
            
            .filter-checkbox {
                display: flex;
                align-items: center;
                gap: 4px;
                color: #ccc;
                font-size: 11px;
                cursor: pointer;
            }
            
            .filter-checkbox input[type="checkbox"] {
                margin: 0;
                width: 12px;
                height: 12px;
            }
            
            body {
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #1a1a1a;
                color: #fff;
                overflow: hidden;
            }
            
            #pip-console-container {
                width: 100vw;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }
        `;
        
        const fallbackStyle = targetWindow.document.createElement('style');
        fallbackStyle.textContent = computedStyles;
        targetWindow.document.head.appendChild(fallbackStyle);
    };

    const openPictureInPicture = async () => {
        if (!supportsPiP) {
            alert(lang === 'es' ? 'Tu navegador no soporta Picture-in-Picture' : 'Your browser does not support Picture-in-Picture');
            return;
        }

        try {
            const pipWin = await window.documentPictureInPicture.requestWindow({
                width: dimensions.width,
                height: dimensions.height,
                disallowReturnToOpener: false,
            });

            // Configurar el documento PiP
            pipWin.document.title = lang === 'es' ? 'Consola de Desarrollo' : 'Dev Console';
            
            // Copiar estilos CSS
            copyCSSToWindow(pipWin);

            // Crear contenedor en PiP
            const pipContainer = pipWin.document.createElement('div');
            pipContainer.id = 'pip-console-container';
            pipWin.document.body.appendChild(pipContainer);

            // Configurar event listeners
            const handlePipClose = () => {
                setPipWindow(null);
                setIsPiPMode(false);
            };

            pipWin.addEventListener('beforeunload', handlePipClose);
            pipWin.addEventListener('pagehide', handlePipClose);

            // Enfocar la ventana PiP
            pipWin.focus();

            setPipWindow(pipWin);
            setIsPiPMode(true);
        } catch (error) {
            console.error('Error opening Picture-in-Picture:', error);
            alert(lang === 'es' ? 'Error al abrir Picture-in-Picture' : 'Error opening Picture-in-Picture');
        }
    };

    const closePictureInPicture = () => {
        if (pipWindow && !pipWindow.closed) {
            pipWindow.close();
        }
        setPipWindow(null);
        setIsPiPMode(false);
    };

    // Cleanup al desmontar
    useEffect(() => {
        return () => {
            if (pipWindow && !pipWindow.closed) {
                pipWindow.close();
            }
        };
    }, [pipWindow]);

    // Efecto para sincronizar el estado del hook con la ventana PiP
    useEffect(() => {
        if (isPiPMode && (!pipWindow || pipWindow.closed)) {
            // Si el hook dice que está en PiP pero no hay ventana, resetear
            setIsPiPMode(false);
        }
    }, [isPiPMode, pipWindow, setIsPiPMode]);

    // Manejar cierre de la consola
    const handleCloseConsole = () => {
        if (isPiPMode) {
            closePictureInPicture();
        } else {
            setIsVisible(false);
        }
    };

    const consoleStyle = useMemo(() => ({
        width: isPiPMode ? '100%' : `${dimensions.width}px`,
        height: isPiPMode ? '100%' : `${dimensions.height}px`,
        maxWidth: isPiPMode ? '100%' : `${window.innerWidth - 100}px`,
        maxHeight: isPiPMode ? '100%' : `${window.innerHeight - 100}px`,
        ...(isPiPMode ? {} : (position.x !== null ? {
            left: `${position.x}px`,
            top: `${position.y}px`,
            transform: 'none'
        } : {
            left: '50%',
            top: `${position.y}px`,
            transform: 'translateX(-50%)'
        }))
    }), [isPiPMode, dimensions.width, dimensions.height, position.x, position.y]);

    const renderMarkdown = (text) => {
        if (!showdown) return <span>{lang === 'es' ? 'Cargando...' : 'Loading...'}</span>;
        if (typeof text === 'string' && text.trim().startsWith('{') && text.trim().endsWith('}')) {
            return <span>{text}</span>;
        }
        const html = showdown.makeHtml(text || '');
        return <span className="console-md-fragment" dangerouslySetInnerHTML={{ __html: html }} />;
    };

    const ConsoleMessages = memo(({ filteredMessages, normalizeRole, formatTime, strings, lang, renderMarkdown, messagesEndRef, isPipMode }) => (
        <div className="console-messages" style={{ pointerEvents: 'auto', overscrollBehavior: 'contain', position: 'relative', zIndex: 1 }}>
            {filteredMessages.map(message => (
                <div key={message.id} className={`console-message console-${normalizeRole(message.role)}`} style={{ pointerEvents: 'auto' }}>
                    <span className="message-timestamp">[{formatTime(message.timestamp)}]</span>
                    <span className="message-role">
                        [{(strings[normalizeRole(message.role)] || normalizeRole(message.role)).toUpperCase()}]
                    </span>
                    <span className="message-content">{renderMarkdown(message.content)}</span>
                </div>
            ))}
            <div ref={isPipMode ? undefined : messagesEndRef} />
        </div>
    ));

    const ConsoleFooter = memo(({ lang, strings, isPipMode, filteredMessages }) => (
        <div className="console-footer">
            <div className="console-shortcuts">
                <span>Shift+T: {lang === 'es' ? 'Mostrar/Ocultar' : 'Toggle'}</span>
                <span>ESC: {strings.close}</span>
                {!isPipMode && (
                    <>
                        <span>{lang === 'es' ? 'Arrastrar: Mover' : 'Drag: Move'}</span>
                        <span>{lang === 'es' ? 'Doble clic: Centrar' : 'Double click: Center'}</span>
                    </>
                )}
                <span>{lang === 'es' ? 'Mensajes' : 'Messages'}: {filteredMessages.length}</span>
            </div>
        </div>
    ));

    const ConsoleContent = ({ isPipMode = false }) => {
        return (
            <div 
                className={`dev-console ${isResizing ? 'resizing' : ''} ${isDragging ? 'dragging' : ''} ${isPipMode ? 'pip-mode' : ''}`} 
                ref={isPipMode ? undefined : consoleRef} 
                style={consoleStyle}
            >
                {/* Resize handles - solo en modo normal */}
                {!isPipMode && (
                    <>
                        <div className="resize-handle resize-right" onMouseDown={(e) => handleMouseDown(e, 'right')} />
                        <div className="resize-handle resize-bottom" onMouseDown={(e) => handleMouseDown(e, 'bottom')} />
                        <div className="resize-handle resize-bottom-right" onMouseDown={(e) => handleMouseDown(e, 'bottom-right')} />
                        <div className="resize-handle resize-left" onMouseDown={(e) => handleMouseDown(e, 'left')} />
                        <div className="resize-handle resize-top" onMouseDown={(e) => handleMouseDown(e, 'top')} />
                        <div className="resize-handle resize-top-left" onMouseDown={(e) => handleMouseDown(e, 'top-left')} />
                        <div className="resize-handle resize-top-right" onMouseDown={(e) => handleMouseDown(e, 'top-right')} />
                        <div className="resize-handle resize-bottom-left" onMouseDown={(e) => handleMouseDown(e, 'bottom-left')} />
                    </>
                )}
                
                <div 
                    className="console-header" 
                    onMouseDown={!isPipMode ? handleHeaderMouseDown : undefined} 
                    onDoubleClick={!isPipMode ? handleHeaderDoubleClick : undefined}
                    title={!isPipMode ? (lang === 'es' ? 'Arrastra para mover | Doble clic para centrar' : 'Drag to move | Double click to center') : ''}
                >
                    <div className="console-title">
                        <span className="console-icon">⚡</span>
                        {!isPipMode && <span className="drag-indicator">≡</span>}
                        {lang === 'es' ? 'Consola de Desarrollo' : 'Dev Console'}
                        <span className="message-count">({filteredMessages.length})</span>
                        {isPipMode && <span className="pip-badge">PiP</span>}
                    </div>
                    
                    <div className="console-controls">
                        <button className="console-filter-btn" onClick={() => setShowFilters(!showFilters)} title={strings.filter}>
                            <Filter size={16} />
                        </button>
                        
                        <button onClick={exportConsole} className="console-export" title={strings.download}>
                            <Download size={16} />
                        </button>
                        
                        <button onClick={clearConsole} className="console-clear" title={strings.clear}>
                            <Trash2 size={16} />
                        </button>
                        
                        {/* Botón PiP */}
                        {supportsPiP && !isPipMode && (
                            <button 
                                ref={pipButtonRef}
                                onClick={openPictureInPicture} 
                                className="console-pip" 
                                title={lang === 'es' ? 'Abrir en Picture-in-Picture' : 'Open in Picture-in-Picture'}
                            >
                                <ExternalLink size={16} />
                            </button>
                        )}
                        
                        <button 
                            onClick={handleCloseConsole} 
                            className="console-close" 
                            title={strings.close + ' (ESC)'}
                        >
                            <X size={16} />
                        </button>
                    </div>
                </div>
                
                {/* Panel de filtros */}
                {showFilters && (
                    <div className="console-filters">
                        <div className="filter-title">{strings.filter} {lang === 'es' ? 'por roles:' : 'by roles:'}</div>
                        <div className="filter-checkboxes">
                            <label className="filter-checkbox">
                                <input type="checkbox" checked={selectedRoles.has('all')} onChange={() => handleRoleToggle('all')} />
                                <span className="checkmark"></span>
                                {strings.all} ({filteredMessages.length})
                            </label>
                            {uniqueRoles.map(role => {
                                const count = filteredMessages.filter(m => normalizeRole(m.role) === role).length;
                                return (
                                    <label key={role} className="filter-checkbox">
                                        <input type="checkbox" value={role} checked={selectedRoles.has(role)} onChange={() => handleRoleToggle(role)} />
                                        <span className="checkmark"></span>
                                        {strings[role] || role.charAt(0).toUpperCase() + role.slice(1)} ({count})
                                    </label>
                                );
                            })}
                        </div>
                    </div>
                )}
                
                <div className="console-body" style={{ overflow: 'auto', flex: 1 }}>
                    <ConsoleMessages
                        filteredMessages={filteredMessages}
                        normalizeRole={normalizeRole}
                        formatTime={formatTime}
                        strings={strings}
                        lang={lang}
                        renderMarkdown={renderMarkdown}
                        messagesEndRef={messagesEndRef}
                        isPipMode={isPipMode}
                    />
                </div>
                <ConsoleFooter
                    lang={lang}
                    strings={strings}
                    isPipMode={isPipMode}
                    filteredMessages={filteredMessages}
                />
            </div>
        );
    };

    // Autoscroll solo si el mensaje está en los filtrados y no se está redimensionando
    const prevFilteredCount = useRef(filteredMessages.length);
    useEffect(() => {
        if (!isResizing && messagesEndRef?.current && filteredMessages.length > prevFilteredCount.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
        prevFilteredCount.current = filteredMessages.length;
    }, [filteredMessages, messagesEndRef, isResizing]);

    // Renderizar en PiP window si está disponible
    if (isPiPMode && pipWindow && !pipWindow.closed) {
        const pipContainer = pipWindow.document.getElementById('pip-console-container');
        if (pipContainer) {
            return createPortal(<ConsoleContent isPipMode={true} />, pipContainer);
        }
    }

    // Renderizar normal solo si es visible y no está en modo PiP
    if (isVisible && !isPiPMode) {
        return <ConsoleContent isPipMode={false} />;
    }

    return null;
};

export default DevConsole;