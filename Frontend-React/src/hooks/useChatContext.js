import { useContext } from 'react';
import { ChatContext } from '../context/ChatContext';

export const useChatContext = () => {
  return useContext(ChatContext);
};
