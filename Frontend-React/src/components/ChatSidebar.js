import React from 'react';
import { useChatContext } from '../hooks/useChatContext';
import './ChatSidebar.css';

const ChatSidebar = ({ visible }) => {
  const { chatList, loadChat, deleteChat, newChat } = useChatContext();

  return (
    <div className={`chat-sidebar ${!visible ? 'hidden' : ''}`}>
      <div className="header-chat-menu">
        <button onClick={newChat}>
          Nueva conversación 🧠
        </button>
      </div>
      <div className="conversations-list">
        {chatList && chatList.length > 0 ? (
          chatList.map((chat, index) => (
            <div className="load-history" key={index}>
              <button className="delete-btn" onClick={() => deleteChat(chat)}>
                ❌
              </button>
              <button className="load-btn" onClick={() => loadChat(chat)}>
                {chat}
              </button>
            </div>
          ))
        ) : (
          <p style={{ color: 'gray', textAlign: 'center', padding: '10px' }}>
            No hay conversaciones guardadas
          </p>
        )}
      </div>
    </div>
  );
};

export default ChatSidebar;
