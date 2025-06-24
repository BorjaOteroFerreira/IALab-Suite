import React, { useEffect } from 'react';
import { useChatContext } from '../../hooks/useChatContext';
import { Trash } from 'lucide-react';
import './ChatSidebar.css';

function ChatSidebar({ visible, onLoadChat, onDeleteChat, onClose }) {
  const { chatList, fetchChatList } = useChatContext();

  useEffect(() => {
    if (visible) {
      fetchChatList();
    }
  }, [visible, fetchChatList]);

  if (!visible) return null;

  return (
    <div className={`chat-sidebar ${visible ? 'visible' : ''}`}>
      <div className="sidebar-header">
        <h3>📁 Historial de Chat</h3>
        <button 
          className="close-btn"
          onClick={onClose}
          title="Cerrar"
        >
          ✕
        </button>
      </div>
      
      <div className="chat-list">
        {Array.isArray(chatList) && chatList.length > 0 ? (
          chatList.map((chatName, idx) => (
            <div key={idx} className="chat-item">
              <button
                onClick={() => onDeleteChat(chatName)}
                className="delete-chat-btn"
                title="Eliminar chat"
              >
                <Trash size={18} />
              </button>
              <button
                onClick={() => onLoadChat(chatName)}
                className="chat-name-btn"
                title={`Cargar: ${chatName}`}
              >
                {chatName}
              </button>
            </div>
          ))
        ) : (
          <div style={{ 
            textAlign: 'center', 
            color: 'var(--text-secondary)', 
            padding: '2rem',
            fontStyle: 'italic'
          }}>
            No hay conversaciones guardadas
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatSidebar;
