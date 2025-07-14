import { useState, useEffect, useRef, useCallback, useContext, useMemo } from 'react';
import { useSocket } from '../context/SocketContext';
import { useLanguage } from '../context/LanguageContext';

export function useDevConsole() {
    const [isVisible, setIsVisible] = useState(false);
    const [messages, setMessages] = useState([]);
    const [selectedRoles, setSelectedRoles] = useState(new Set(['all']));
    const [showFilters, setShowFilters] = useState(false);
    const [dimensions, setDimensions] = useState({ width: 800, height: 400 });
    const [position, setPosition] = useState({ x: null, y: 50 });
    const [isResizing, setIsResizing] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const [resizeDirection, setResizeDirection] = useState(null);
    const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
    const [showdown, setShowdown] = useState(null);
    const [isPiPMode, setIsPiPMode] = useState(false);
    const messagesEndRef = useRef(null);
    const consoleRef = useRef(null);
    const socket = useSocket();
    const { getStrings, currentLang } = useLanguage();
    const strings = getStrings('devconsole');
    const lang = currentLang;
    const normalizeRole = (role) => (role || '').toLowerCase().replace(/\s+/g, '');
    const getUniqueRoles = useCallback(() => {
        const roles = new Set();
        messages.forEach(msg => { if (msg.role) { roles.add(normalizeRole(msg.role)); } });
        return Array.from(roles).sort();
    }, [messages]);
    useEffect(() => {
        const handleKeyPress = (event) => {
            if (event.shiftKey && event.key === 'T') {
                event.preventDefault();
                setIsVisible(prev => !prev);
            }
            if (event.key === 'Escape' && isVisible) {
                setIsVisible(false);
            }
        };
        document.addEventListener('keydown', handleKeyPress);
        return () => { document.removeEventListener('keydown', handleKeyPress); };
    }, [isVisible]);
    const [autoScroll, setAutoScroll] = useState(true);
    useEffect(() => {
        if (!isVisible) return;
        const el = consoleRef.current?.querySelector('.console-messages');
        if (!el) return;
        const handleScroll = () => {
            const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
            setAutoScroll(atBottom);
        };
        el.addEventListener('scroll', handleScroll);
        return () => el.removeEventListener('scroll', handleScroll);
    }, [isVisible]);
    const prevMessagesCount = useRef(messages.length);
    useEffect(() => {
        // Eliminado: autoscroll en el hook
        // if (isVisible && autoScroll && messages.length > prevMessagesCount.current) {
        //     messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        // }
        prevMessagesCount.current = messages.length;
    }, [messages, isVisible, autoScroll]);
    useEffect(() => {
        if (!socket) return;
        const handleConsoleOutput = (data) => {
            const normRole = normalizeRole(data.role || 'info');
            // Solo agregar si el rol está seleccionado
            if (selectedRoles.has('all') || selectedRoles.has(normRole)) {
                const newMessage = {
                    id: Date.now() + Math.random(),
                    timestamp: new Date(),
                    content: data.content || '',
                    role: normRole
                };
                setMessages(prev => {
                    const updatedMessages = [...prev, newMessage];
                    if (updatedMessages.length > 2000) {
                        return updatedMessages.slice(-2000);
                    }
                    return updatedMessages;
                });
            }
        };
        const handleAssistantResponse = (data) => {
            const normRole = 'assistant';
            if ((selectedRoles.has('all') || selectedRoles.has(normRole)) && data.content && !data.finished) {
                const newMessage = {
                    id: Date.now() + Math.random(),
                    timestamp: new Date(),
                    content: `Assistant: ${data.content.substring(0, 100)}${data.content.length > 100 ? '...' : ''}`,
                    role: normRole
                };
                setMessages(prev => [...prev, newMessage]);
            }
        };
        const handleUtilities = (data) => {
            const normRole = 'tool';
            if (selectedRoles.has('all') || selectedRoles.has(normRole)) {
                const newMessage = {
                    id: Date.now() + Math.random(),
                    timestamp: new Date(),
                    content: `Utilidades: ${JSON.stringify(data)}`,
                    role: normRole
                };
                setMessages(prev => [...prev, newMessage]);
            }
        };
        socket.on('output_console', handleConsoleOutput);
        socket.on('assistant_response', handleAssistantResponse);
        socket.on('utilidades', handleUtilities);
        return () => {
            socket.off('output_console', handleConsoleOutput);
            socket.off('assistant_response', handleAssistantResponse);
            socket.off('utilidades', handleUtilities);
        };
    }, [socket, isPiPMode, selectedRoles]); // Added selectedRoles dependency
    const clearConsole = () => {
        setMessages([]);
        localStorage.removeItem('devConsole_messages');
    };
    useEffect(() => {
        if (messages.length > 0) {
            const messagesToSave = messages.slice(-100);
            localStorage.setItem('devConsole_messages', JSON.stringify(messagesToSave));
        }
    }, [messages]);
    useEffect(() => {
        try {
            const savedMessages = localStorage.getItem('devConsole_messages');
            if (savedMessages) {
                const parsedMessages = JSON.parse(savedMessages);
                setMessages(parsedMessages.map(msg => ({ ...msg, timestamp: new Date(msg.timestamp) })));
            }
        } catch (error) {
            console.error('Error cargando mensajes de consola:', error);
        }
    }, []);
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
    const filteredMessages = messages.filter(msg => {
        const normRole = normalizeRole(msg.role);
        if (selectedRoles.size === 0) return false;
        if (selectedRoles.has('all')) return true;
        return selectedRoles.has(normRole);
    });
    const uniqueRoles = getUniqueRoles();
    const formatTime = (timestamp) => {
        return timestamp.toLocaleTimeString(lang === 'es' ? 'es-ES' : 'en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            fractionalSecondDigits: 3
        });
    };
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
            }
            return newSelection;
        });
    };
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
            const maxWidth = window.innerWidth;
            const maxHeight = window.innerHeight;
            newWidth = Math.min(newWidth, maxWidth);
            newHeight = Math.min(newHeight, maxHeight);
            setDimensions({ width: newWidth, height: newHeight });
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
    const handleHeaderMouseDown = (e) => {
        if (e.target.closest('.console-controls')) return;
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
            const minX = -dimensions.width + 100;
            const maxX = window.innerWidth - 100;
            const minY = 0;
            const maxY = window.innerHeight - 50;
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
    const centerConsole = () => { setPosition({ x: null, y: 50 }); };
    const handleHeaderDoubleClick = () => { centerConsole(); };
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
    useEffect(() => { localStorage.setItem('devConsole_dimensions', JSON.stringify(dimensions)); }, [dimensions]);
    useEffect(() => {
        try {
            const savedDimensions = localStorage.getItem('devConsole_dimensions');
            if (savedDimensions) {
                const parsedDimensions = JSON.parse(savedDimensions);
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
    useEffect(() => { localStorage.setItem('devConsole_position', JSON.stringify(position)); }, [position]);
    useEffect(() => {
        try {
            const savedPosition = localStorage.getItem('devConsole_position');
            if (savedPosition) {
                const parsedPosition = JSON.parse(savedPosition);
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
    useEffect(() => { localStorage.setItem('devConsole_selectedRoles', JSON.stringify(Array.from(selectedRoles))); }, [selectedRoles]);
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
    // Memoizar el objeto de retorno para evitar renders innecesarios
    return useMemo(() => ({
        isVisible, setIsVisible, messages, setMessages, selectedRoles, setSelectedRoles, showFilters, setShowFilters,
        dimensions, setDimensions, position, setPosition, isResizing, setIsResizing, isDragging, setIsDragging,
        resizeDirection, setResizeDirection, dragOffset, setDragOffset, showdown, setShowdown, isPiPMode, setIsPiPMode,
        messagesEndRef, consoleRef, socket, getStrings, currentLang, strings, lang,
        normalizeRole, getUniqueRoles, autoScroll, setAutoScroll, prevMessagesCount,
        clearConsole, exportConsole, filteredMessages, uniqueRoles, formatTime,
        handleRoleToggle, handleMouseDown, handleHeaderMouseDown, centerConsole, handleHeaderDoubleClick, getCursorStyle
    }), [
        isVisible, messages, selectedRoles, showFilters, dimensions, position, isResizing, isDragging,
        resizeDirection, dragOffset, showdown, isPiPMode, socket, getStrings, currentLang, strings, lang,
        autoScroll, prevMessagesCount, filteredMessages, uniqueRoles
    ]);
}