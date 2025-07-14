import React, { useState, useEffect, useRef, memo, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useDevConsole } from '../../hooks/useDevConsole';
import './DevConsole.css';
import { Filter, Download, Trash2, X, ExternalLink } from 'lucide-react';

const DevConsole = () => {
    const [pipWindow, setPipWindow] = useState(null);
    const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
    const messagesContainerRef = useRef(null);
    const pipButtonRef = useRef(null);

    const {
        isVisible, setIsVisible, messagesEndRef, consoleRef,
        showFilters, setShowFilters, dimensions, position, isResizing, isDragging,
        resizeDirection, showdown, filteredMessages, uniqueRoles, selectedRoles,
        handleRoleToggle, handleMouseDown, handleHeaderMouseDown, handleHeaderDoubleClick,
        exportConsole, clearConsole, formatTime, normalizeRole, strings, lang,
        isPiPMode, setIsPiPMode
    } = useDevConsole();

    const supportsPiP = 'documentPictureInPicture' in window;

    const isScrollNearBottom = (el, threshold = 100) => {
        if (!el) return true;
        const { scrollTop, scrollHeight, clientHeight } = el;
        return Math.abs(scrollHeight - scrollTop - clientHeight) <= threshold;
    };

    const handleScroll = (e) => {
        const el = e.target;
        const nearBottom = isScrollNearBottom(el);
        setShouldAutoScroll(nearBottom);
    };

    const scrollToBottom = () => {
        const container = messagesContainerRef.current;
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    };

    // Efecto para scroll automático cuando llegan nuevos mensajes
    useEffect(() => {
        if (shouldAutoScroll && filteredMessages.length > 0) {
            // Usar setTimeout para asegurar que el DOM se actualice primero
            setTimeout(() => {
                scrollToBottom();
            }, 0);
        }
    }, [filteredMessages, shouldAutoScroll]);

    // Resetear autoscroll cuando se abre la consola
    useEffect(() => {
        if (isVisible) {
            setShouldAutoScroll(true);
            setTimeout(() => {
                scrollToBottom();
            }, 0);
        }
    }, [isVisible]);


    const copyCSSToWindow = (targetWindow) => {
        const allStyles = document.querySelectorAll('style, link[rel="stylesheet"]');
        allStyles.forEach(styleEl => {
            if (styleEl.tagName === 'STYLE') {
                const newStyle = targetWindow.document.createElement('style');
                newStyle.textContent = styleEl.textContent;
                targetWindow.document.head.appendChild(newStyle);
            } else if (styleEl.tagName === 'LINK' && styleEl.href) {
                const newLink = targetWindow.document.createElement('link');
                newLink.rel = 'stylesheet';
                newLink.type = 'text/css';
                newLink.href = styleEl.href;
                targetWindow.document.head.appendChild(newLink);
            }
        });
        const computedStyles = `
            .dev-console { font-family: -apple-system,... }
            /* resto del CSS copiado según tu original */
        `;
        const fallback = targetWindow.document.createElement('style');
        fallback.textContent = computedStyles;
        targetWindow.document.head.appendChild(fallback);
    };

    const openPictureInPicture = async () => {
        if (!supportsPiP) return alert(lang === 'es' ? 'Tu navegador no soporta Picture-in-Picture' : 'Your browser does not support Picture-in-Picture');
        try {
            const pipWin = await window.documentPictureInPicture.requestWindow({ width: dimensions.width, height: dimensions.height, disallowReturnToOpener: false });
            pipWin.document.title = lang === 'es' ? 'Consola de Desarrollo' : 'Dev Console';
            copyCSSToWindow(pipWin);
            const container = pipWin.document.createElement('div');
            container.id = 'pip-console-container';
            pipWin.document.body.appendChild(container);
            const handlePipClose = () => { setPipWindow(null); setIsPiPMode(false); };
            pipWin.addEventListener('beforeunload', handlePipClose);
            pipWin.addEventListener('pagehide', handlePipClose);
            setPipWindow(pipWin);
            setIsPiPMode(true);
        } catch (error) {
            console.error('Error opening PiP:', error);
            alert(lang === 'es' ? 'Error al abrir Picture-in-Picture' : 'Error opening Picture-in-Picture');
        }
    };

    const closePictureInPicture = () => {
        if (pipWindow && !pipWindow.closed) pipWindow.close();
        setPipWindow(null);
        setIsPiPMode(false);
    };

    useEffect(() => {
        return () => {
            if (pipWindow && !pipWindow.closed) pipWindow.close();
            clearTimeout(messagesContainerRef.current?._scrollTimeout);
        };
    }, [pipWindow]);

    useEffect(() => {
        if (isPiPMode && (!pipWindow || pipWindow.closed)) {
            setIsPiPMode(false);
        }
    }, [isPiPMode, pipWindow, setIsPiPMode]);

    const handleCloseConsole = () => {
        if (isPiPMode) closePictureInPicture();
        else setIsVisible(false);
    };

    const consoleStyle = useMemo(() => ({
        width: isPiPMode ? '100%' : `${dimensions.width}px`,
        height: isPiPMode ? '100%' : `${dimensions.height}px`,
        maxWidth: isPiPMode ? '100%' : `${window.innerWidth - 100}px`,
        maxHeight: isPiPMode ? '100%' : `${window.innerHeight - 100}px`,
        ...(isPiPMode ? {} : (position.x !== null ? { left: `${position.x}px`, top: `${position.y}px`, transform: 'none' } : { left: '50%', top: `${position.y}px`, transform: 'translateX(-50%)' }))
    }), [isPiPMode, dimensions.width, dimensions.height, position.x, position.y]);

    const renderMarkdown = (text) => {
        if (!showdown) return <span>{lang === 'es' ? 'Cargando...' : 'Loading...'}</span>;
        if (typeof text === 'string' && text.trim().startsWith('{') && text.trim().endsWith('}')) return <span>{text}</span>;
        const html = showdown.makeHtml(text || '');
        return <span className="console-md-fragment" dangerouslySetInnerHTML={{ __html: html }} />;
    };

    const ConsoleMessages = memo(({ filteredMessages, normalizeRole, formatTime, strings, lang, renderMarkdown, messagesEndRef, isPipMode }) => (
        <div 
            ref={messagesContainerRef} 
            className="console-messages" 
            onScroll={handleScroll} 
            style={{ overscrollBehavior: 'contain' }}
        >
            {filteredMessages.map(message => (
                <div key={message.id} className={`console-message console-${normalizeRole(message.role)}`}>
                    <span className="message-timestamp">[{formatTime(message.timestamp)}]</span>
                    <span className="message-role">[{(strings[normalizeRole(message.role)]||normalizeRole(message.role)).toUpperCase()}]</span>
                    <span className="message-content">{renderMarkdown(message.content)}</span>
                </div>
            ))}
            <div ref={messagesEndRef} />
        </div>
    ));

    const ConsoleFooter = memo(({ lang, strings, isPipMode, filteredMessages }) => (
        <div className="console-footer">
            <div className="console-shortcuts">
                <span>Shift+T: {lang === 'es' ? 'Mostrar/Ocultar' : 'Toggle'}</span>
                <span>ESC: {strings.close}</span>
                {!isPipMode && (
                    <><span>{lang === 'es' ? 'Arrastrar: Mover' : 'Drag: Move'}</span><span>{lang === 'es' ? 'Doble clic: Centrar' : 'Double click: Center'}</span></>
                )}
                <span>{lang === 'es' ? 'Mensajes' : 'Messages'}: {filteredMessages.length}</span>
            </div>
        </div>
    ));

    const ConsoleContent = ({ isPipMode = false }) => (
        <div className={`dev-console ${isResizing?'resizing':''} ${isDragging?'dragging':''} ${isPipMode?'pip-mode':''}`} ref={isPipMode?undefined:consoleRef} style={consoleStyle}>
            {!isPipMode && (
                <>
                    <div className="resize-handle resize-right" onMouseDown={(e)=>handleMouseDown(e,'right')} />
                    <div className="resize-handle resize-bottom" onMouseDown={(e)=>handleMouseDown(e,'bottom')} />
                    <div className="resize-handle resize-bottom-right" onMouseDown={(e)=>handleMouseDown(e,'bottom-right')} />
                    <div className="resize-handle resize-left" onMouseDown={(e)=>handleMouseDown(e,'left')} />
                    <div className="resize-handle resize-top" onMouseDown={(e)=>handleMouseDown(e,'top')} />
                    <div className="resize-handle resize-top-left" onMouseDown={(e)=>handleMouseDown(e,'top-left')} />
                    <div className="resize-handle resize-top-right" onMouseDown={(e)=>handleMouseDown(e,'top-right')} />
                    <div className="resize-handle resize-bottom-left" onMouseDown={(e)=>handleMouseDown(e,'bottom-left')} />
                </>
            )}
            <div className="console-header" onMouseDown={!isPipMode?handleHeaderMouseDown:undefined} onDoubleClick={!isPipMode?handleHeaderDoubleClick:undefined} title={!isPipMode?(lang==='es'?'Arrastra para mover | Doble clic para centrar':'Drag to move | Double click to center'):''}>
                <div className="console-title">
                    <span className="console-icon">⚡</span>
                    {!isPipMode && <span className="drag-indicator">≡</span>}
                    {lang === 'es' ? 'Consola de Desarrollo' : 'Dev Console'}
                    <span className="message-count">({filteredMessages.length})</span>
                    {isPipMode && <span className="pip-badge">PiP</span>}
                </div>
                <div className="console-controls">
                    <button className="console-filter-btn" onClick={()=>setShowFilters(!showFilters)} title={strings.filter}><Filter size={16} /></button>
                    <button onClick={exportConsole} className="console-export" title={strings.download}><Download size={16} /></button>
                    <button onClick={clearConsole} className="console-clear" title={strings.clear}><Trash2 size={16} /></button>
                    {supportsPiP && !isPipMode && <button ref={pipButtonRef} onClick={openPictureInPicture} className="console-pip" title={lang==='es'?'Abrir en PiP':'Open in PiP'}><ExternalLink size={16} /></button>}
                    <button onClick={handleCloseConsole} className="console-close" title={strings.close+' (ESC)'}><X size={16} /></button>
                </div>
            </div>
            {showFilters && (
                <div className="console-filters">
                    <div className="filter-title">{strings.filter} {lang==='es'?'por roles':'by roles'}:</div>
                    <div className="filter-checkboxes">
                        <label className="filter-checkbox">
                            <input type="checkbox" checked={selectedRoles.has('all')} onChange={()=>handleRoleToggle('all')} />
                            <span className="checkmark"></span>
                            {strings.all} ({filteredMessages.length})
                        </label>
                        {uniqueRoles.map(role => {
                            const count = filteredMessages.filter(m=>normalizeRole(m.role)===role).length;
                            return <label key={role} className="filter-checkbox"><input type="checkbox" checked={selectedRoles.has(role)} onChange={()=>handleRoleToggle(role)} /><span className="checkmark" />{strings[role]||role.charAt(0).toUpperCase()+role.slice(1)} ({count})</label>;
                        })}
                    </div>
                </div>
            )}
            <div className="console-body" style={{ overflow:'auto', flex:1 }}>
                <ConsoleMessages filteredMessages={filteredMessages} normalizeRole={normalizeRole} formatTime={formatTime} strings={strings} lang={lang} renderMarkdown={renderMarkdown} messagesEndRef={messagesEndRef} isPipMode={isPiPMode} />
            </div>
            <ConsoleFooter lang={lang} strings={strings} isPipMode={isPiPMode} filteredMessages={filteredMessages} />
        </div>
    );



    if (isPiPMode && pipWindow && !pipWindow.closed) {
        const pipContainer = pipWindow.document.getElementById('pip-console-container');
        if (pipContainer) return createPortal(<ConsoleContent isPipMode={true} />, pipContainer);
    }
    if (isVisible && !isPiPMode) return <ConsoleContent isPipMode={false} />;
    return null;
};

export default DevConsole;

