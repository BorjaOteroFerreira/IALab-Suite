import React, { createContext, useContext } from 'react';
import { ChatContext } from './ChatContext';

const SocketContext = createContext();

export const useSocket = () => {
  const chatContext = useContext(ChatContext);
  return chatContext?.socket;
};

export const SocketProvider = ({ children }) => {
  return (
    <SocketContext.Provider value={{}}>
      {children}
    </SocketContext.Provider>
  );
};

export default SocketContext;
