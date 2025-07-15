import { useState, useEffect, useLayoutEffect, useRef, useCallback, useMemo } from 'react';
import { useSocket } from '../context/SocketContext';
import { useLanguage } from '../context/LanguageContext';

/**
 * Hook: useDevConsole
 * --------------------
 *   • Mantiene la posición de scroll del usuario.
 *   • Sólo recalcula el desplazamiento cuando CAMBIA la lista de mensajes VISIBLES.
 *   • Si el usuario está a <100 px del final, se ancla; de lo contrario conserva su punto de lectura.
 */
export function useDevConsole() {
    /* ------------------------------------------------------------------ */
    /* React state y refs                                                 */
    /* ------------------------------------------------------------------ */
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

    const consoleRef = useRef(null);
    const messagesEndRef = useRef(null);

    // Refs para conservar la posición exacta entre renders
    const prevScrollHeightRef = useRef(0);
    const prevScrollTopRef   = useRef(0);

    /* ------------------------------------------------------------------ */
    /* Contextos externos                                                 */
    /* ------------------------------------------------------------------ */
    const socket = useSocket();
    const { getStrings, currentLang } = useLanguage();
    const strings = getStrings('devconsole');
    const lang = currentLang;

    /* ------------------------------------------------------------------ */
    /* Helpers                                                            */
    /* ------------------------------------------------------------------ */
    const normalizeRole = (role) => (role || '').toLowerCase().replace(/\s+/g, '');

    const getUniqueRoles = useCallback(() => {
        const roles = new Set();
        messages.forEach((m) => m.role && roles.add(normalizeRole(m.role)));
        return [...roles].sort();
    }, [messages]);

    /* ------------------------------------------------------------------ */
    /* Filtros (antes de scroll)                                          */
    /* ------------------------------------------------------------------ */
    const filteredMessages = useMemo(() => {
        return messages.filter((msg) => {
            if (selectedRoles.has('all')) return true;
            return selectedRoles.has(normalizeRole(msg.role));
        });
    }, [messages, selectedRoles]);

    const uniqueRoles = getUniqueRoles();

    const formatTime = (ts) =>
        ts.toLocaleTimeString(lang === 'es' ? 'es-ES' : 'en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            fractionalSecondDigits: 3,
        });

    /* ------------------------------------------------------------------ */
    /* Scroll: mantener posición del usuario                              */
    /* ------------------------------------------------------------------ */
    useLayoutEffect(() => {
        const container = consoleRef.current?.querySelector('.console-messages');
        if (!container) return;

        /**
         * Sólo actuar si la altura ha cambiado (es decir, si DOM ha cambiado).
         */
        const heightDiff = container.scrollHeight - prevScrollHeightRef.current;
        if (heightDiff === 0) return; // nada cambió -> nada que hacer

        const wasAtBottom =
            prevScrollHeightRef.current - prevScrollTopRef.current <= container.clientHeight + 100;

        if (wasAtBottom) {
            container.scrollTop = container.scrollHeight - container.clientHeight;
        } else {
            container.scrollTop = prevScrollTopRef.current + heightDiff;
        }

        prevScrollHeightRef.current = container.scrollHeight;
        prevScrollTopRef.current = container.scrollTop;
    }, [filteredMessages.length]);

    // Capturar posición antes del próximo render
    useLayoutEffect(() => {
        const container = consoleRef.current?.querySelector('.console-messages');
        if (!container) return () => {};
        return () => {
            prevScrollHeightRef.current = container.scrollHeight;
            prevScrollTopRef.current = container.scrollTop;
        };
    });

    /* ------------------------------------------------------------------ */
    /* Keyboard shortcuts                                                 */
    /* ------------------------------------------------------------------ */
    useEffect(() => {
        const onKey = (e) => {
            if (e.shiftKey && e.key === 'T') {
                e.preventDefault();
                setIsVisible((v) => !v);
            }
            if (e.key === 'Escape' && isVisible) setIsVisible(false);
        };
        document.addEventListener('keydown', onKey);
        return () => document.removeEventListener('keydown', onKey);
    }, [isVisible]);

    /* ------------------------------------------------------------------ */
    /* Socket listeners                                                   */
    /* ------------------------------------------------------------------ */
    const addMessage = useCallback((msg) => {
        setMessages((prev) => {
            const next = [...prev, msg];
            return next.length > 2000 ? next.slice(-2000) : next;
        });
    }, []);

    useEffect(() => {
        if (!socket) return;

        const handleConsoleOutput = (d) => {
            addMessage({ id: Date.now() + Math.random(), timestamp: new Date(), role: normalizeRole(d.role || 'info'), content: d.content || '' });
        };

        const handleAssistantResponse = (d) => {
            const normRole = 'assistant';
            setMessages((prev) => {
                if (prev.length && prev[prev.length - 1].role === normRole && !prev[prev.length - 1].finished) {
                    const upd = [...prev];
                    upd[upd.length - 1] = { ...upd[upd.length - 1], content: `Assistant: ${d.content.slice(0, 100)}${d.content.length > 100 ? '...' : ''}`, finished: !!d.finished };
                    return upd;
                }
                if (d.content) return [...prev, { id: Date.now() + Math.random(), timestamp: new Date(), role: normRole, content: `Assistant: ${d.content.slice(0, 100)}${d.content.length > 100 ? '...' : ''}`, finished: !!d.finished }];
                return prev;
            });
        };

        const handleUtilities = (d) => addMessage({ id: Date.now() + Math.random(), timestamp: new Date(), role: 'tool', content: `Utilidades: ${JSON.stringify(d)}` });

        socket.on('output_console', handleConsoleOutput);
        socket.on('assistant_response', handleAssistantResponse);
        socket.on('utilidades', handleUtilities);
        return () => {
            socket.off('output_console', handleConsoleOutput);
            socket.off('assistant_response', handleAssistantResponse);
            socket.off('utilidades', handleUtilities);
        };
    }, [socket, addMessage]);

    /* ------------------------------------------------------------------ */
    /* Persistencia (mensajes & UI)                                       */
    /* ------------------------------------------------------------------ */
    const clearConsole = () => {
        setMessages([]);
        localStorage.removeItem('devConsole_messages');
    };

    useEffect(() => {
        if (messages.length) localStorage.setItem('devConsole_messages', JSON.stringify(messages.slice(-100)));
    }, [messages]);

    useEffect(() => {
        try {
            const saved = localStorage.getItem('devConsole_messages');
            if (saved) setMessages(JSON.parse(saved).map((m) => ({ ...m, timestamp: new Date(m.timestamp) })));
        } catch (e) {
            console.error('Error cargando mensajes de consola:', e);
        }
    }, []);

    /* ------------------------------------------------------------------ */
    /* Persistencia: mensajes, UI state                                   */
    /* ------------------------------------------------------------------ */


    useEffect(() => {
        if (messages.length)
            localStorage.setItem('devConsole_messages', JSON.stringify(messages.slice(-100)));
    }, [messages]);

    useEffect(() => {
        try {
            const saved = localStorage.getItem('devConsole_messages');
            if (saved)
                setMessages(
                    JSON.parse(saved).map((msg) => ({ ...msg, timestamp: new Date(msg.timestamp) }))
                );
        } catch (err) {
            console.error('Error cargando mensajes de consola:', err);
        }
    }, []);

    useEffect(() =>
        localStorage.setItem('devConsole_dimensions', JSON.stringify(dimensions)),
        [dimensions]
    );
    useEffect(() => localStorage.setItem('devConsole_position', JSON.stringify(position)), [position]);
    useEffect(() =>
        localStorage.setItem('devConsole_selectedRoles', JSON.stringify([...selectedRoles])),
        [selectedRoles]
    );

    /* ------------------------------------------------------------------ */
    /* Restore UI state                                                   */
    /* ------------------------------------------------------------------ */
    useEffect(() => {
        try {
            const saved = localStorage.getItem('devConsole_dimensions');
            if (saved) {
                const s = JSON.parse(saved);
                const maxW = window.innerWidth - 100;
                const maxH = window.innerHeight - 100;
                setDimensions({
                    width: Math.min(Math.max(s.width, 300), maxW),
                    height: Math.min(Math.max(s.height, 200), maxH),
                });
            }
        } catch (err) {
            console.error('Error cargando dimensiones de consola:', err);
        }
    }, []);

    useEffect(() => {
        try {
            const saved = localStorage.getItem('devConsole_position');
            if (saved) {
                const p = JSON.parse(saved);
                if (p.x !== null) {
                    const maxX = window.innerWidth - 100;
                    const maxY = window.innerHeight - 50;
                    setPosition({
                        x: Math.max(-dimensions.width + 100, Math.min(maxX, p.x)),
                        y: Math.max(0, Math.min(maxY, p.y)),
                    });
                }
            }
        } catch (err) {
            console.error('Error cargando posición de consola:', err);
        }
    }, [dimensions.width]);

    useEffect(() => {
        try {
            const saved = localStorage.getItem('devConsole_selectedRoles');
            if (saved) setSelectedRoles(new Set(JSON.parse(saved)));
        } catch (err) {
            console.error('Error cargando roles seleccionados de consola:', err);
        }
    }, []);

    /* ------------------------------------------------------------------ */
    /* Resize & Drag                                                      */
    /* ------------------------------------------------------------------ */
    const handleMouseDown = (e, direction) => {
        e.preventDefault();
        e.stopPropagation();
        setIsResizing(true);
        setResizeDirection(direction);

        const startX = e.clientX;
        const startY = e.clientY;
        const { width: startW, height: startH } = dimensions;

        const onMove = (ev) => {
            let newW = startW;
            let newH = startH;
            if (direction.includes('right')) newW = Math.max(300, startW + (ev.clientX - startX));
            if (direction.includes('left')) newW = Math.max(300, startW - (ev.clientX - startX));
            if (direction.includes('bottom')) newH = Math.max(200, startH + (ev.clientY - startY));
            if (direction.includes('top')) newH = Math.max(200, startH - (ev.clientY - startY));
            setDimensions({
                width: Math.min(newW, window.innerWidth),
                height: Math.min(newH, window.innerHeight),
            });
        };
        const onUp = () => {
            setIsResizing(false);
            setResizeDirection(null);
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
        };
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    };

    const handleHeaderMouseDown = (e) => {
        if (e.target.closest('.console-controls')) return;
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
        const rect = consoleRef.current.getBoundingClientRect();
        const offX = e.clientX - rect.left;
        const offY = e.clientY - rect.top;
        setDragOffset({ x: offX, y: offY });

        const onMove = (ev) => {
            const minX = -dimensions.width + 100;
            const maxX = window.innerWidth - 100;
            const minY = 0;
            const maxY = window.innerHeight - 50;
            setPosition({
                x: Math.max(minX, Math.min(maxX, ev.clientX - offX)),
                y: Math.max(minY, Math.min(maxY, ev.clientY - offY)),
            });
        };
        const onUp = () => {
            setIsDragging(false);
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
        };
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    };

    const centerConsole = () => setPosition({ x: null, y: 50 });
    const handleHeaderDoubleClick = () => centerConsole();

    const getCursorStyle = (direction) => {
        switch (direction) {
            case 'left':
            case 'right':
                return 'ew-resize';
            case 'top':
            case 'bottom':
                return 'ns-resize';
            case 'top-left':
            case 'bottom-right':
                return 'nw-resize';
            case 'top-right':
            case 'bottom-left':
                return 'ne-resize';
            default:
                return 'default';
        }
    };

    /* ------------------------------------------------------------------ */
    /* Export JSON                                                        */
    /* ------------------------------------------------------------------ */
    const exportConsole = () => {
        const blob = new Blob([JSON.stringify(messages, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `console_log_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    /* ------------------------------------------------------------------ */
    /* Markdown converter (showdown)                                      */
    /* ------------------------------------------------------------------ */
    useEffect(() => {
        let mounted = true;
        (async () => {
            const sd = await import('showdown');
            if (mounted)
                setShowdown(
                    new sd.Converter({
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
                        headerLevelStart: 1,
                    })
                );
        })();
        return () => {
            mounted = false;
        };
    }, []);

    /* ------------------------------------------------------------------ */
    /* Filtros                                                            */
    /* ------------------------------------------------------------------ */





    const handleRoleToggle = (role) => {
        setSelectedRoles((prev) => {
            const next = new Set(prev);
            if (role === 'all') {
                next.has('all') ? next.clear() : (next = new Set(['all']));
            } else {
                if (next.has('all')) next.delete('all');
                next.has(role) ? next.delete(role) : next.add(role);
            }
            return new Set(next);
        });
    };

    /* ------------------------------------------------------------------ */
    /* API público                                                        */
    /* ------------------------------------------------------------------ */
    return useMemo(
        () => ({
            isVisible,
            setIsVisible,
            messages,
            setMessages,
            selectedRoles,
            setSelectedRoles,
            showFilters,
            setShowFilters,
            dimensions,
            setDimensions,
            position,
            setPosition,
            isResizing,
            setIsResizing,
            isDragging,
            setIsDragging,
            resizeDirection,
            setResizeDirection,
            dragOffset,
            setDragOffset,
            showdown,
            setShowdown,
            isPiPMode,
            setIsPiPMode,
            messagesEndRef,
            consoleRef,
            socket,
            getStrings,
            currentLang,
            strings,
            lang,
            normalizeRole,
            getUniqueRoles,
            clearConsole,
            exportConsole,
            filteredMessages,
            uniqueRoles,
            formatTime,
            handleRoleToggle,
            handleMouseDown,
            handleHeaderMouseDown,
            centerConsole,
            handleHeaderDoubleClick,
            getCursorStyle,
        }), [
            isVisible,
            messages,
            selectedRoles,
            showFilters,
            dimensions,
            position,
            isResizing,
            isDragging,
            resizeDirection,
            dragOffset,
            showdown,
            isPiPMode,
            socket,
            getStrings,
            currentLang,
            strings,
            lang,
            filteredMessages,
            uniqueRoles,
        ]
    );
}
