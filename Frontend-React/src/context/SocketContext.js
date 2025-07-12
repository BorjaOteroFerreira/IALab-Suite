import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import io from 'socket.io-client';

export const SocketContext = createContext();

export const SocketProvider = ({ children }) => {
    const [socket, setSocket] = useState(null);
    const socketRef = useRef(null);

    useEffect(() => {
        // Usar el mismo puerto y namespace que ChatContext
        const newSocket = io.connect(`http://${window.location.hostname}:8081/test`, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: 5
        });
        setSocket(newSocket);
        socketRef.current = newSocket;
        return () => {
            newSocket.disconnect();
        };
    }, []);

    return (
        <SocketContext.Provider value={{ socket }}>
            {children}
        </SocketContext.Provider>
    );
};

export const useSocket = () => {
    const context = useContext(SocketContext);
    if (!context) throw new Error('useSocket debe usarse dentro de SocketProvider');
    return context.socket;
};
