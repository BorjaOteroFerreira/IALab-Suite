import React, { useState, useEffect, useRef, useCallback, useContext } from 'react';
import { ChatContext } from '../../context/ChatContext';
import { useLanguage } from '../../context/LanguageContext';
import './DevConsole.css';
import { Filter, Download, Trash2, X } from 'lucide-react';

// Importar showdown dinámicamente como en MessageList

const DevConsole = () => {
    const [isVisible, setIsVisible] = useState(false);
    const [messages, setMessages] = useState([]);
    const [selectedRoles, setSelectedRoles] = useState(new Set(['all'])); // Set para múltiples roles
    const [showFilters, setShowFilters] = useState(false); // Para mostrar/ocultar panel de filtros
    const [dimensions, setDimensions] = useState({
        width: 800,
        height: 400
    });
    const [position, setPosition] = useState({
        x: null, // null significa centrado
        y: 50
    });
    const [isResizing, setIsResizing] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const [resizeDirection, setResizeDirection] = useState(null);
    const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
    const [showdown, setShowdown] = useState(null);
    const messagesEndRef = useRef(null);
    const consoleRef = useRef(null);
    const { socket } = useContext(ChatContext);
    const { getStrings, currentLang } = useLanguage();
    const strings = getStrings('devconsole');
    const lang = currentLang;

    // Configuración de colores por rol
    const roleColors = {
        info: '#5ecbfa',      // Azul pastel
        pensamiento: '#ff9500', // Naranja
        tool: '#00ff41',      // Verde
        assistant: '#ffffff',  // Blanco
        error: '#ff3333',     // Rojo
        warning: '#ffff00',   // Amarillo
        success: '#00ff00',   // Verde brillante
        debug: '#888888'      // Gris
    };

    // Normalizar roles para consistencia en filtros y visualización
    const normalizeRole = (role) => (role || '').toLowerCase().replace(/\s+/g, '');

    // Obtener lista de roles únicos de los mensajes (normalizados)
    const getUniqueRoles = useCallback(() => {
        const roles = new Set();
        messages.forEach(msg => {
            if (msg.role) {
                roles.add(normalizeRole(msg.role));
            }
        });
        return Array.from(roles).sort();
    }, [messages]);

    // Manejar tecla Shift+T
    useEffect(() => {
        const handleKeyPress = (event) => {
            if (event.shiftKey && event.key === 'T') {
                event.preventDefault();
                setIsVisible(prev => !prev);
            }
            
            // ESC para cerrar
            if (event.key === 'Escape' && isVisible) {
                setIsVisible(false);
            }
        };

        document.addEventListener('keydown', handleKeyPress);
        return () => {
            document.removeEventListener('keydown', handleKeyPress);
        };
    }, [isVisible]);

    // Scroll automático al final SOLO si la consola está visible y el usuario no está haciendo scroll manual
    const [autoScroll, setAutoScroll] = useState(true);

    // Detectar si el usuario hace scroll manual en la consola
    useEffect(() => {
        if (!isVisible) return;
        const el = consoleRef.current?.querySelector('.console-messages');
        if (!el) return;
        const handleScroll = () => {
            // Si el usuario está cerca del fondo, activar autoscroll
            const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
            setAutoScroll(atBottom);
        };
        el.addEventListener('scroll', handleScroll);
        return () => el.removeEventListener('scroll', handleScroll);
    }, [isVisible]);



    // Guardar el número de mensajes previos para detectar si hay mensajes nuevos
    const prevMessagesCount = useRef(messages.length);

    useEffect(() => {
        // Solo hacer scroll si hay mensajes nuevos en la consola
        if (isVisible && autoScroll && messages.length > prevMessagesCount.current) {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
        prevMessagesCount.current = messages.length;
    }, [messages, isVisible, autoScroll]);

    // Escuchar mensajes del socket
    useEffect(() => {
        if (!socket) return;

        const handleConsoleOutput = (data) => {
            const newMessage = {
                id: Date.now() + Math.random(),
                timestamp: new Date(),
                content: data.content || '',
                role: normalizeRole(data.role || 'info')
            };
            setMessages(prev => {
                // Limitar el número de mensajes para evitar problemas de memoria
                const updatedMessages = [...prev, newMessage];
                if (updatedMessages.length > 2000) {
                    return updatedMessages.slice(-2000);
                }
                return updatedMessages;
            });
        };

        const handleAssistantResponse = (data) => {
            if (data.content && !data.finished) {
                const newMessage = {
                    id: Date.now() + Math.random(),
                    timestamp: new Date(),
                    content: `Assistant: ${data.content.substring(0, 100)}${data.content.length > 100 ? '...' : ''}`,
                    role: 'assistant'
                };
                // Normalizar role
                newMessage.role = normalizeRole(newMessage.role);
                setMessages(prev => [...prev, newMessage]);
            }
        };

        const handleUtilities = (data) => {
            const newMessage = {
                id: Date.now() + Math.random(),
                timestamp: new Date(),
                content: `Utilidades: ${JSON.stringify(data)}`,
                role: 'tool'
            };
            newMessage.role = normalizeRole(newMessage.role);
            setMessages(prev => [...prev, newMessage]);
        };

        socket.on('output_console', handleConsoleOutput);
        socket.on('assistant_response', handleAssistantResponse);
        socket.on('utilidades', handleUtilities);

        return () => {
            socket.off('output_console', handleConsoleOutput);
            socket.off('assistant_response', handleAssistantResponse);
            socket.off('utilidades', handleUtilities);
        };
    }, [socket]);

    // Limpiar consola
    const clearConsole = () => {
        setMessages([]);
        localStorage.removeItem('devConsole_messages');
    };

    // Guardar mensajes en localStorage
    useEffect(() => {
        if (messages.length > 0) {
            const messagesToSave = messages.slice(-100); // Solo guardar los últimos 100
            localStorage.setItem('devConsole_messages', JSON.stringify(messagesToSave));
        }
    }, [messages]);

    // Cargar mensajes del localStorage al inicializar
    useEffect(() => {
        try {
            const savedMessages = localStorage.getItem('devConsole_messages');
            if (savedMessages) {
                const parsedMessages = JSON.parse(savedMessages);
                setMessages(parsedMessages.map(msg => ({
                    ...msg,
                    timestamp: new Date(msg.timestamp)
                })));
            }
        } catch (error) {
            console.error('Error cargando mensajes de consola:', error);
        }
    }, []);

    // Exportar mensajes
    const exportConsole = () => {
        const dataStr = JSON.stringify(messages, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `console_log_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    // Filtrar mensajes según roles seleccionados (usando roles normalizados)
    const filteredMessages = messages.filter(msg => {
        const normRole = normalizeRole(msg.role);
        if (selectedRoles.size === 0) return false; // Si no hay roles seleccionados, no mostrar nada
        if (selectedRoles.has('all')) return true;
        return selectedRoles.has(normRole);
    });

    // Obtener roles únicos para el filtro (ya normalizados)
    const uniqueRoles = getUniqueRoles();

    // Formatear timestamp
    const formatTime = (timestamp) => {
        return timestamp.toLocaleTimeString(lang === 'es' ? 'es-ES' : 'en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            fractionalSecondDigits: 3
        });
    };

    // Funciones para manejo de filtros
    const handleRoleToggle = (role) => {
        setSelectedRoles(prev => {
            const newSelection = new Set(prev);
            if (role === 'all') {
                if (newSelection.has('all')) {
                    newSelection.clear();
                } else {
                    newSelection.clear();
                    newSelection.add('all');
                }
            } else {
                if (newSelection.has('all')) {
                    newSelection.delete('all');
                }
                if (newSelection.has(role)) {
                    newSelection.delete(role);
                } else {
                    newSelection.add(role);
                }
                // Ya no seleccionamos 'all' automáticamente si queda vacío
            }
            return newSelection;
        });
    };

    // Funciones de redimensionamiento
    const handleMouseDown = (e, direction) => {
        e.preventDefault();
        e.stopPropagation();
        
        setIsResizing(true);
        setResizeDirection(direction);
        
        const startX = e.clientX;
        const startY = e.clientY;
        const startWidth = dimensions.width;
        const startHeight = dimensions.height;
        
        const handleMouseMove = (e) => {
            let newWidth = startWidth;
            let newHeight = startHeight;
            
            if (direction.includes('right')) {
                newWidth = Math.max(300, startWidth + (e.clientX - startX));
            }
            if (direction.includes('left')) {
                newWidth = Math.max(300, startWidth - (e.clientX - startX));
            }
            if (direction.includes('bottom')) {
                newHeight = Math.max(200, startHeight + (e.clientY - startY));
            }
            if (direction.includes('top')) {
                newHeight = Math.max(200, startHeight - (e.clientY - startY));
            }
            
            // Limitar el tamaño máximo al viewport menos márgenes
            const maxWidth = window.innerWidth;
            const maxHeight = window.innerHeight;
            
            newWidth = Math.min(newWidth, maxWidth);
            newHeight = Math.min(newHeight, maxHeight);
            
            setDimensions({
                width: newWidth,
                height: newHeight
            });
        };
        
        const handleMouseUp = () => {
            setIsResizing(false);
            setResizeDirection(null);
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
        
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    };

    // Funciones de arrastre
    const handleHeaderMouseDown = (e) => {
        if (e.target.closest('.console-controls')) {
            // No arrastrar si se hace clic en los controles
            return;
        }
        
        e.preventDefault();
        e.stopPropagation();
        
        setIsDragging(true);
        
        const rect = consoleRef.current.getBoundingClientRect();
        const offsetX = e.clientX - rect.left;
        const offsetY = e.clientY - rect.top;
        
        setDragOffset({ x: offsetX, y: offsetY });
        
        const handleMouseMove = (e) => {
            let newX = e.clientX - offsetX;
            let newY = e.clientY - offsetY;
            
            // Limitar la posición para que la ventana no se salga completamente de la pantalla
            const minX = -dimensions.width + 100; // Dejar al menos 100px visibles
            const maxX = window.innerWidth - 100;
            const minY = 0;
            const maxY = window.innerHeight - 50; // Dejar al menos el header visible
            
            newX = Math.max(minX, Math.min(maxX, newX));
            newY = Math.max(minY, Math.min(maxY, newY));
            
            setPosition({ x: newX, y: newY });
        };
        
        const handleMouseUp = () => {
            setIsDragging(false);
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
        
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    };

    // Función para centrar la consola
    const centerConsole = () => {
        setPosition({
            x: null, // null significa centrado horizontalmente
            y: 50
        });
    };

    // Manejar doble clic en el header para centrar
    const handleHeaderDoubleClick = () => {
        centerConsole();
    };

    // Inicializar showdown
    useEffect(() => {
        let mounted = true;
        (async () => {
            const sd = await import('showdown');
            if (mounted) {
                setShowdown(new sd.Converter({
                    tables: true,
                    simplifiedAutoLink: true,
                    openLinksInNewWindow: true,
                    strikethrough: true,
                    emoji: true,
                    tasklists: true,
                    ghCodeBlocks: true,
                    noHeaderId: true,
                    excludeTrailingPunctuationFromURLs: true,
                    parseImgDimensions: true,
                    headerLevelStart: 1
                }));
            }
        })();
        return () => { mounted = false; };
    }, []);

    // Guardar dimensiones en localStorage
    useEffect(() => {
        localStorage.setItem('devConsole_dimensions', JSON.stringify(dimensions));
    }, [dimensions]);

    // Cargar dimensiones del localStorage
    useEffect(() => {
        try {
            const savedDimensions = localStorage.getItem('devConsole_dimensions');
            if (savedDimensions) {
                const parsedDimensions = JSON.parse(savedDimensions);
                // Verificar que las dimensiones sean válidas para el viewport actual
                const maxWidth = window.innerWidth - 100;
                const maxHeight = window.innerHeight - 100;
                
                setDimensions({
                    width: Math.min(Math.max(parsedDimensions.width, 300), maxWidth),
                    height: Math.min(Math.max(parsedDimensions.height, 200), maxHeight)
                });
            }
        } catch (error) {
            console.error('Error cargando dimensiones de consola:', error);
        }
    }, []);

    // Guardar posición en localStorage
    useEffect(() => {
        localStorage.setItem('devConsole_position', JSON.stringify(position));
    }, [position]);

    // Cargar posición del localStorage
    useEffect(() => {
        try {
            const savedPosition = localStorage.getItem('devConsole_position');
            if (savedPosition) {
                const parsedPosition = JSON.parse(savedPosition);
                // Verificar que la posición sea válida para el viewport actual
                if (parsedPosition.x !== null) {
                    const maxX = window.innerWidth - 100;
                    const maxY = window.innerHeight - 50;
                    
                    setPosition({
                        x: Math.max(-dimensions.width + 100, Math.min(maxX, parsedPosition.x)),
                        y: Math.max(0, Math.min(maxY, parsedPosition.y))
                    });
                }
            }
        } catch (error) {
            console.error('Error cargando posición de consola:', error);
        }
    }, [dimensions.width]);

    // Aplicar cursor durante el redimensionamiento y arrastre
    useEffect(() => {
        if (isResizing) {
            document.body.style.cursor = getCursorStyle(resizeDirection);
            document.body.style.userSelect = 'none';
        } else if (isDragging) {
            document.body.style.cursor = 'grabbing';
            document.body.style.userSelect = 'none';
        } else {
            document.body.style.cursor = 'default';
            document.body.style.userSelect = 'auto';
        }
        
        return () => {
            document.body.style.cursor = 'default';
            document.body.style.userSelect = 'auto';
        };
    }, [isResizing, isDragging, resizeDirection]);

    // Guardar roles seleccionados en localStorage
    useEffect(() => {
        localStorage.setItem('devConsole_selectedRoles', JSON.stringify(Array.from(selectedRoles)));
    }, [selectedRoles]);

    // Cargar roles seleccionados del localStorage
    useEffect(() => {
        try {
            const savedRoles = localStorage.getItem('devConsole_selectedRoles');
            if (savedRoles) {
                const roles = JSON.parse(savedRoles);
                setSelectedRoles(new Set(roles));
            }
        } catch (error) {
            console.error('Error cargando roles seleccionados de consola:', error);
        }
    }, []);

    // Función para obtener el estilo del cursor
    const getCursorStyle = (direction) => {
        switch (direction) {
            case 'right':
            case 'left':
                return 'ew-resize';
            case 'bottom':
            case 'top':
                return 'ns-resize';
            case 'bottom-right':
            case 'top-left':
                return 'nw-resize';
            case 'bottom-left':
            case 'top-right':
                return 'ne-resize';
            default:
                return 'default';
        }
    };

    if (!isVisible) return null;

    const consoleStyle = {
        width: `${dimensions.width}px`,
        height: `${dimensions.height}px`,
        maxWidth: `${window.innerWidth - 100}px`,
        maxHeight: `${window.innerHeight - 100}px`,
        ...(position.x !== null ? {
            left: `${position.x}px`,
            top: `${position.y}px`,
            transform: 'none'
        } : {
            left: '50%',
            top: `${position.y}px`,
            transform: 'translateX(-50%)'
        })
    };

    // Renderizar el contenido del mensaje como Markdown interpretado
    const renderMarkdown = (text) => {
        if (!showdown) return <span>{lang === 'es' ? 'Cargando...' : 'Loading...'}</span>;
        // Si el texto es JSON.stringify, no lo proceses como markdown
        if (typeof text === 'string' && text.trim().startsWith('{') && text.trim().endsWith('}')) {
            return <span>{text}</span>;
        }
        const html = showdown.makeHtml(text || '');
        return <span className="console-md-fragment" dangerouslySetInnerHTML={{ __html: html }} />;
    };

    return (
        <div 
            className={`dev-console ${isResizing ? 'resizing' : ''} ${isDragging ? 'dragging' : ''}`} 
            ref={consoleRef} 
            style={consoleStyle}
        >
            {/* Resize handles */}
            <div 
                className="resize-handle resize-right"
                onMouseDown={(e) => handleMouseDown(e, 'right')}
            />
            <div 
                className="resize-handle resize-bottom"
                onMouseDown={(e) => handleMouseDown(e, 'bottom')}
            />
            <div 
                className="resize-handle resize-bottom-right"
                onMouseDown={(e) => handleMouseDown(e, 'bottom-right')}
            />
            <div 
                className="resize-handle resize-left"
                onMouseDown={(e) => handleMouseDown(e, 'left')}
            />
            <div 
                className="resize-handle resize-top"
                onMouseDown={(e) => handleMouseDown(e, 'top')}
            />
            <div 
                className="resize-handle resize-top-left"
                onMouseDown={(e) => handleMouseDown(e, 'top-left')}
            />
            <div 
                className="resize-handle resize-top-right"
                onMouseDown={(e) => handleMouseDown(e, 'top-right')}
            />
            <div 
                className="resize-handle resize-bottom-left"
                onMouseDown={(e) => handleMouseDown(e, 'bottom-left')}
            />
            
            <div 
                className="console-header" 
                onMouseDown={handleHeaderMouseDown} 
                onDoubleClick={handleHeaderDoubleClick}
                title={lang === 'es' ? 'Arrastra para mover | Doble clic para centrar' : 'Drag to move | Double click to center'}
            >
                <div className="console-title">
                    <span className="console-icon">⚡</span>
                    <span className="drag-indicator">≡</span>
                    {lang === 'es' ? 'Consola de Desarrollo' : 'Dev Console'}
                    <span className="message-count">({filteredMessages.length})</span>
                </div>
                
                <div className="console-controls">
                    <button
                        className="console-filter-btn"
                        onClick={() => setShowFilters(!showFilters)}
                        title={strings.filter}
                    >
                        <Filter size={16} />
                    </button>
                    
                    <button 
                        onClick={exportConsole}
                        className="console-export"
                        title={strings.download}
                    >
                        <Download size={16} />
                    </button>
                    
                    <button 
                        onClick={clearConsole}
                        className="console-clear"
                        title={strings.clear}
                    >
                        <Trash2 size={16} />
                    </button>
                    
                    <button 
                        onClick={() => setIsVisible(false)}
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
                            <input
                                type="checkbox"
                                checked={selectedRoles.has('all')}
                                onChange={() => handleRoleToggle('all')}
                            />
                            <span className="checkmark"></span>
                            {strings.all} ({messages.length})
                        </label>
                        {uniqueRoles.map(role => {
                            const count = messages.filter(m => normalizeRole(m.role) === role).length;
                            return (
                                <label key={role} className="filter-checkbox">
                                    <input
                                        type="checkbox"
                                        value={role}
                                        checked={selectedRoles.has(role)}
                                        onChange={() => handleRoleToggle(role)}
                                    />
                                    <span 
                                        className="checkmark"
                                        style={{ backgroundColor: roleColors[role] || '#ffffff' }}
                                    ></span>
                                    {strings[role] || role.charAt(0).toUpperCase() + role.slice(1)} ({count})
                                </label>
                            );
                        })}
                    </div>
                </div>
            )}
            
            <div className="console-body">
                <div className="console-messages">
                    {filteredMessages.map(message => (
                        <div 
                            key={message.id} 
                            className={`console-message console-${normalizeRole(message.role)}`}
                        >
                            <span className="message-timestamp">
                                [{formatTime(message.timestamp)}]
                            </span>
                            <span 
                                className="message-role"
                                style={{ color: roleColors[normalizeRole(message.role)] || '#ffffff' }}
                            >
                                [{(strings[normalizeRole(message.role)] || normalizeRole(message.role)).toUpperCase()}]
                            </span>
                            <span className="message-content">
                                {renderMarkdown(message.content)}
                            </span>
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>
            </div>
            
            <div className="console-footer">
                <div className="console-shortcuts">
                    <span>Shift+T: {lang === 'es' ? 'Mostrar/Ocultar' : 'Toggle'}</span>
                    <span>ESC: {strings.close}</span>
                    <span>{lang === 'es' ? 'Arrastrar: Mover' : 'Drag: Move'}</span>
                    <span>{lang === 'es' ? 'Doble clic: Centrar' : 'Double click: Center'}</span>
                    <span>{lang === 'es' ? 'Mensajes' : 'Messages'}: {messages.length}</span>
                </div>
            </div>
        </div>
    );
};

export default DevConsole;
